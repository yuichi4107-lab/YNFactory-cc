# -*- coding: utf-8 -*-
# C3 shadow track (forward-test, live予想と並走): NO_ODDSモデル + value買い目 + オッズ品質0.86 + flat。
# source="live_c3" で保存。Telegram/X通知は一切なし（記録のみ）。cron 9:35想定（オッズ発表後）。
# 結果集計は check_results.py が source別に独立表示する。
import sys, os
from datetime import date as _date
sys.path.insert(0, os.path.dirname(__file__))
import model_v2
import predictor_v1
from predictor_v1 import get_conn, generate_bets, select_races
from run_today import scrape_odds, save_predictions
from scraper_legacy import init_db

RACE_BUDGET = 5000
THRESHOLD = 0.86  # ライブと同じオッズ品質閾値で比較
NO_ODDS_MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                  "data", "models", "model_v2_no_odds.pkl")


def main():
    date_args = [a for a in sys.argv[1:] if len(a) >= 4 and a[:4].isdigit()]
    target = date_args[0] if date_args else _date.today().strftime("%Y-%m-%d")
    print(f"=== C3 shadow (source=live_c3): {target} ===")

    conn = get_conn()
    init_db()
    c = conn.cursor()

    # NO_ODDSモデル + オッズ品質（select_races内のevaluate_race_quality=オッズ版を使用）
    model_v2.MODEL_PATH = NO_ODDS_MODEL_PATH
    model_v2.FEATURE_COLS = model_v2.FEATURE_COLS_NO_ODDS
    predictor_v1.QUALITY_THRESHOLD = 0.0  # 全レース取得→後段で0.86で分離

    # オッズ取得（value_score/品質に必要。liveが取得済みでも冪等）
    c.execute("""SELECT race_id FROM races WHERE date=? AND surface IN ('芝','ダート')
                 AND name NOT LIKE '%障害%' ORDER BY start_time""", (target,))
    rids = [r[0] for r in c.fetchall()]
    okc = sum(1 for rid in rids if scrape_odds(rid, conn, retries=2, verbose=False))
    print(f"オッズ: {okc}/{len(rids)}レース")

    all_races = select_races(conn, target)
    buy = [r for r in all_races if r["quality"]["quality_score"] >= THRESHOLD]
    skip = [r for r in all_races if r["quality"]["quality_score"] < THRESHOLD]
    print(f"C3選定: 買い{len(buy)} / 見送り{len(skip)}")

    if buy:
        pred = {"date": target, "races": [
            {"race_id": r["race_id"], "quality": r["quality"],
             "bets": generate_bets(r["scored_horses"], {"race_id": r["race_id"]}, RACE_BUDGET)}
            for r in buy]}
        save_predictions(pred, conn, source="live_c3")
    if skip:
        skipd = {"date": target, "races": [
            {"race_id": r["race_id"], "quality": r["quality"],
             "bets": {"bet_type": "見送り", "bets": [{"combination": "-", "amount": 0}]}}
            for r in skip]}
        save_predictions(skipd, conn, source="live_c3")

    conn.close()
    print("DONE (Telegram/X通知なし・記録のみ)")


if __name__ == "__main__":
    main()
