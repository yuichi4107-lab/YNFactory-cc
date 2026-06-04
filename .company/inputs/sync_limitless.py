#!/usr/bin/env python3
"""
Limitless AI → .company/inputs/conversations/ 日次バッチ取り込みスクリプト

Usage:
    python sync_limitless.py                 # 昨日の会話を取り込み
    python sync_limitless.py 2026-03-25      # 指定日の会話を取り込み
    python sync_limitless.py --range 7       # 過去7日分を取り込み
    python sync_limitless.py --all           # 全会話を取り込み（初回用）
"""
import os
import sys
import datetime
import argparse

# Add parent path to import limitless_client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "biz_idea_generator", "src"))
from limitless_client import LimitlessClient

CONVERSATIONS_DIR = os.path.join(os.path.dirname(__file__), "conversations")


def save_daily_lifelogs(client, date, output_dir):
    """Fetch and save lifelogs for a single date as markdown."""
    lifelogs = client.fetch_lifelogs(date=date)
    filename = f"{date.strftime('%Y-%m-%d')}-lifelogs.md"
    filepath = os.path.join(output_dir, filename)

    if not lifelogs:
        lines = [
            f"---",
            f"date: {date.strftime('%Y-%m-%d')}",
            f"source: limitless-ai",
            f"type: lifelogs",
            f"count: 0",
            f"synced_at: {datetime.datetime.now().isoformat()}",
            f"---",
            f"",
            f"# Lifelogs - {date.strftime('%Y-%m-%d')}",
            f"",
            "_No lifelogs returned by the Limitless API for this date._",
            f"",
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"  No lifelogs for {date}; saved empty marker → {filepath}")
        return 0

    lines = [
        f"---",
        f"date: {date.strftime('%Y-%m-%d')}",
        f"source: limitless-ai",
        f"type: lifelogs",
        f"count: {len(lifelogs)}",
        f"synced_at: {datetime.datetime.now().isoformat()}",
        f"---",
        f"",
        f"# Lifelogs - {date.strftime('%Y-%m-%d')}",
        f"",
    ]

    for i, log in enumerate(lifelogs, 1):
        lines.append(f"---")
        lines.append(f"")
        lines.append(f"### Entry {i}")
        lines.append(client.lifelog_to_markdown(log))
        lines.append(f"")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  Saved {len(lifelogs)} lifelogs → {filepath}")
    return len(lifelogs)


def save_daily_chats(client, output_dir):
    """Fetch and save all chats (not date-filtered by API, so we save once)."""
    chats = client.fetch_chats()
    if not chats:
        print("  No chats found")
        return 0

    # Group chats by date
    by_date = {}
    for chat in chats:
        started = chat.get("startedAt") or chat.get("createdAt", "")
        if started:
            try:
                dt = datetime.datetime.fromisoformat(started.replace("Z", "+00:00"))
                date_key = dt.strftime("%Y-%m-%d")
            except ValueError:
                date_key = "unknown"
        else:
            date_key = "unknown"
        by_date.setdefault(date_key, []).append(chat)

    total = 0
    for date_key, day_chats in sorted(by_date.items()):
        filename = f"{date_key}-chats.md"
        filepath = os.path.join(output_dir, filename)

        lines = [
            f"---",
            f"date: {date_key}",
            f"source: limitless-ai",
            f"type: chats",
            f"count: {len(day_chats)}",
            f"synced_at: {datetime.datetime.now().isoformat()}",
            f"---",
            f"",
            f"# Chats - {date_key}",
            f"",
        ]

        for i, chat in enumerate(day_chats, 1):
            summary = chat.get("summary", "No summary")
            lines.append(f"## Chat {i}: {summary}")
            lines.append(f"")
            for msg in chat.get("messages", []):
                role = msg.get("role", "unknown")
                text = msg.get("text", "")
                lines.append(f"**{role}**: {text}")
                lines.append(f"")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"  Saved {len(day_chats)} chats → {filepath}")
        total += len(day_chats)

    return total


def main():
    parser = argparse.ArgumentParser(description="Sync Limitless AI conversations")
    parser.add_argument("date", nargs="?", help="Date in YYYY-MM-DD format (default: yesterday)")
    parser.add_argument("--range", type=int, help="Fetch past N days")
    parser.add_argument("--all", action="store_true", help="Fetch all available data")
    parser.add_argument("--chats", action="store_true", help="Also sync chat history")
    args = parser.parse_args()

    os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

    client = LimitlessClient()
    total_lifelogs = 0

    if args.all:
        print("=== Fetching ALL lifelogs (no date filter) ===")
        lifelogs = client.fetch_lifelogs(date=False)
        # Group by date and save
        by_date = {}
        for log in lifelogs:
            start = log.get("startTime", "")
            try:
                dt = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
                date_key = dt.date()
            except ValueError:
                date_key = datetime.date.today()
            by_date.setdefault(date_key, []).append(log)

        for date_key in sorted(by_date.keys()):
            day_logs = by_date[date_key]
            filename = f"{date_key.strftime('%Y-%m-%d')}-lifelogs.md"
            filepath = os.path.join(CONVERSATIONS_DIR, filename)
            lines = [
                f"---",
                f"date: {date_key.strftime('%Y-%m-%d')}",
                f"source: limitless-ai",
                f"type: lifelogs",
                f"count: {len(day_logs)}",
                f"synced_at: {datetime.datetime.now().isoformat()}",
                f"---",
                f"",
                f"# Lifelogs - {date_key.strftime('%Y-%m-%d')}",
                f"",
            ]
            for i, log in enumerate(day_logs, 1):
                lines.append(f"---")
                lines.append(f"")
                lines.append(f"### Entry {i}")
                lines.append(client.lifelog_to_markdown(log))
                lines.append(f"")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            print(f"  Saved {len(day_logs)} lifelogs → {filename}")
            total_lifelogs += len(day_logs)

    elif args.range:
        print(f"=== Fetching past {args.range} days ===")
        for i in range(args.range):
            date = datetime.date.today() - datetime.timedelta(days=i + 1)
            total_lifelogs += save_daily_lifelogs(client, date, CONVERSATIONS_DIR)

    else:
        if args.date:
            date = datetime.date.fromisoformat(args.date)
        else:
            date = datetime.date.today() - datetime.timedelta(days=1)
        print(f"=== Fetching lifelogs for {date} ===")
        total_lifelogs = save_daily_lifelogs(client, date, CONVERSATIONS_DIR)

    if args.chats:
        print(f"\n=== Fetching chat history ===")
        save_daily_chats(client, CONVERSATIONS_DIR)

    print(f"\n=== Done! Total lifelogs saved: {total_lifelogs} ===")


if __name__ == "__main__":
    main()
