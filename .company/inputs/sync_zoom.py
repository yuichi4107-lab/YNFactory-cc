#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
Zoom AI Companion議事録 → .company/inputs/conversations/ 取り込みスクリプト

Usage:
    python sync_zoom.py                  # 昨日の議事録を取り込み
    python sync_zoom.py 2026-03-25       # 指定日の議事録を取り込み
    python sync_zoom.py --range 7        # 過去7日分を取り込み
    python sync_zoom.py --range 30       # 過去30日分を取り込み（初回用）
"""
import os
import sys
import datetime
import argparse

sys.path.insert(0, os.path.dirname(__file__))
from zoom_client import ZoomClient

CONVERSATIONS_DIR = os.path.join(os.path.dirname(__file__), "conversations")


def save_zoom_data(client, from_date, to_date, output_dir):
    """Fetch and save Zoom meeting summaries and transcripts."""
    total_saved = 0

    # Get meeting summaries via list endpoint
    print(f"=== Fetching meeting summaries ({from_date} ~ {to_date}) ===")
    summaries_list = client.list_meeting_summaries(from_date=from_date, to_date=to_date)

    # Get recordings (for transcripts)
    print(f"=== Fetching recordings ({from_date} ~ {to_date}) ===")
    recordings = client.get_recordings(from_date=from_date, to_date=to_date)

    # Build recording map by meeting UUID
    recording_map = {}
    for rec in recordings:
        uuid = rec.get("uuid", "")
        transcript_files = [
            f for f in rec.get("recording_files", [])
            if f.get("file_type") == "TRANSCRIPT" and f.get("status") == "completed"
        ]
        if transcript_files:
            recording_map[uuid] = transcript_files

    # Group summaries by date
    by_date = {}
    for s in summaries_list:
        start = s.get("meeting_start_time", "")
        try:
            dt = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
            date_key = dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            date_key = from_date.strftime("%Y-%m-%d")
        by_date.setdefault(date_key, []).append(s)

    for date_key in sorted(by_date.keys()):
        day_summaries = by_date[date_key]
        filename = f"{date_key}-zoom.md"
        filepath = os.path.join(output_dir, filename)

        lines = [
            "---",
            f"date: {date_key}",
            "source: zoom",
            "type: meeting-summaries",
            f"count: {len(day_summaries)}",
            f"synced_at: {datetime.datetime.now().isoformat()}",
            "---",
            "",
            f"# Zoom Meetings - {date_key}",
            "",
        ]

        for i, entry in enumerate(day_summaries, 1):
            meeting_uuid = entry.get("meeting_uuid", "")
            topic = entry.get("meeting_topic", "Untitled Meeting")
            start_time = entry.get("meeting_start_time", "")
            end_time = entry.get("meeting_end_time", "")

            lines.append("---")
            lines.append("")
            lines.append(f"## Meeting {i}: {topic}")
            lines.append(f"- **Start**: {start_time}")
            lines.append(f"- **End**: {end_time}")
            lines.append("")

            # Get detailed AI Companion summary
            summary = client.get_meeting_summary(meeting_uuid)
            if summary:
                lines.append("### AI Companion Summary")
                lines.append(client.summary_to_markdown(summary, topic))
                lines.append("")
                print(f"    Summary saved: {topic}")
            else:
                print(f"    No detailed summary for: {topic}")

            # Get transcript if available
            transcript_files = recording_map.get(meeting_uuid, [])
            for tf in transcript_files:
                download_url = tf.get("download_url", "")
                if download_url:
                    try:
                        vtt = client.download_transcript(download_url)
                        lines.append("### Transcript")
                        lines.append(client.vtt_to_markdown(vtt, topic))
                        lines.append("")
                        print(f"    Transcript downloaded for: {topic}")
                    except Exception as e:
                        print(f"    Transcript download failed for {topic}: {e}")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"  Saved {len(day_summaries)} meetings → {filename}")
        total_saved += len(day_summaries)

    return total_saved


def main():
    parser = argparse.ArgumentParser(description="Sync Zoom AI Companion meeting summaries")
    parser.add_argument("date", nargs="?", help="Date in YYYY-MM-DD format (default: yesterday)")
    parser.add_argument("--range", type=int, help="Fetch past N days")
    args = parser.parse_args()

    os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
    client = ZoomClient()

    # Zoom API allows max 30-day range per request
    if args.range:
        total = 0
        days_left = args.range
        end_date = datetime.date.today()
        while days_left > 0:
            chunk = min(days_left, 30)
            from_date = end_date - datetime.timedelta(days=chunk)
            total += save_zoom_data(client, from_date, end_date, CONVERSATIONS_DIR)
            end_date = from_date
            days_left -= chunk
        print(f"\n=== Done! Total meetings saved: {total} ===")
    else:
        if args.date:
            from_date = datetime.date.fromisoformat(args.date)
        else:
            from_date = datetime.date.today() - datetime.timedelta(days=1)
        to_date = from_date + datetime.timedelta(days=1)
        total = save_zoom_data(client, from_date, to_date, CONVERSATIONS_DIR)
        print(f"\n=== Done! Total meetings saved: {total} ===")


if __name__ == "__main__":
    main()
