#!/usr/bin/env python3
"""
朝7時の morning.py が「オッズ取得失敗 → 注目0レース」だった場合、
9時に自動再実行するリトライ機構。

cron 設定（土日のみ）:
    0 9 * * 6,0 cd /opt/keiba-unified/jra && /usr/bin/python3 scripts/run_morning_retry.py >> data/logs/morning.log 2>&1

判定ロジック:
- 今日の morning.log セクションを読む
- 「オッズ取得: 0/」かつ「注目レース: 0レース」が両方含まれる → リトライ
- それ以外（既に注目あり / 既にX投稿成功） → スキップ
"""

import os
import sys
import subprocess
from datetime import date

LOG_PATH = "/opt/keiba-unified/jra/data/logs/morning.log"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_MORNING = os.path.join(SCRIPT_DIR, "run_morning.py")


def get_today_section() -> str:
    """今日の morning.log セクションのみ抽出。"""
    today = date.today().strftime("%Y-%m-%d")
    marker = f"=== モーニング予想: {today} ==="
    try:
        text = open(LOG_PATH, encoding="utf-8").read()
    except FileNotFoundError:
        return ""
    idx = text.rfind(marker)
    if idx < 0:
        return ""
    # 次の "=== モーニング予想: " マーカーで切る（複数日のログ混在対策）
    section = text[idx:]
    next_marker = section.find("=== モーニング予想: ", len(marker))
    if next_marker > 0:
        section = section[:next_marker]
    return section


def should_retry() -> tuple[bool, str]:
    """リトライすべきか判定。"""
    today_section = get_today_section()
    if not today_section:
        return False, "今日の morning.log セクションが見つからない（朝7時の cron が未実行？）"

    # オッズ取得失敗 + 注目0 のパターン
    has_zero_odds = "オッズ取得: 0/" in today_section
    has_zero_picks = "注目レース: 0レース" in today_section

    # 注目0 + オッズ0 → リトライ（X投稿は注目0でも送信されるため判定材料にしない）
    if has_zero_odds and has_zero_picks:
        return True, "オッズ取得失敗 + 注目0レース → リトライ実行"

    # オッズ取得済みで注目0 → モデルが「自信なし」と判断 → リトライしない
    if has_zero_picks and not has_zero_odds:
        return False, "オッズ取得済み・注目0（モデル判定の防御挙動、リトライ不要）"

    # 注目あり → 既に正常配信済み
    if not has_zero_picks:
        return False, "注目レース1件以上（既に正常配信済み）"

    return False, f"判定不明: zero_odds={has_zero_odds} zero_picks={has_zero_picks}"


def main() -> int:
    print(f"\n=== morning_retry.py 起動: {date.today()} ===")
    retry, reason = should_retry()
    print(f"判定: {'リトライ' if retry else 'スキップ'} ({reason})")

    if not retry:
        return 0

    print(f"\n--- run_morning.py を再実行 ---")
    result = subprocess.run(
        ["/usr/bin/python3", RUN_MORNING],
        cwd="/opt/keiba-unified/jra",
        capture_output=False,
    )
    print(f"\n--- run_morning.py exit: {result.returncode} ---")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
