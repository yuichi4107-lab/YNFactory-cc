#!/usr/bin/env python3
"""
Limitless AI lifelogs から事業に有用な情報を抽出し、
`.company/secretary/inbox/YYYY-MM-DD-lifelog-insights.md` に整理する。

Usage:
    python extract_insights.py                   # 昨日分を抽出
    python extract_insights.py 2026-04-13        # 指定日分を抽出
    python extract_insights.py --range 7         # 過去7日分を順次抽出（未処理のみ）
"""
import os
import sys
import json
import datetime
import argparse
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", "biz_idea_generator", ".env"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPANY_DIR = os.path.dirname(BASE_DIR)
CONVERSATIONS_DIR = os.path.join(BASE_DIR, "conversations")
INBOX_DIR = os.path.join(COMPANY_DIR, "secretary", "inbox")

MODEL_NAME = "gemini-2.5-flash"
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "60"))

EXTRACTION_PROMPT = """あなたはオーナーの1日の会話ログを分析し、事業に役立つ情報を抽出・整理するアシスタントです。

# オーナーの事業領域
1. 電子書籍の執筆・制作・出版・プロデュース
2. マンガを使ったコンテンツ制作
3. Instagram転職系アカウント運用
4. YouTubeでの日本史解説動画チャンネル運用
5. フリーランス（AI活用・業務自動化の開発案件）

# ルール
- 会話ログに**実際に含まれる内容**のみを根拠とすること（推測・空想の追加は禁止）
- 各項目には元会話のタイムスタンプ（HH:MM）を含めること
- 雑談や日常会話は無視し、事業判断・タスク・アイデア・人物情報など**ビジネスに関連する情報**だけ抽出する
- 該当なしカテゴリは空配列で返す

# 出力形式
以下のJSONのみを返す（前後の説明文・コードフェンス不要）:

{
  "summary": "1日の要旨を2-3行で",
  "business_ideas": [
    {"title": "...", "description": "...", "domain": "ebook|manga|instagram|youtube|freelance|other", "timestamp": "HH:MM", "potential": 1-5}
  ],
  "action_items": [
    {"task": "...", "priority": "high|normal|low", "due": "YYYY-MM-DD or null", "timestamp": "HH:MM"}
  ],
  "research_topics": [
    {"topic": "...", "reason": "...", "timestamp": "HH:MM"}
  ],
  "contacts": [
    {"name": "...", "context": "...", "timestamp": "HH:MM"}
  ],
  "decisions": [
    {"decision": "...", "timestamp": "HH:MM"}
  ]
}

# 会話ログ
"""


def get_lifelog_path(date: datetime.date) -> str:
    return os.path.join(CONVERSATIONS_DIR, f"{date.strftime('%Y-%m-%d')}-lifelogs.md")


def get_output_path(date: datetime.date) -> str:
    return os.path.join(INBOX_DIR, f"{date.strftime('%Y-%m-%d')}-lifelog-insights.md")


def extract(date: datetime.date, force: bool = False) -> bool:
    src = get_lifelog_path(date)
    dst = get_output_path(date)

    if not os.path.exists(src):
        print(f"  [{date}] Lifelog not found: {src}")
        return False

    if os.path.exists(dst) and not force:
        print(f"  [{date}] Already extracted, skipping: {dst}")
        return False

    with open(src, "r", encoding="utf-8") as f:
        content = f.read()

    if len(content.strip()) < 200:
        print(f"  [{date}] Content too small ({len(content)} chars), skipping")
        return False

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)

    print(f"  [{date}] Calling Gemini ({len(content)} chars)...", flush=True)
    try:
        resp = model.generate_content(
            EXTRACTION_PROMPT + content,
            request_options={"timeout": GEMINI_TIMEOUT_SECONDS},
        )
    except Exception as e:
        print(f"  [{date}] Gemini call failed: {type(e).__name__}: {e}", flush=True)
        return False
    raw = resp.text.strip()

    # Strip markdown code fence if present
    if raw.startswith("```"):
        first_nl = raw.find("\n")
        if first_nl != -1:
            raw = raw[first_nl + 1 :]
        if raw.rstrip().endswith("```"):
            raw = raw.rstrip()[:-3].rstrip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  [{date}] JSON parse error: {e}")
        print(f"  Raw response (first 500 chars): {raw[:500]}")
        return False

    md = render_markdown(date, data)

    os.makedirs(INBOX_DIR, exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(md)

    total = (
        len(data.get("business_ideas", []))
        + len(data.get("action_items", []))
        + len(data.get("research_topics", []))
        + len(data.get("contacts", []))
        + len(data.get("decisions", []))
    )
    print(f"  [{date}] Saved {total} insights → {dst}")
    return True


def render_markdown(date: datetime.date, data: dict) -> str:
    lines = [
        "---",
        f"date: {date.strftime('%Y-%m-%d')}",
        "source: limitless-ai-extraction",
        f"generated_at: {datetime.datetime.now().isoformat()}",
        f"model: {MODEL_NAME}",
        "---",
        "",
        f"# Lifelog Insights - {date.strftime('%Y-%m-%d')}",
        "",
        "## 📋 Summary",
        "",
        data.get("summary", "(none)"),
        "",
    ]

    ideas = data.get("business_ideas", [])
    lines.append(f"## 💡 Business Ideas ({len(ideas)})")
    lines.append("")
    if not ideas:
        lines.append("_(none)_")
    for i, item in enumerate(ideas, 1):
        stars = "★" * int(item.get("potential", 0)) + "☆" * (5 - int(item.get("potential", 0)))
        lines.append(
            f"{i}. **{item.get('title', '')}** [{item.get('domain', '')}] {stars} ({item.get('timestamp', '')})"
        )
        lines.append(f"   - {item.get('description', '')}")
    lines.append("")

    actions = data.get("action_items", [])
    lines.append(f"## ✅ Action Items ({len(actions)})")
    lines.append("")
    if not actions:
        lines.append("_(none)_")
    for item in actions:
        due = item.get("due") or "-"
        pri = item.get("priority", "normal")
        lines.append(f"- [ ] {item.get('task', '')} | 優先度:{pri} | 期限:{due} ({item.get('timestamp', '')})")
    lines.append("")

    topics = data.get("research_topics", [])
    lines.append(f"## 🔍 Research Topics ({len(topics)})")
    lines.append("")
    if not topics:
        lines.append("_(none)_")
    for item in topics:
        lines.append(f"- **{item.get('topic', '')}** ({item.get('timestamp', '')})")
        lines.append(f"  - 理由: {item.get('reason', '')}")
    lines.append("")

    contacts = data.get("contacts", [])
    lines.append(f"## 👥 Contacts ({len(contacts)})")
    lines.append("")
    if not contacts:
        lines.append("_(none)_")
    for item in contacts:
        lines.append(f"- **{item.get('name', '')}** — {item.get('context', '')} ({item.get('timestamp', '')})")
    lines.append("")

    decisions = data.get("decisions", [])
    lines.append(f"## 📝 Decisions ({len(decisions)})")
    lines.append("")
    if not decisions:
        lines.append("_(none)_")
    for item in decisions:
        lines.append(f"- {item.get('decision', '')} ({item.get('timestamp', '')})")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("date", nargs="?", help="YYYY-MM-DD (default: yesterday)")
    parser.add_argument("--range", type=int, help="Process past N days")
    parser.add_argument("--force", action="store_true", help="Overwrite existing insights")
    args = parser.parse_args()

    targets = []
    if args.range:
        for i in range(args.range):
            targets.append(datetime.date.today() - datetime.timedelta(days=i + 1))
    elif args.date:
        targets.append(datetime.date.fromisoformat(args.date))
    else:
        targets.append(datetime.date.today() - datetime.timedelta(days=1))

    print(f"=== Extracting insights for {len(targets)} date(s) ===")
    success = 0
    for d in sorted(targets):
        if extract(d, force=args.force):
            success += 1

    print(f"=== Done! {success}/{len(targets)} extracted ===")


if __name__ == "__main__":
    main()
