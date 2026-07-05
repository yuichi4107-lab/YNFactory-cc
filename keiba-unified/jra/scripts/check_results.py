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
from scraper_legacy import HEADERS, REQUEST_INTERVAL, scrape_race, scrape_result_live_netkeiba, init_db
from run_today import _build_jra_result_cname_map, scrape_result_jra
from backtest_legacy import check_hit

# Telegram設定
TG_TOKEN = os.environ.get("TG_TOKEN_JRA", os.environ.get("TG_TOKEN", ""))
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "8571447808")

# --no-notify / 再集計リプレイ時に Telegram 送信を抑制するためのフラグ
NOTIFY = True


def send_telegram(message):
    """Telegramにメッセージ送信"""
    if not NOTIFY:
        return
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

        # 当日ライブ結果(race.netkeiba)を試す（当日中に着順・払戻が掲載される）
        if scrape_result_live_netkeiba(race_id, conn):
            scraped += 1
            print(" OK (live)")
            time.sleep(0.5)
            continue

        # 履歴DB(db.netkeiba)にフォールバック（過去日・当日反映後向け）
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

        # prediction_results に保存（source別に独立保存）
        c.execute("""INSERT OR REPLACE INTO prediction_results
                     (date, race_id, venue, race_number, race_name, bet_type,
                      bet_total, hit, payout, profit, quality_score, source)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (date_str, race_id, venue, race_number, race_name,
                   info["bet_type"], bet_total, hit, payout, profit,
                   info["quality_score"], source))

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
    """予測と結果を照合して収支を計算（morning/live を合算せず source別に独立保存）"""
    morning = _check_source_results(conn, date_str, "morning")
    morning_nv = _check_source_results(conn, date_str, "morning_nv")
    live = _check_source_results(conn, date_str, "live")
    live_c3 = _check_source_results(conn, date_str, "live_c3")
    live_santan = _check_source_results(conn, date_str, "live_santan")

    if not morning and not live and not morning_nv and not live_c3 and not live_santan:
        print(f"予測データなし: {date_str}")
        return None

    # daily_summary に source別で独立保存（合算行は作らない）
    c = conn.cursor()
    for src in (morning, morning_nv, live, live_c3, live_santan):
        if not src:
            continue
        races = len(src["results"])
        hits = src["hits"]
        hit_rate = hits / races if races else 0
        c.execute("""INSERT OR REPLACE INTO daily_summary
                     (date, source, races_bet, races_hit, total_bet,
                      total_payout, profit, roi, hit_rate)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (date_str, src["source"], races, hits, src["total_bet"],
                   src["total_payout"], src["profit"], src["roi"], hit_rate))
    conn.commit()

    return {
        "date": date_str,
        "morning": morning,
        "morning_nv": morning_nv,
        "live": live,
        "live_c3": live_c3,
        "live_santan": live_santan,
    }


def _source_cumulative(conn, source, upto_date):
    """指定source単独の累計（daily_summaryベース、upto_date以前を合算）"""
    if conn is None:
        return None
    c = conn.cursor()
    c.execute("""SELECT COUNT(*), SUM(races_bet), SUM(races_hit),
                        SUM(total_bet), SUM(total_payout), SUM(profit)
                 FROM daily_summary WHERE source = ? AND date <= ?""",
              (source, upto_date))
    row = c.fetchone()
    if not row or not row[3]:
        return None
    days, races, hits, bet, payout, profit = row
    roi = payout / bet if bet else 0
    return {"days": days, "races": races or 0, "hits": hits or 0,
            "bet": bet or 0, "payout": payout or 0, "profit": profit or 0, "roi": roi}


def _format_source_section(src, label, conn=None, date_str=None):
    """1ソース分のレポートセクションを生成（source単独の累計付き）"""
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

    # source単独の累計
    cum = _source_cumulative(conn, src["source"], date_str)
    if cum:
        csign = "+" if cum["profit"] >= 0 else ""
        lines.append(f"  └ 累計{cum['days']}日: {csign}{cum['profit']:,}円 "
                     f"(ROI {cum['roi']*100:.1f}% / {cum['hits']}/{cum['races']}的中)")

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


def format_result_message(day, conn=None):
    """Telegram用の結果メッセージを生成（朝予想・ライブを合算せず独立表示）"""
    d = day["date"]
    lines = [f"📊 *競馬結果速報 {d}*", ""]

    # 朝予想の結果（単独累計付き）
    lines.extend(_format_source_section(day.get("morning"), "🌅 朝予想", conn, d))
    lines.append("")

    # ライブモードの結果（単独累計付き）
    lines.extend(_format_source_section(day.get("live"), "🔴 ライブ", conn, d))
    lines.append("")

    # ライブC3（オッズ抜きモデル並走・予想時は無通知）の結果（単独累計付き）
    if day.get("live_c3"):
        lines.extend(_format_source_section(day.get("live_c3"), "🟣 ライブC3(オッズ抜き)", conn, d))
        lines.append("")

    # サンタンシャドー（新馬未勝利ダ短の三連単1点・記録のみ）の結果（単独累計付き）
    if day.get("live_santan"):
        lines.extend(_format_source_section(day.get("live_santan"), "🎯 サンタンシャドー(新馬未勝利ダ短)", conn, d))
        lines.append("")

    # A/Bテスト（バリューなし版）
    if day.get("morning_nv"):
        lines.extend(_format_source_section(day.get("morning_nv"), "🧪 朝予想B(バリューなし)", conn, d))
        lines.append("")
        # 比較サマリー
        m = day.get("morning")
        nv = day.get("morning_nv")
        if m and nv:
            lines.append("*🔬 A/B比較*")
            lines.append(f"  A(現行): {m['hits']}/{m['races']}的中 ROI {m['roi']*100:.0f}%")
            lines.append(f"  B(提案): {nv['hits']}/{nv['races']}的中 ROI {nv['roi']*100:.0f}%")
            diff = nv['profit'] - m['profit']
            lines.append(f"  差分: {diff:+,}円(B-A)")
            lines.append("")

    # ※ 朝予想とライブは独立集計のため「合計」欄は設けない
    return "\n".join(lines).rstrip()


SRC_LABELS = {"morning": "🌅 朝予想", "live": "🔴 ライブ", "morning_nv": "🧪 朝予想B",
              "live_c3": "🟣 ライブC3(オッズ抜き)",
              "live_santan": "🎯 サンタンシャドー(新馬未勝利ダ短)"}


def monthly_summary(conn, year=None, month=None):
    """月間サマリーを生成して送信（朝予想・ライブを合算せず source別に集計）"""
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
    c.execute("""SELECT source, COUNT(*), SUM(races_bet), SUM(races_hit),
                        SUM(total_bet), SUM(total_payout), SUM(profit)
                 FROM daily_summary WHERE date >= ? AND date < ?
                 GROUP BY source ORDER BY source""", (start, end))
    rows = c.fetchall()

    if not rows:
        print(f"{year}年{month}月: データなし")
        return

    lines = [f"📈 *月間成績 {year}年{month}月*"]
    for source, days, races, hit_total, bet_total, payout_total, profit_total in rows:
        if not races:
            continue
        label = SRC_LABELS.get(source, source)
        roi = payout_total / bet_total if bet_total else 0
        hit_rate = hit_total / races if races else 0
        sign = "+" if profit_total >= 0 else ""
        lines.append("")
        lines.append(f"*{label}*")
        lines.append(f"開催{days}日 / {races}レース / 的中{hit_total} ({hit_rate * 100:.1f}%)")
        lines.append(f"投資 {bet_total:,}円 → 回収 {payout_total:,}円")
        lines.append(f"収支 {sign}{profit_total:,}円 (ROI {roi * 100:.1f}%)")
        if roi < 0.80:
            lines.append("  ⚠️ ROI低下: 見直し検討")

    msg = "\n".join(lines)
    print(msg)
    send_telegram(msg)

    # 直近4週のROIも source別に確認
    four_weeks_ago = (date(year, month, 1) - timedelta(days=28)).isoformat()
    c.execute("""SELECT source, SUM(total_bet), SUM(total_payout)
                 FROM daily_summary WHERE date >= ?
                 GROUP BY source""", (four_weeks_ago,))
    for source, bet, payout in c.fetchall():
        if bet and bet > 0:
            recent_roi = payout / bet
            if recent_roi < 0.80:
                label = SRC_LABELS.get(source, source)
                alert = (f"⚠️ *モデル要確認 ({label})*\n"
                         f"直近4週のROI: {recent_roi * 100:.1f}%\n"
                         f"モデルパラメータの見直しを検討してください。")
                send_telegram(alert)


def main():
    global NOTIFY
    target_date = date.today()
    do_monthly = False

    for arg in sys.argv[1:]:
        if arg == "--monthly":
            do_monthly = True
        elif arg == "--no-notify":
            NOTIFY = False  # 再集計リプレイ時に Telegram 送信を止める
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
    msg = format_result_message(day, conn)
    print("\n" + msg)

    # Telegram送信
    send_telegram(msg)
    print("\nTelegram通知送信完了")


    # ====================================================
    # --- 穴予想（Longshot Wide）結果チェック ---
    # ====================================================
    try:
        import sys as _sys_ls
        _sys_ls.path.insert(0, os.path.dirname(__file__))
        from longshot_wide_tracker import check_longshot_results, format_longshot_result_message

        for src_name, src_label in [("morning", "モーニング"), ("live", "直前")]:
            print(f"\n穴予想({src_label}) 結果チェック中...")
            ls_result = check_longshot_results(date_str, source=src_name)
            if ls_result:
                ls_msg = format_longshot_result_message(ls_result)
                ls_msg = ls_msg.replace("穴予想 結果速報", f"穴予想({src_label}) 結果速報")
                print(ls_msg)
                send_telegram(ls_msg)
                print(f"穴予想({src_label})結果 Telegram送信完了")
            else:
                print(f"穴予想({src_label}): 予測データなし（スキップ）")
    except Exception as _ls_e:
        import traceback as _tb
        print(f"穴予想結果チェックエラー（既存処理には影響なし）: {_ls_e}")
        _tb.print_exc()

    conn.close()


if __name__ == "__main__":
    main()
