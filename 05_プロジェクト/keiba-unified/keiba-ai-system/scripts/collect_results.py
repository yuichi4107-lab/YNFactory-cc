"""開催日のレース結果を収集して既存データに追加するスクリプト

開催日の22時にcronで実行し、当日のレース結果を
data/raw/race_results.csv に追記する。

使い方:
    PYTHONPATH=. python3 scripts/collect_results.py
    PYTHONPATH=. python3 scripts/collect_results.py --date 2026-03-14
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime

import pandas as pd

from config.settings import RAW_DATA_DIR, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.scraper.banei_scraper import BaneiScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def collect_and_append(target_date: date) -> bool:
    """当日のレース結果を取得してCSVに追記する"""
    raw_file = RAW_DATA_DIR / "race_results.csv"

    # 既存データを読み込み、当日のデータが既にあるかチェック
    if raw_file.exists():
        existing = pd.read_csv(raw_file)
        date_str = target_date.strftime("%Y-%m-%d")
        if date_str in existing["race_date"].values:
            logger.info("%s のデータは既に登録済みです（%d件）",
                        date_str,
                        len(existing[existing["race_date"] == date_str]))
            return False
    else:
        existing = pd.DataFrame()

    # 当日のレース結果をスクレイピング
    logger.info("%s のレース結果を取得中...", target_date)
    scraper = BaneiScraper()
    df = scraper.scrape_date_range(target_date, target_date)

    if df.empty:
        logger.info("%s は開催がありません", target_date)
        return False

    # 既存データに追記
    if not existing.empty:
        combined = pd.concat([existing, df], ignore_index=True)
    else:
        combined = df

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_csv(raw_file, index=False, encoding="utf-8-sig")

    logger.info("結果追加完了: %s (%d件追加, 合計%d件)",
                target_date, len(df), len(combined))
    return True




def _send_telegram(text: str) -> bool:
    """Telegram にメッセージを送信する"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram設定が未設定です")
        return False
    import requests
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
        if resp.ok:
            logger.info("Telegram送信完了")
            return True
        else:
            logger.error("Telegram送信失敗: %s", resp.text[:200])
            return False
    except Exception as e:
        logger.error("Telegram送信エラー: %s", e)
        return False


def check_and_notify(target_date: date):
    """予想と結果を照合し、Telegram配信する"""
    from pathlib import Path
    pred_dir = Path("/opt/keiba-unified/keiba-ai-system/predictions")
    date_str = target_date.strftime("%Y-%m-%d")
    pred_file = pred_dir / f"{date_str}.csv"

    if not pred_file.exists():
        logger.info("予想ファイルなし: %s", pred_file)
        return

    raw_file = RAW_DATA_DIR / "race_results.csv"
    if not raw_file.exists():
        logger.info("結果ファイルなし")
        return

    pred_df = pd.read_csv(pred_file)
    result_df = pd.read_csv(raw_file)
    result_today = result_df[result_df["race_date"] == date_str]

    if result_today.empty:
        logger.info("当日結果なし: %s", date_str)
        return

    marks = ["◎", "○", "▲", "△"]
    lines = [f"🏇 ばんえい競馬 AI予想 結果速報", f"📅 {date_str}", "=" * 28, ""]

    total_races = 0
    hit_1st = hit_top3 = 0

    for race_no in sorted(pred_df["race_no"].unique()):
        race_pred = pred_df[pred_df["race_no"] == race_no].drop_duplicates(subset=["horse_number"]).sort_values("pred_rank")
        race_result = result_today[result_today["race_no"] == race_no].sort_values("finish_order")

        if race_result.empty:
            continue

        total_races += 1
        top3_nums = set(race_result.head(3)["horse_number"].values)
        winner_num = race_result.iloc[0]["horse_number"] if len(race_result) > 0 else -1

        race_lines = [f"【{int(race_no)}R】"]
        for i, (_, row) in enumerate(race_pred.iterrows()):
            if i >= 4:
                break
            mark = marks[i] if i < len(marks) else "  "
            hn = int(row["horse_number"])
            name = row["horse_name"]
            finish_row = race_result[race_result["horse_number"] == hn]
            if not finish_row.empty:
                fin_val = finish_row.iloc[0]["finish_order"]; fin = int(fin_val) if pd.notna(fin_val) else 99
                fin_str = f"{fin}着" if fin < 90 else "除外"
            else:
                fin = 99
                fin_str = "?"

            result_mark = ""
            if fin == 1:
                result_mark = " 🥇"
                if i == 0:
                    hit_1st += 1
            elif fin == 2:
                result_mark = " 🥈"
            elif fin == 3:
                result_mark = " 🥉"

            if i < 3 and fin <= 3:
                hit_top3 += 1

            race_lines.append(f"  {mark} {hn} {name} → {fin_str}{result_mark}")

        lines.extend(race_lines)
        lines.append("")

    lines.append("=" * 28)
    lines.append(f"集計: {total_races}レース")
    lines.append(f"◎1着的中: {hit_1st}/{total_races} ({hit_1st/total_races*100:.0f}%)" if total_races else "")
    lines.append(f"◎○▲ Top3入り: {hit_top3}回")
    lines.append("")

    msg = "\n".join(lines)
    logger.info("結果メッセージ:\n%s", msg)
    _send_telegram(msg)


def main():
    parser = argparse.ArgumentParser(description="帯広ばんえい競馬 レース結果収集")
    parser.add_argument("--date", help="収集日 (YYYY-MM-DD, デフォルト: 本日)")
    args = parser.parse_args()

    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today()

    collect_and_append(target_date)
    check_and_notify(target_date)


if __name__ == "__main__":
    main()
