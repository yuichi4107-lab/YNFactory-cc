# -*- coding: utf-8 -*-
"""掛け金配分の再検証（2026-07-11・現行レジーム版）

7/5検証との違い: 修復済みDB＋修復後データ学習モデル＋開幕週末(3/14-15)分離評価。
同一の買い目に対し flat / 配当均等(∝1/推定オッズ) / 穴厚め(∝推定オッズ) を精算比較。
レースごとの combos(key, est_odds, payout) をJSONダンプしローカルで頑健性分析する。

対象:
  C5b_morning : nb_no_odds_B + 本番C5b構成 @0.92（現在の本番=朝）
  FULL_prodOLD: 本番稼働中ライブモデル + 品質@0.86（現在の本番=ライブ）
  FULL_B      : nb_full_B（参考・修復後データ学習の候補系）
"""
import sys, os, json, time
sys.path.insert(0, "/opt/keiba-unified/jra/scripts")
os.chdir("/opt/keiba-unified/jra")
import sqlite3, model_v2, predictor_v1

DB = "/tmp/jra_v3.db"
BUDGET = 5000.0

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def build_one(d):
    import sqlite3, model_v2
    conn = sqlite3.connect(DB)
    try:
        return (d, model_v2.build_features_for_date(conn, d))
    finally:
        conn.close()

def main():
    from multiprocessing import Pool
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

    QS = {}
    def run(label, mpath, kind, base_t):
        QS.clear()
        import pickle
        d0 = pickle.load(open(mpath, "rb"))
        model_v2.MODEL_PATH = mpath
        model_v2.FEATURE_COLS = d0["feature_cols"]
        qbase = predictor_v1.evaluate_race_quality_no_odds if kind == "no_odds" else _ORIG_QUAL
        def qw(c, rid, scored, race_info=None):
            q = qbase(c, rid, scored, race_info)
            QS[rid] = q.get("quality_score", 0.0)
            return q
        predictor_v1.QUALITY_THRESHOLD = 0.0
        predictor_v1.evaluate_race_quality = qw
        gen = predictor_v1.generate_bets_c5b if kind == "no_odds" else _ORIG_GEN
        races = []
        for d in dates:
            if d not in cache: continue
            try: evs = predictor_v1.select_races(conn, d)
            except Exception as e:
                log(f"  fail {d}: {e}"); continue
            for ev in evs:
                rid = ev["race_id"]
                if QS.get(rid, 0.0) < base_t: continue
                if not settled(rid): continue
                bets = gen(ev["scored_horses"], ev.get("race_info") or {}, int(BUDGET))
                bt = bets.get("bet_type")
                if bt not in ("三連複", "馬連") or not bets.get("bets"): continue
                pm = payout_map(rid)
                combos = []
                for b in bets["bets"]:
                    try:
                        key = (bt, tuple(sorted(int(x) for x in b["combination"].replace(" ","").split("-"))))
                        eo = float(b.get("est_odds") or 0) or 10.0
                    except (ValueError, TypeError): continue
                    combos.append([list(key[1]), max(eo, 1.01), pm.get(key)])
                if combos:
                    races.append(dict(date=d, rid=rid, qs=QS.get(rid, 0.0), combos=combos))
        json.dump(races, open(f"/tmp/stake_v4_{label}.json", "w"))
        log(f"{label}: {len(races)} races dumped")
        return races

    run("C5b_morning", "/tmp/model_nb_no_odds_B.pkl", "no_odds", 0.92)
    run("FULL_prodOLD", "/opt/keiba-unified/jra/data/models/model_v2_live.pkl", "full", 0.86)
    run("FULL_B", "/tmp/model_nb_full_B.pkl", "full", 0.86)
    print("STAKE V4 DONE", flush=True)

if __name__ == "__main__":
    main()
