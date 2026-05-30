#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
競馬予想 結果チェックスクリプト
レース結果をスクレイピングし、予測との照合・収支記録・Telegram通知を行う

Usage:
  python3 check_results.py              # 今日の結果をチェック
  python3 check_results.py 2026-03-14   # 指定日の結果をチェック
  python3 check_results.py --monthly    # 月間サマリーを送信
"""

import sys
import os
import io
import re
import time
import requests
from datetime import datetime, date, timedelta

# Windows cp932でUnicode絵文字を出力できるようにする
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(__file__))
from predictor_v1 import get_conn
from scraper_legacy import HEADERS, REQUEST_INTERVAL, scrape_race, init_db
from run_today import _build_jra_result_cname_map, scrape_result_jra
from backtest_legacy import check_hit

# Telegram設定（環境変数優先・2026-05-30 ハードコード除去）
TG_TOKEN = os.environ.get("TG_TOKEN_JRA", os.environ.get("TG_TOKEN", ""))
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "8571447808")


def send_telegram(message):
    """Telegramにメッセージ送信"""
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT_ID, "parse_mode": "Markdown", "text": message},
            timeout=10)
    except requests.RequestException:
        pass


def scrape_day_results(conn, date_str):
    """指定日の全レース結果をスクレイピング（JRA公式 → netkeiba フォールバック）"""
    c = conn.cursor()
    c.execute("""SELECT race_id FROM races WHERE date = ?
                 AND surface IN ('芝', 'ダート') AND name NOT LIKE '%障害%'""", (date_str,))
    race_ids = [row[0] for row in c.fetchall()]

    if not race_ids:
        print(f"レースデータなし: {date_str}")
        return 0

    # JRA公式の結果CNAME マップを構築
    from datetime import datetime as _dt
    target_date = _dt.strptime(date_str, "%Y-%m-%d").date()
    print("  JRA公式結果CNAMEマップ構築中...")
    result_cname_map = _build_jra_result_cname_map(target_date)
    print(f"  {len(result_cname_map)}レース分の結果CNAMEを取得")

    scraped = 0
    for race_id in race_ids:
        # 既に結果がある場合はスキップ
        c.execute("""SELECT COUNT(*) FROM results
                     WHERE race_id = ? AND finish_position > 0""", (race_id,))
        if c.fetchone()[0] > 0:
            scraped += 1
            continue

        print(f"  結果取得: {race_id}", end="")

        # JRA公式から取得を試みる
        cname = result_cname_map.get(race_id)
        if cname:
            if scrape_result_jra(race_id, conn, cname):
                scraped += 1
                print(" OK (JRA)")
                time.sleep(0.5)
                continue

        # JRA失敗時はnetkeibaにフォールバック
        if scrape_race(race_id, conn):
            scraped += 1
            print(" OK (netkeiba)")
        else:
            print(" -")
        time.sleep(REQUEST_INTERVAL)

    return scraped


def _check_source_results(conn, date_str, source):
    """指定ソース(morning/live)の予測と結果を照合して収支を計算"""
    c = conn.cursor()

    # sourceカラムの有無を確認
    has_source = False
    try:
        c.execute("SELECT source FROM predictions LIMIT 1")
        has_source = True
    except Exception:
        pass

    # 予測データを取得（見送りも含む）
    if has_source:
        c.execute("""SELECT DISTINCT race_id, bet_type, quality_score
                     FROM predictions WHERE date = ? AND source = ?""", (date_str, source))
    else:
        c.execute("""SELECT DISTINCT race_id, bet_type, quality_score
                     FROM predictions WHERE date = ?""", (date_str,))

    predicted_races = {}
    for race_id, bet_type, q_score in c.fetchall():
        # 同一レースに推奨と見送りがある場合、推奨を優先
        if race_id in predicted_races and predicted_races[race_id]["bet_type"] != "見送り":
            continue
        predicted_races[race_id] = {"bet_type": bet_type, "quality_score": q_score}

    if not predicted_races:
        return None

    # 推奨レースと見送りレースを分離
    recommended = {k: v for k, v in predicted_races.items() if v["bet_type"] != "見送り"}
    skipped = {k: v for k, v in predicted_races.items() if v["bet_type"] == "見送り"}

    # 結果が出ているか確認
    race_ids = list(predicted_races.keys())
    placeholders = ",".join("?" * len(race_ids))
    c.execute(f"""SELECT DISTINCT race_id FROM results
                  WHERE race_id IN ({placeholders}) AND finish_position > 0""", race_ids)
    finished_ids = set(row[0] for row in c.fetchall())

    results = []
    skipped_results = []
    total_bet = 0
    total_payout = 0
    hits = 0

    for race_id, info in recommended.items():
        if race_id not in finished_ids:
            continue

        # 買い目を取得（amount > 0 のみ）
        if has_source:
            c.execute("""SELECT combination, amount FROM predictions
                         WHERE date = ? AND race_id = ? AND source = ? AND amount > 0""",
                      (date_str, race_id, source))
        else:
            c.execute("""SELECT combination, amount FROM predictions
                         WHERE date = ? AND race_id = ? AND amount > 0""",
                      (date_str, race_id))
        bets = [{"combination": row[0], "amount": row[1]} for row in c.fetchall()]
        if not bets:
            continue

        bet_total = sum(b["amount"] for b in bets)
        hit_result = check_hit(conn, race_id, info["bet_type"], bets)

        # レース情報
        c.execute("SELECT venue, race_number, name FROM races WHERE race_id = ?", (race_id,))
        race_row = c.fetchone()
        venue = race_row[0] if race_row else ""
        race_number = race_row[1] if race_row else 0
        race_name = race_row[2] if race_row else ""

        payout = hit_result["total_payout"]
        profit = payout - bet_total
        hit = 1 if hit_result["hit"] else 0
        if hit:
            hits += 1

        total_bet += bet_total
        total_payout += payout

        # prediction_results に保存
        c.execute("""INSERT OR REPLACE INTO prediction_results
                     VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                  (date_str, race_id, venue, race_number, race_name,
                   info["bet_type"], bet_total, hit, payout, profit,
                   info["quality_score"]))

        results.append({
            "race_id": race_id,
            "venue": venue,
            "race_number": race_number,
            "race_name": race_name,
            "bet_type": info["bet_type"],
            "bet_total": bet_total,
            "hit": hit,
            "payout": payout,
            "profit": profit,
            "hit_details": hit_result["hit_details"],
        })

    # 見送りレースの結果も記録
    for race_id, info in skipped.items():
        if race_id not in finished_ids:
            continue
        c.execute("SELECT venue, race_number, name FROM races WHERE race_id = ?", (race_id,))
        race_row = c.fetchone()
        if race_row:
            skipped_results.append({
                "race_id": race_id,
                "venue": race_row[0],
                "race_number": race_row[1],
                "quality_score": info["quality_score"],
            })

    roi = total_payout / total_bet if total_bet > 0 else 0

    return {
        "date": date_str,
        "source": source,
        "results": results,
        "skipped": skipped_results,
        "total_analyzed": len(predicted_races),
        "total_recommended": len(recommended),
        "total_skipped": len(skipped),
        "total_bet": total_bet,
        "total_payout": total_payout,
        "profit": total_payout - total_bet,
        "roi": roi,
        "hits": hits,
        "races": len(results),
    }


def check_day_results(conn, date_str):
    """予測と結果を照合して収支を計算（morning/live別 + 合計）"""
    morning = _check_source_results(conn, date_str, "morning")
    live = _check_source_results(conn, date_str, "live")

    if not morning and not live:
        print(f"予測データなし: {date_str}")
        return None

    # 合計をdaily_summaryに保存
    all_results = []
    total_bet = 0
    total_payout = 0
    hits = 0
    for src in [morning, live]:
        if src:
            all_results.extend(src["results"])
            total_bet += src["total_bet"]
            total_payout += src["total_payout"]
            hits += src["hits"]

    roi = total_payout / total_bet if total_bet > 0 else 0
    hit_rate = hits / len(all_results) if all_results else 0

    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO daily_summary VALUES (?,?,?,?,?,?,?,?)""",
              (date_str, len(all_results), hits, total_bet, total_payout,
               total_payout - total_bet, roi, hit_rate))
    conn.commit()

    return {
        "date": date_str,
        "morning": morning,
        "live": live,
        "total_bet": total_bet,
        "total_payout": total_payout,
        "profit": total_payout - total_bet,
        "roi": roi,
        "hits": hits,
        "races": len(all_results),
    }


def _format_source_section(src, label):
    """1ソース分のレポートセクションを生成"""
    if not src:
        return [f"*{label}*: 該当なし"]

    lines = [f"*{label}*"]
    lines.append(f"分析: {src['total_analyzed']}レース → 推奨: {src['total_recommended']} / 見送り: {src['total_skipped']}")

    if not src["results"]:
        lines.append("推奨レースなし")
        return lines

    roi_pct = src["roi"] * 100
    profit = src["profit"]
    sign = "+" if profit >= 0 else ""

    lines.append(f"推奨{src['races']}レース中 {src['hits']}的中")
    lines.append(f"投資: {src['total_bet']:,}円 → 回収: {src['total_payout']:,}円")
    lines.append(f"収支: {sign}{profit:,}円 (ROI: {roi_pct:.1f}%)")

    hit_races = [r for r in src["results"] if r["hit"]]
    miss_races = [r for r in src["results"] if not r["hit"]]

    if hit_races:
        for r in hit_races:
            details = ", ".join(f'{h["combination"]}→{h["payout"]:,}円' for h in r["hit_details"])
            lines.append(f"  ✅ {r['venue']}{r['race_number']}R {r['bet_type']} {details}")

    if miss_races:
        miss_str = ", ".join(f"{r['venue']}{r['race_number']}R" for r in miss_races)
        lines.append(f"  ❌ {miss_str}")

    return lines


def format_result_message(day):
    """Telegram用の結果メッセージを生成（朝予想・ライブ別レポート）"""
    d = day["date"]
    roi_pct = day["roi"] * 100
    profit = day["profit"]
    sign = "+" if profit >= 0 else ""

    lines = [f"📊 *競馬結果速報 {d}*", ""]

    # 朝予想の結果
    lines.extend(_format_source_section(day.get("morning"), "🌅 朝予想"))
    lines.append("")

    # ライブモードの結果
    lines.extend(_format_source_section(day.get("live"), "🔴 ライブ"))
    lines.append("")

    # 合計
    lines.append("*📋 合計*")
    lines.append(f"{day['races']}レース中 {day['hits']}的中")
    lines.append(f"投資: {day['total_bet']:,}円 → 回収: {day['total_payout']:,}円")
    lines.append(f"収支: {sign}{profit:,}円 (ROI: {roi_pct:.1f}%)")

    return "\n".join(lines)


def monthly_summary(conn, year=None, month=None):
    """月間サマリーを生成して送信"""
    if year is None or month is None:
        today = date.today()
        # 前月の集計（月初に実行される想定）
        first_of_month = today.replace(day=1)
        last_month = first_of_month - timedelta(days=1)
        year = last_month.year
        month = last_month.month

    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year + 1}-01-01"
    else:
        end = f"{year}-{month + 1:02d}-01"

    c = conn.cursor()
    c.execute("""SELECT COUNT(*), SUM(races_bet), SUM(races_hit),
                        SUM(total_bet), SUM(total_payout), SUM(profit)
                 FROM daily_summary WHERE date >= ? AND date < ?""", (start, end))
    row = c.fetchone()
    days, races, hit_total, bet_total, payout_total, profit_total = row

    if not days or not races:
        print(f"{year}年{month}月: データなし")
        return

    roi = payout_total / bet_total if bet_total > 0 else 0
    hit_rate = hit_total / races if races > 0 else 0
    sign = "+" if profit_total >= 0 else ""

    lines = [f"📈 *月間成績 {year}年{month}月*", ""]
    lines.append(f"開催日数: {days}日 / 対象レース: {races}レース")
    lines.append(f"的中: {hit_total}レース ({hit_rate * 100:.1f}%)")
    lines.append(f"投資: {bet_total:,}円 → 回収: {payout_total:,}円")
    lines.append(f"収支: {sign}{profit_total:,}円 (ROI: {roi * 100:.1f}%)")

    # ROIアラート
    if roi < 0.80:
        lines.append("")
        lines.append("⚠️ *ROI低下: モデル見直しを検討してください*")

    msg = "\n".join(lines)
    print(msg)
    send_telegram(msg)

    # 直近4週のROIも確認
    four_weeks_ago = (date(year, month, 1) - timedelta(days=28)).isoformat()
    c.execute("""SELECT SUM(total_bet), SUM(total_payout)
                 FROM daily_summary WHERE date >= ?""", (four_weeks_ago,))
    r2 = c.fetchone()
    if r2 and r2[0] and r2[0] > 0:
        recent_roi = r2[1] / r2[0]
        if recent_roi < 0.80:
            alert = (f"⚠️ *モデル要確認*\n"
                     f"直近4週のROI: {recent_roi * 100:.1f}%\n"
                     f"モデルパラメータの見直しを検討してください。")
            send_telegram(alert)


def main():
    target_date = date.today()
    do_monthly = False

    for arg in sys.argv[1:]:
        if arg == "--monthly":
            do_monthly = True
        elif re.match(r'\d{4}-\d{2}-\d{2}', arg):
            target_date = datetime.strptime(arg, "%Y-%m-%d").date()

    conn = get_conn()
    init_db()  # 新テーブルを作成

    if do_monthly:
        monthly_summary(conn)
        conn.close()
        return

    date_str = target_date.strftime("%Y-%m-%d")
    print(f"結果チェック: {date_str}")

    # 結果スクレイピング
    print("レース結果を取得中...")
    scraped = scrape_day_results(conn, date_str)
    print(f"  {scraped}レース取得完了")

    # 予測との照合
    print("予測結果を照合中...")
    day = check_day_results(conn, date_str)

    if day is None:
        print("照合できるデータがありません。")
        conn.close()
        return

    # 結果表示
    msg = format_result_message(day)
    print("\n" + msg)

    # Telegram送信
    send_telegram(msg)
    print("\nTelegram通知送信完了")

    conn.close()


if __name__ == "__main__":
    main()
