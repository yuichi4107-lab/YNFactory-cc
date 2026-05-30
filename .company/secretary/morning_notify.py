"""
毎朝のTODO通知スクリプト
Windowsタスクスケジューラから毎朝6:30に実行される想定。

設定方法:
  1. .env ファイルに通知先の認証情報を記載
  2. morning_notify.bat をタスクスケジューラに登録
"""

import os
import sys
import re
import datetime
import smtplib
from email.message import EmailMessage
from pathlib import Path

# Windows cp932環境での文字化け対策
if sys.stdout.encoding and sys.stdout.encoding.lower().startswith("cp"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# --- 設定 ---
SCRIPT_DIR = Path(__file__).resolve().parent
TODOS_DIR = SCRIPT_DIR / "todos"
ENV_FILE = SCRIPT_DIR / ".env"

# 曜日名（日本語）
WEEKDAYS_JA = ["月", "火", "水", "木", "金", "土", "日"]


def load_env():
    """簡易 .env ローダー（python-dotenv不要）"""
    if not ENV_FILE.exists():
        return
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def get_today_todo() -> str | None:
    """今日のTODOファイルを読む。なければNone。"""
    today = datetime.date.today()
    filename = TODOS_DIR / f"{today.isoformat()}.md"
    if filename.exists():
        return filename.read_text(encoding="utf-8")
    return None


def get_latest_todo() -> tuple[str, str] | None:
    """最新のTODOファイルを探す（今日分がない場合のフォールバック）。"""
    todo_files = sorted(TODOS_DIR.glob("2*.md"), reverse=True)
    for f in todo_files:
        if f.name != "_template.md":
            return (f.stem, f.read_text(encoding="utf-8"))
    return None


def extract_tasks(content: str) -> dict:
    """TODOファイルからセクション別にタスクを抽出。"""
    sections = {"最優先": [], "通常": [], "余裕があれば": [], "完了": []}
    current_section = None

    for line in content.split("\n"):
        line = line.strip()
        # セクションヘッダー検出
        if line.startswith("## "):
            header = line[3:].strip()
            if header in sections:
                current_section = header
            elif header == "メモ・振り返り":
                current_section = None
            continue

        if current_section and (line.startswith("- [ ]") or line.startswith("- [x]")):
            # タスク名部分を抽出（| 以降のメタデータは省略形にする）
            task_text = line[6:].strip()
            # プロジェクト名を抽出
            project_match = re.search(r"プロジェクト:\s*(.+?)(?:\s*\||$)", task_text)
            project = project_match.group(1).strip() if project_match else ""
            # タスク名（最初の | まで）
            task_name = task_text.split("|")[0].strip()

            if project:
                sections[current_section].append(f"  {task_name}【{project}】")
            else:
                sections[current_section].append(f"  {task_name}")

    return sections


def format_message(date_str: str, tasks: dict, is_today: bool) -> str:
    """通知メッセージをフォーマット。"""
    try:
        d = datetime.date.fromisoformat(date_str)
        weekday = WEEKDAYS_JA[d.weekday()]
        date_display = f"{d.month}/{d.day}({weekday})"
    except ValueError:
        date_display = date_str

    if is_today:
        header = f"おはようございます！\n今日 {date_display} のタスクです。"
    else:
        header = f"おはようございます！\n今日のTODOがまだ作成されていません。\n直近 {date_display} の未完了タスクです。"

    lines = [header, ""]

    if tasks["最優先"]:
        lines.append(f"■ 最優先（{len(tasks['最優先'])}件）")
        lines.extend(tasks["最優先"])
        lines.append("")

    if tasks["通常"]:
        lines.append(f"■ 通常（{len(tasks['通常'])}件）")
        lines.extend(tasks["通常"])
        lines.append("")

    if tasks["余裕があれば"]:
        lines.append(f"□ 余裕があれば（{len(tasks['余裕があれば'])}件）")
        lines.extend(tasks["余裕があれば"])
        lines.append("")

    total_incomplete = len(tasks["最優先"]) + len(tasks["通常"]) + len(tasks["余裕があれば"])
    done_count = len(tasks["完了"])

    lines.append(f"---\n未完了: {total_incomplete}件 / 完了済み: {done_count}件")
    lines.append("今日も頑張りましょう！")

    return "\n".join(lines)


def send_line_notify(message: str):
    """LINE Notifyで通知を送信。"""
    token = os.getenv("LINE_ACCESS_TOKEN")
    if not token:
        print("[LINE] LINE_ACCESS_TOKEN 未設定。スキップします。")
        return False

    try:
        import requests
    except ImportError:
        print("[LINE] requestsライブラリがインストールされていません。")
        print("       pip install requests を実行してください。")
        return False

    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"message": f"\n{message}"}

    try:
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            print("[LINE] 送信成功")
            return True
        else:
            print(f"[LINE] 送信失敗 (HTTP {response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"[LINE] エラー: {e}")
        return False


def send_email(subject: str, body: str):
    """Gmailで通知メールを送信。"""
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")

    if not all([sender, password, receiver]):
        print("[Email] EMAIL_SENDER/EMAIL_PASSWORD/EMAIL_RECEIVER 未設定。スキップします。")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("[Email] 送信成功")
        return True
    except Exception as e:
        print(f"[Email] エラー: {e}")
        return False


def main():
    print(f"=== 朝のTODO通知 ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")

    # .envを読み込み
    load_env()

    # 今日のTODOを取得
    today = datetime.date.today()
    content = get_today_todo()
    is_today = True

    if content is None:
        # 今日分がなければ最新のTODOから未完了タスクを取得
        result = get_latest_todo()
        if result is None:
            print("TODOファイルが見つかりません。終了します。")
            sys.exit(0)
        date_str, content = result
        is_today = False
    else:
        date_str = today.isoformat()

    # タスク抽出
    tasks = extract_tasks(content)
    total_incomplete = len(tasks["最優先"]) + len(tasks["通常"]) + len(tasks["余裕があれば"])

    if total_incomplete == 0 and is_today:
        print("未完了タスクがありません。通知をスキップします。")
        sys.exit(0)

    # メッセージ生成
    message = format_message(date_str, tasks, is_today)
    print("\n--- メッセージプレビュー ---")
    print(message)
    print("---\n")

    # 通知送信
    weekday = WEEKDAYS_JA[today.weekday()]
    subject = f"【TODO】{today.month}/{today.day}({weekday}) 今日のタスク"

    line_ok = send_line_notify(message)
    email_ok = send_email(subject, message)

    if not line_ok and not email_ok:
        print("\n[警告] LINE・メールどちらも送信できませんでした。")
        print("  .env ファイルに認証情報を設定してください。")
        print(f"  設定ファイル: {ENV_FILE}")


if __name__ == "__main__":
    main()
