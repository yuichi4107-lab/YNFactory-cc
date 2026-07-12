# -*- coding: utf-8 -*-
"""JRA-VANデータ特徴量（調教・血統）の新モデル実験（工程F2相当）

1. JV特徴量込みの行列を全期間(2022-01-01..2026-07-12)一括ビルド（1回だけ）
2. 変種を学習（窓<=2025-12-31、列選択で単一ビルドから派生）:
     nb(76/80列)=既存ベースライン(再利用・学習なし) / +調教(84/88) / +調教+血統(88/92)
3. OOS 2026-03-14..07-12（確定分のみ・実払戻・本番実装の買い目）で対決
   出力: /tmp/jv_oos_{label}.json（date/qs/inv/pay/hit）→ローカルで標準プロトコル分析
"""
import sys, os, time, json, pickle, sqlite3
sys.path.insert(0, "/tmp")
sys.path.insert(0, "/opt/keiba-unified/jra/scripts")
os.chdir("/opt/keiba-unified/jra")

DB = "/tmp/jra_v5.db"
FEATS = "/tmp/jv_feats.pkl"

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def build_one(d):
    import sqlite3
    import model_v2_jv as J
    conn = sqlite3.connect(DB)
    try:
        df = J.build_features_for_date(conn, d)
        if df is not None and not df.empty:
            df = df.copy(); df["date"] = d
        return (d, df)
    finally:
        conn.close()

def main():
    import pandas as pd
    import model_v2
    import model_v2_jv as J
    import predictor_v1
    from multiprocessing import Pool

    log(f"blood table available: {J.has_blood()}")
    conn = sqlite3.connect(DB)
    dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM races WHERE date BETWEEN '2022-01-01' AND '2026-07-12' "
        "AND surface IN ('芝','ダート') ORDER BY date")]
    oos_dates = [d for d in dates if d >= "2026-03-14"]
    log(f"dates={len(dates)} oos={len(oos_dates)}")

    t = time.time()
    if os.path.exists(FEATS):
        per_date = pickle.load(open(FEATS, "rb"))
        log(f"feature cache loaded: {len(per_date)}")
    else:
        with Pool(3) as p:
            pairs = p.map(build_one, dates)
        per_date = {d: df for d, df in pairs if df is not None and not df.empty}
        pickle.dump(per_date, open(FEATS, "wb"))
        log(f"feature build {time.time()-t:.0f}s")
    df_all = pd.concat(list(per_date.values()), ignore_index=True)
    log(f"rows={len(df_all)} cols={len(df_all.columns)}")
    for c in J.TRAIN_COLS + (J.BLOOD_COLS if J.has_blood() else []):
        log(f"  {c}: mean={df_all[c].mean():.4f} std={df_all[c].std():.4f}")

    variants = [
        ("jv_tr_no_odds", J.FEATURE_COLS_NO_ODDS, "/tmp/model_jvtr_no_odds_B.pkl"),
        ("jv_tr_full", J.FEATURE_COLS_FULL, "/tmp/model_jvtr_full_B.pkl"),
    ]
    if J.has_blood():
        variants += [
            ("jv_trbl_no_odds", J.FEATURE_COLS_NO_ODDS_B, "/tmp/model_jvtrbl_no_odds_B.pkl"),
            ("jv_trbl_full", J.FEATURE_COLS_FULL_B, "/tmp/model_jvtrbl_full_B.pkl"),
        ]
    sub = df_all[df_all["date"] <= "2025-12-31"]
    for name, cols, path in variants:
        if os.path.exists(path):
            log(f"skip train {name}"); continue
        log(f"train {name}: rows={len(sub)} feats={len(cols)}")
        model_v2.FEATURE_COLS = cols
        model_v2.MODEL_PATH = path
        model_v2.build_training_data = lambda c, s, e, _s=sub: _s
        c2 = sqlite3.connect(DB)
        model_v2.train_model(c2, "2022-01-01", "2025-12-31")
        c2.close()

    # ===== OOS eval =====
    model_v2.build_features_for_date = lambda c, d: per_date.get(d)
    cur = conn.cursor()
    _OG, _OQ = predictor_v1.generate_bets, predictor_v1.evaluate_race_quality

    def payout_map(rid):
        m = {}
        for bt, comb, po in cur.execute("SELECT bet_type,combination,payout FROM payouts WHERE race_id=?", (rid,)):
            try: m[(bt, tuple(sorted(int(x) for x in comb.replace('→',' ').replace('-',' ').split())))] = po
            except ValueError: pass
        return m

    def settled(rid):
        return cur.execute("SELECT COUNT(*) FROM results WHERE race_id=? AND finish_position>0",
                           (rid,)).fetchone()[0] >= 3

    QS = {}
    def run(label, mpath, kind):
        QS.clear()
        d0 = pickle.load(open(mpath, "rb"))
        model_v2.MODEL_PATH = mpath
        model_v2.FEATURE_COLS = d0["feature_cols"]
        qbase = predictor_v1.evaluate_race_quality_no_odds if kind == "no_odds" else _OQ
        def qw(c, rid, scored, race_info=None):
            q = qbase(c, rid, scored, race_info)
            QS[rid] = q.get("quality_score", 0.0)
            return q
        predictor_v1.QUALITY_THRESHOLD = 0.0
        predictor_v1.evaluate_race_quality = qw
        gen = predictor_v1.generate_bets_c5b if kind == "no_odds" else _OG
        rows = []
        for d in oos_dates:
            if d not in per_date: continue
            try: evs = predictor_v1.select_races(conn, d)
            except Exception as e:
                log(f"  fail {d}: {e}"); continue
            for ev in evs:
                rid = ev["race_id"]
                if not settled(rid): continue
                bets = gen(ev["scored_horses"], ev.get("race_info") or {}, 5000)
                bt = bets.get("bet_type")
                if bt not in ("三連複", "馬連") or not bets.get("bets"): continue
                pm = payout_map(rid)
                inv = pay = 0
                for b in bets["bets"]:
                    try:
                        key = (bt, tuple(sorted(int(x) for x in b["combination"].replace(" ","").split("-"))))
                        amt = int(b.get("amount", 0) or 0)
                    except (ValueError, TypeError): continue
                    inv += amt
                    po = pm.get(key)
                    if po: pay += po*amt//100
                if inv <= 0: continue
                rows.append(dict(date=d, qs=QS.get(rid, 0.0), inv=inv, pay=pay, hit=1 if pay>0 else 0))
        json.dump(rows, open(f"/tmp/jv_oos_{label}.json", "w"))
        sel = [r for r in rows if r["qs"] >= (0.92 if kind == "no_odds" else 0.86)]
        inv = sum(r["inv"] for r in sel) or 1
        log(f"{label}: races={len(rows)} @base n={len(sel)} ROI={100*sum(r['pay'] for r in sel)/inv:.1f}%")
        return rows

    run("c5b_base", "/tmp/model_nb_no_odds_B.pkl", "no_odds")
    run("c5b_jvtr", "/tmp/model_jvtr_no_odds_B.pkl", "no_odds")
    if J.has_blood():
        run("c5b_jvtrbl", "/tmp/model_jvtrbl_no_odds_B.pkl", "no_odds")
    run("full_base", "/tmp/model_nb_full_B.pkl", "full")
    run("full_jvtr", "/tmp/model_jvtr_full_B.pkl", "full")
    if J.has_blood():
        run("full_jvtrbl", "/tmp/model_jvtrbl_full_B.pkl", "full")
    print("JV EXPERIMENT DONE", flush=True)

if __name__ == "__main__":
    main()
