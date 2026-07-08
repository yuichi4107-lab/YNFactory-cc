# -*- coding: utf-8 -*-
"""馬場バイアス特徴量の実験ドライバ（工程F2）

1. bias付き特徴量を全期間(2022-01-01..2026-07-05)並列ビルド（1回だけ）
2. bias版モデルを学習: NO_ODDS/FULL × 学習窓<=2025-12-31（単一変数比較用B）
3. OOS 2026-03-14..2026-07-05 で5構成を対決（実払戻・本番実装の買い目生成）:
     C5b: 無bias-B(7/5作成済) vs bias-B ／ FULL: 本番OLD vs 無bias-B vs bias-B
   ※無biasモデルのスコアリングもbias付きdf(上位集合)で可能（pklに列名が埋め込み済み）
判定基準（要件定義F2）: 朝C5b@0.92で ROI+2pt以上 または 的中率+1pt以上（他方が劣化しない）
"""
import sys, os, time, pickle, sqlite3, json
sys.path.insert(0, "/opt/keiba-unified/jra/scripts")
sys.path.insert(0, "/tmp")
os.chdir("/opt/keiba-unified/jra")

DB = "/tmp/jra_v3.db"
FEATS = "/tmp/bias_feats.pkl"

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def build_one(d):
    import sqlite3
    import model_v2_bias as B
    conn = sqlite3.connect(DB)
    try:
        df = B.build_features_for_date(conn, d)
        if df is not None and not df.empty:
            df = df.copy(); df["date"] = d
        return (d, df)
    finally:
        conn.close()

def main():
    import pandas as pd
    import model_v2
    import model_v2_bias as B
    import predictor_v1
    from multiprocessing import Pool

    conn = sqlite3.connect(DB)
    dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM races WHERE date BETWEEN '2022-01-01' AND '2026-07-05' "
        "AND surface IN ('芝','ダート') ORDER BY date")]
    oos_dates = [d for d in dates if d >= "2026-03-14"]
    conn.close()
    log(f"dates={len(dates)} oos={len(oos_dates)}")

    t = time.time()
    if os.path.exists(FEATS):
        per_date = pickle.load(open(FEATS, "rb"))
        log(f"feature cache loaded: {len(per_date)} dates")
    else:
        with Pool(3) as p:
            pairs = p.map(build_one, dates)
        per_date = {d: df for d, df in pairs if df is not None and not df.empty}
        pickle.dump(per_date, open(FEATS, "wb"))
        log(f"feature build {time.time()-t:.0f}s dates={len(per_date)}")
    df_all = pd.concat(list(per_date.values()), ignore_index=True)
    log(f"total rows={len(df_all)} cols={len(df_all.columns)}")
    for c in B.BIAS_COLS:
        nz = (df_all[c] != 0).mean()
        log(f"  {c}: nonzero={100*nz:.1f}% mean={df_all[c].mean():.4f} std={df_all[c].std():.4f}")

    # --- train 4 models (<=2025-12-31): 修復後データで無bias/bias両方を学習し
    #     「データ修復効果」と「バイアス特徴量効果」を分離した単一変数比較にする ---
    for cols, path in [(model_v2.FEATURE_COLS_NO_ODDS, "/tmp/model_nb_no_odds_B.pkl"),
                       (model_v2.FEATURE_COLS_FULL, "/tmp/model_nb_full_B.pkl"),
                       (B.FEATURE_COLS_NO_ODDS, "/tmp/model_bias_no_odds_B.pkl"),
                       (B.FEATURE_COLS_FULL, "/tmp/model_bias_full_B.pkl")]:
        if os.path.exists(path):
            log(f"skip train (exists): {path}"); continue
        sub = df_all[df_all["date"] <= "2025-12-31"]
        log(f"train {path}: rows={len(sub)} feats={len(cols)}")
        model_v2.FEATURE_COLS = cols
        model_v2.MODEL_PATH = path
        model_v2.build_training_data = lambda c, s, e, _sub=sub: _sub
        c2 = sqlite3.connect(DB)
        model_v2.train_model(c2, "2022-01-01", "2025-12-31")
        c2.close()

    # --- OOS eval ---
    model_v2.build_features_for_date = lambda c, d: per_date.get(d)
    conn = sqlite3.connect(DB); cur = conn.cursor()
    _ORIG_GEN = predictor_v1.generate_bets
    _ORIG_QUAL = predictor_v1.evaluate_race_quality

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
        model_v2.MODEL_PATH = mpath
        # FEATURE_COLSはpkl埋め込みのfeature_colsが優先されるが、明示同期しておく
        d0 = pickle.load(open(mpath, "rb"))
        model_v2.FEATURE_COLS = d0["feature_cols"]
        qbase = predictor_v1.evaluate_race_quality_no_odds if kind == "no_odds" else _ORIG_QUAL
        def qw(c, rid, scored, race_info=None):
            q = qbase(c, rid, scored, race_info)
            QS[rid] = q.get("quality_score", 0.0)
            return q
        predictor_v1.QUALITY_THRESHOLD = 0.0
        predictor_v1.evaluate_race_quality = qw
        gen = predictor_v1.generate_bets_c5b if kind == "no_odds" else _ORIG_GEN
        rows = []
        for d in oos_dates:
            if d not in per_date: continue
            try: evs = predictor_v1.select_races(conn, d)
            except Exception as e:
                log(f"  select fail {d}: {e}"); continue
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
        print(f"\n===== {label} ===== races={len(rows)}", flush=True)
        for t_ in (0.0, 0.86, 0.90, 0.92, 0.94, 0.96):
            sel = [r for r in rows if r["qs"] >= t_]
            if not sel: continue
            inv = sum(r["inv"] for r in sel); pay = sum(r["pay"] for r in sel); h = sum(r["hit"] for r in sel)
            print(f"  q>={t_:.2f}: n={len(sel):3d} hit={h:3d}({100*h/len(sel):4.1f}%) ROI={100*pay/inv:6.1f}% P/L={pay-inv:+d}", flush=True)
        json.dump(rows, open(f"/tmp/bias_oos_{label}.json", "w"))
        return rows

    run("C5b_oldData_B", "/tmp/model_v2_no_odds_B.pkl", "no_odds")      # 参考: 修復前データ学習(7/5)
    run("C5b_noBias_B", "/tmp/model_nb_no_odds_B.pkl", "no_odds")       # ベースライン: 修復後データ・無bias
    run("C5b_bias_B", "/tmp/model_bias_no_odds_B.pkl", "no_odds")       # 本命: 修復後データ・bias付き
    run("FULL_prodOLD", "/opt/keiba-unified/jra/data/models/model_v2_live.pkl", "full")
    run("FULL_noBias_B", "/tmp/model_nb_full_B.pkl", "full")
    run("FULL_bias_B", "/tmp/model_bias_full_B.pkl", "full")
    print("BIAS EXPERIMENT DONE", flush=True)

if __name__ == "__main__":
    main()
