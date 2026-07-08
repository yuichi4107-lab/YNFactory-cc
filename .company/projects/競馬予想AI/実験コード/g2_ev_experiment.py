# -*- coding: utf-8 -*-
"""G2 Step2: 較正確率×Harville近似によるEVレース選別 vs 品質閾値のOOS対決

- OOS: 2026-03-14..2026-07-05（両モデル未学習・修復済み実払戻・flat）
- ライブFULL系（オッズあり）:
    baseline  = 品質スコア(オッズ版) >= 0.86 で選別（現行方式・同一Bモデル）
    EV選別    = レースEV >= τ で選別（τスイープ）。EVは
                較正勝率(iso_win)→Harville近似で馬連/三連複の組合せ確率を出し
                本番買い目スレートの est_odds と掛けて算出
- C5b系（追加実験）: v2_probを較正値(iso_top3)に差し替えたC5bパイプライン
    （買い目のselfval妙味とレース選択が変わる）vs 無較正C5b
出力: /tmp/g2_oos_{label}.json ＋ 標準出力サマリー
"""
import sys, os, time, json, pickle, sqlite3, itertools
sys.path.insert(0, "/opt/keiba-unified/jra/scripts")
os.chdir("/opt/keiba-unified/jra")

DB = "/tmp/jra_v3.db"

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def build_one(d):
    import sqlite3, model_v2
    conn = sqlite3.connect(DB)
    try:
        return (d, model_v2.build_features_for_date(conn, d))
    finally:
        conn.close()

def harville_umaren(w, i, j):
    return w[i] * w[j] / max(1e-9, 1 - w[i]) + w[j] * w[i] / max(1e-9, 1 - w[j])

def harville_sanpuku(w, i, j, k):
    tot = 0.0
    for a, b, c in itertools.permutations((i, j, k)):
        tot += w[a] * (w[b] / max(1e-9, 1 - w[a])) * (w[c] / max(1e-9, 1 - w[a] - w[b]))
    return tot

def main():
    import model_v2, predictor_v1
    from multiprocessing import Pool

    cal_full = pickle.load(open("/tmp/g2_cal_full.pkl", "rb"))
    cal_no = pickle.load(open("/tmp/g2_cal_no_odds.pkl", "rb"))

    conn = sqlite3.connect(DB)
    dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM races WHERE date BETWEEN '2026-03-14' AND '2026-07-05' "
        "AND surface IN ('芝','ダート') ORDER BY date")]
    log(f"oos dates={len(dates)}")
    t = time.time()
    with Pool(3) as p:
        pairs = p.map(build_one, dates)
    cache = {d: df for d, df in pairs if df is not None and not df.empty}
    log(f"feature build {time.time()-t:.0f}s")
    model_v2.build_features_for_date = lambda c, d: cache.get(d)

    cur = conn.cursor()
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

    def settle(bt, bets, pm):
        inv = pay = 0
        for b in bets:
            try:
                key = (bt, tuple(sorted(int(x) for x in b["combination"].replace(" ", "").split("-"))))
                amt = int(b.get("amount", 0) or 0)
            except (ValueError, TypeError):
                continue
            inv += amt
            po = pm.get(key)
            if po:
                pay += po * amt // 100
        return inv, pay

    QS = {}
    def qwrap(base):
        def f(c, rid, scored, race_info=None):
            q = base(c, rid, scored, race_info)
            QS[rid] = q.get("quality_score", 0.0)
            return q
        return f

    # ===== A) ライブFULL: EV選別 vs 品質閾値（同一Bモデル・同一スレート） =====
    QS.clear()
    model_v2.MODEL_PATH = "/tmp/model_nb_full_B.pkl"
    model_v2.FEATURE_COLS = model_v2.FEATURE_COLS_FULL
    predictor_v1.QUALITY_THRESHOLD = 0.0
    predictor_v1.evaluate_race_quality = qwrap(_ORIG_QUAL)
    rows = []
    for d in dates:
        if d not in cache: continue
        try: evs = predictor_v1.select_races(conn, d)
        except Exception as e:
            log(f"select fail {d}: {e}"); continue
        for ev in evs:
            rid = ev["race_id"]
            if not settled(rid): continue
            horses = ev["scored_horses"]
            bets = _ORIG_GEN(horses, ev.get("race_info") or {}, 5000)
            bt = bets.get("bet_type")
            if bt not in ("三連複", "馬連") or not bets.get("bets"): continue
            # 較正勝率 → Harville
            raw = {h["horse_number"]: float(h.get("v2_prob") or 0.0) for h in horses}
            wv = {n: max(1e-4, float(cal_full["iso_win"].predict([p])[0])) for n, p in raw.items()}
            s = sum(wv.values())
            w = {n: v / s for n, v in wv.items()}
            ev_num = ev_den = 0.0
            for b in bets["bets"]:
                try:
                    nums = [int(x) for x in b["combination"].replace(" ", "").split("-")]
                    amt = float(b.get("amount", 0) or 0)
                    eo = float(b.get("est_odds") or 0) or 10.0
                except (ValueError, TypeError):
                    continue
                if any(n not in w for n in nums): continue
                pc = harville_umaren(w, nums[0], nums[1]) if bt == "馬連" else harville_sanpuku(w, *nums[:3])
                ev_num += pc * eo * amt
                ev_den += amt
            if ev_den <= 0: continue
            race_ev = ev_num / ev_den
            pm = payout_map(rid)
            inv, pay = settle(bt, bets["bets"], pm)
            if inv <= 0: continue
            rows.append(dict(date=d, rid=rid, qs=QS.get(rid, 0.0), ev=race_ev,
                             inv=inv, pay=pay, hit=1 if pay > 0 else 0))
    json.dump(rows, open("/tmp/g2_oos_full_ev.json", "w"))
    print(f"\n===== A) FULL_B: races={len(rows)} =====", flush=True)
    def line(label, sel):
        if not sel:
            print(f"  {label}: n=0"); return
        inv = sum(r["inv"] for r in sel); pay = sum(r["pay"] for r in sel); h = sum(r["hit"] for r in sel)
        pays = sorted((r["pay"] for r in sel), reverse=True)
        d3 = 100*(pay-sum(pays[:3]))/inv if len(pays) >= 3 else 0
        print(f"  {label}: n={len(sel):4d} hit={h:3d}({100*h/len(sel):4.1f}%) ROI={100*pay/inv:6.1f}% "
              f"P/L={pay-inv:+9d} drop-top3={d3:5.1f}%", flush=True)
    line("baseline q>=0.86 ", [r for r in rows if r["qs"] >= 0.86])
    line("baseline q>=0.90 ", [r for r in rows if r["qs"] >= 0.90])
    for tau in (0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4):
        line(f"EV>={tau:.1f}         ", [r for r in rows if r["ev"] >= tau])
    line("EV>=1.0 & q>=0.80", [r for r in rows if r["ev"] >= 1.0 and r["qs"] >= 0.80])

    # ===== B) C5b: 較正確率注入 vs 無較正 =====
    def run_c5b(label, calibrate):
        QS.clear()
        model_v2.MODEL_PATH = "/tmp/model_nb_no_odds_B.pkl"
        model_v2.FEATURE_COLS = model_v2.FEATURE_COLS_NO_ODDS
        predictor_v1.QUALITY_THRESHOLD = 0.0
        predictor_v1.evaluate_race_quality = qwrap(predictor_v1.evaluate_race_quality_no_odds)
        out = []
        for d in dates:
            if d not in cache: continue
            try: evs = predictor_v1.select_races(conn, d)
            except Exception: continue
            for ev in evs:
                rid = ev["race_id"]
                if not settled(rid): continue
                horses = ev["scored_horses"]
                if calibrate:
                    horses = [dict(h) for h in horses]
                    for h in horses:
                        h["v2_prob"] = float(cal_no["iso_top3"].predict([float(h.get("v2_prob") or 0.0)])[0])
                bets = predictor_v1.generate_bets_c5b(horses, ev.get("race_info") or {}, 5000)
                bt = bets.get("bet_type")
                if bt not in ("三連複", "馬連") or not bets.get("bets"): continue
                pm = payout_map(rid)
                inv, pay = settle(bt, bets["bets"], pm)
                if inv <= 0: continue
                out.append(dict(date=d, rid=rid, qs=QS.get(rid, 0.0),
                                inv=inv, pay=pay, hit=1 if pay > 0 else 0))
        json.dump(out, open(f"/tmp/g2_oos_{label}.json", "w"))
        print(f"\n===== B) {label}: races={len(out)} =====", flush=True)
        for t_ in (0.0, 0.90, 0.92, 0.94):
            line(f"q>={t_:.2f}          ", [r for r in out if r["qs"] >= t_])
        return out

    run_c5b("c5b_raw", calibrate=False)
    run_c5b("c5b_cal", calibrate=True)
    print("G2 EV EXPERIMENT DONE", flush=True)


if __name__ == "__main__":
    main()
