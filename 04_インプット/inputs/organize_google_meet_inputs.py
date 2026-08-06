#!/usr/bin/env python3
"""
Google Meet conversation files -> organized inputs and indexes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
COMPANY_DIR = BASE_DIR.parent
CONVERSATIONS_DIR = BASE_DIR / "conversations"
ORGANIZED_DIR = BASE_DIR / "organized" / "google-meet"
INDEX_DIR = BASE_DIR / "indexes"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MEET_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-google-meet\.md$")
MEETING_RE = re.compile(r"^## Meeting\s+(\d+):\s*(.+)$", re.MULTILINE)


@dataclass
class MeetMeeting:
    date: str
    number: int
    title: str
    start: str
    end: str
    participants: str
    raw_dir: str
    normalized_path: str
    source_path: str
    overview: str
    notes: str
    next_steps: list[str]
    raw_path: Path


@dataclass
class MeetDay:
    date: str
    meetings: list[MeetMeeting]
    raw_path: Path

    @property
    def organized_path(self) -> Path:
        return ORGANIZED_DIR / f"{self.date}-google-meet-meetings.md"


def today() -> dt.date:
    return dt.date.today()


def parse_date(value: str) -> dt.date:
    if not DATE_RE.match(value):
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD")
    return dt.date.fromisoformat(value)


def workspace_path(path: Path) -> str:
    try:
        return str(path.relative_to(COMPANY_DIR.parent))
    except ValueError:
        return str(path)


def clean_text(value: str) -> str:
    return value.strip()


def excerpt(value: str, limit: int = 160) -> str:
    one_line = re.sub(r"\s+", " ", value).strip()
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 1].rstrip() + "..."


def extract_field(block: str, label: str) -> str:
    match = re.search(rf"^- \*\*{re.escape(label)}\*\*:\s*(.+)$", block, re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_heading_block(block: str, heading: str) -> str:
    pattern = rf"^### {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^### |^---\s*$|\Z)"
    match = re.search(pattern, block, re.MULTILINE | re.DOTALL)
    return clean_text(match.group("body")) if match else ""


def clean_step(value: str) -> str:
    step = value.strip()
    step = re.sub(r"^[-*]\s*", "", step).strip()
    if step in {"", "-", "--", "---", "_明示されたNext Stepsなし_"}:
        return ""
    return step


def parse_steps(raw: str) -> list[str]:
    return [step for line in raw.splitlines() if (step := clean_step(line))]


def split_meetings(text: str) -> list[tuple[int, str, str]]:
    matches = list(MEETING_RE.finditer(text))
    meetings = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        meetings.append((int(match.group(1)), match.group(2).strip(), text[start:end]))
    return meetings


def load_meet_day(path: Path) -> MeetDay | None:
    match = MEET_FILE_RE.match(path.name)
    if not match:
        return None
    date = match.group(1)
    text = path.read_text(encoding="utf-8", errors="replace")
    meetings = []
    for number, title, block in split_meetings(text):
        meetings.append(
            MeetMeeting(
                date=date,
                number=number,
                title=title,
                start=extract_field(block, "Start"),
                end=extract_field(block, "End"),
                participants=extract_field(block, "Participants"),
                raw_dir=extract_field(block, "Raw Dir").strip("`"),
                normalized_path=extract_field(block, "Normalized").strip("`"),
                source_path=extract_field(block, "Source").strip("`"),
                overview=extract_heading_block(block, "Overview"),
                notes=extract_heading_block(block, "Notes / Transcript"),
                next_steps=parse_steps(extract_heading_block(block, "Next Steps")),
                raw_path=path,
            )
        )
    return MeetDay(date=date, meetings=meetings, raw_path=path)


def tags_for(day: MeetDay) -> list[str]:
    tags = ["google-meet", "meeting-notes", "organized-input"]
    if any(meeting.next_steps for meeting in day.meetings):
        tags.append("todo-candidates")
    if any("面接" in meeting.title or "面接" in meeting.notes for meeting in day.meetings):
        tags.append("interview")
    if any("採用" in meeting.title or "採用" in meeting.notes for meeting in day.meetings):
        tags.append("recruiting")
    return tags


def render_steps(steps: list[str]) -> list[str]:
    if not steps:
        return ["_該当なし_"]
    return [f"- [ ] {step}" for step in steps]


def render_organized(day: MeetDay) -> str:
    generated_at = dt.datetime.now().isoformat(timespec="seconds")
    tags = "\n".join(f"  - {tag}" for tag in tags_for(day))
    lines = [
        "---",
        f"date: {day.date}",
        "source: google-meet",
        "type: organized-input",
        "input_type: google-meet-notes",
        f"meeting_count: {len(day.meetings)}",
        f"generated_at: {generated_at}",
        f"raw_source: {workspace_path(day.raw_path)}",
        "tags:",
        tags,
        "---",
        "",
        f"# Google Meet 整理済みインプット - {day.date}",
        "",
        "## 出典",
        "",
        f"- 原本: `{workspace_path(day.raw_path)}`",
        f"- 会議数: {len(day.meetings)}",
        "",
        "## 会議一覧",
        "",
    ]
    if not day.meetings:
        lines.append("_該当する会議なし_")
    for meeting in day.meetings:
        lines.append(f"- Meeting {meeting.number}: {meeting.title} ({meeting.start} - {meeting.end})")
    lines.append("")

    for meeting in day.meetings:
        lines.extend(
            [
                f"## Meeting {meeting.number}: {meeting.title}",
                "",
                f"- Start: {meeting.start or '-'}",
                f"- End: {meeting.end or '-'}",
                f"- Participants: {meeting.participants or '-'}",
                f"- Raw Dir: `{meeting.raw_dir}`",
                f"- Normalized: `{meeting.normalized_path}`",
                "",
                "### 概要",
                "",
                meeting.overview or "_概要なし_",
                "",
                "### Notes / Transcript",
                "",
                meeting.notes or "_抽出テキストなし_",
                "",
                "### Next Steps / TODO候補",
                "",
                *render_steps(meeting.next_steps),
                "",
                "### 活用メモ",
                "",
                "- Next Steps はそのまま日別TODOへ入れず、相手・案件・完了状況を確認してから反映する。",
                "- Google Docs 原本が直接読めない場合は normalized のMarkdownを参照する。",
                "- 商談・面接・顧客情報として継続利用する場合は、案件別ファイルや顧客別メモへ昇格する。",
                "",
            ]
        )
    return "\n".join(lines)


def write_organized(day: MeetDay, force: bool) -> bool:
    ORGANIZED_DIR.mkdir(parents=True, exist_ok=True)
    if day.organized_path.exists() and not force:
        print(f"  [{day.date}] Already organized, skipping: {day.organized_path}")
        return False
    day.organized_path.write_text(render_organized(day), encoding="utf-8")
    print(f"  [{day.date}] Organized → {day.organized_path}")
    return True


def iter_all_meet_files() -> list[Path]:
    return sorted(CONVERSATIONS_DIR.glob("*-google-meet.md"))


def meet_path_for(date: dt.date) -> Path:
    return CONVERSATIONS_DIR / f"{date.strftime('%Y-%m-%d')}-google-meet.md"


def resolve_targets(args: argparse.Namespace) -> list[Path]:
    if args.all:
        return iter_all_meet_files()
    if args.range:
        return [meet_path_for(today() - dt.timedelta(days=i + 1)) for i in range(args.range)]
    if args.date:
        return [meet_path_for(args.date)]
    return [meet_path_for(today() - dt.timedelta(days=1))]


def collect_existing_days() -> list[MeetDay]:
    days = []
    for path in iter_all_meet_files():
        day = load_meet_day(path)
        if day:
            days.append(day)
    return days


def index_header(title: str, description: str) -> list[str]:
    return [
        "---",
        "source: organize_google_meet_inputs.py",
        "type: input-index",
        "scope: google-meet-notes",
        f"generated_at: {dt.datetime.now().isoformat(timespec='seconds')}",
        "---",
        "",
        f"# {title}",
        "",
        description,
        "",
        "> 自動生成ファイル。必要な修正は元の organized input または organizer に反映する。",
        "",
    ]


def source_suffix(day: MeetDay) -> str:
    return f"`{workspace_path(day.organized_path)}`"


def render_meetings_index(days: list[MeetDay]) -> str:
    lines = index_header("Google Meet Meetings", "Google Meet 議事録・文字起こしの会議一覧。")
    for day in sorted(days, key=lambda item: item.date, reverse=True):
        if not day.meetings:
            continue
        lines.extend([f"## {day.date}", ""])
        for meeting in day.meetings:
            lines.append(
                f"- {meeting.title} | start:{meeting.start or '-'} | participants:{meeting.participants or '-'} | source:{source_suffix(day)}"
            )
        lines.append("")
    return "\n".join(lines)


def render_next_steps_index(days: list[MeetDay]) -> str:
    lines = index_header("Google Meet Next Steps", "Google Meet 由来の Next Steps。日別TODOへ反映する前に確認する。")
    for day in sorted(days, key=lambda item: item.date, reverse=True):
        items = [(meeting, step) for meeting in day.meetings for step in meeting.next_steps]
        if not items:
            continue
        lines.extend([f"## {day.date}", ""])
        for meeting, step in items:
            lines.append(f"- [ ] {step} | meeting:{meeting.title} | source:{source_suffix(day)}")
        lines.append("")
    return "\n".join(lines)


def render_topics_index(days: list[MeetDay]) -> str:
    lines = index_header("Google Meet Topics", "Google Meet 議事録に出てくる会議テーマの入口。")
    for day in sorted(days, key=lambda item: item.date, reverse=True):
        if not day.meetings:
            continue
        lines.extend([f"## {day.date}", ""])
        for meeting in day.meetings:
            summary = excerpt(meeting.overview or meeting.notes)
            lines.append(f"- {meeting.title} | summary:{summary or '概要なし'} | source:{source_suffix(day)}")
        lines.append("")
    return "\n".join(lines)


def rebuild_indexes() -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    days = collect_existing_days()
    outputs = {
        "google-meet-meetings.md": render_meetings_index(days),
        "google-meet-next-steps.md": render_next_steps_index(days),
        "google-meet-topics.md": render_topics_index(days),
    }
    for filename, content in outputs.items():
        path = INDEX_DIR / filename
        path.write_text(content + "\n", encoding="utf-8")
        print(f"  Rebuilt index → {path}")


def main() -> None:
    global CONVERSATIONS_DIR, ORGANIZED_DIR, INDEX_DIR

    parser = argparse.ArgumentParser(description="Organize Google Meet notes")
    parser.add_argument("date", nargs="?", type=parse_date, help="YYYY-MM-DD (default: yesterday)")
    parser.add_argument("--range", type=int, help="Organize past N days")
    parser.add_argument("--all", action="store_true", help="Organize all Google Meet raw files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing organized daily files")
    parser.add_argument("--no-index", action="store_true", help="Do not rebuild Google Meet indexes")
    parser.add_argument("--conversations-dir", type=Path, default=CONVERSATIONS_DIR, help="Google Meet conversation directory")
    parser.add_argument("--organized-dir", type=Path, default=ORGANIZED_DIR, help="Organized output directory")
    parser.add_argument("--index-dir", type=Path, default=INDEX_DIR, help="Index output directory")
    args = parser.parse_args()

    CONVERSATIONS_DIR = args.conversations_dir
    ORGANIZED_DIR = args.organized_dir
    INDEX_DIR = args.index_dir

    targets = resolve_targets(args)
    print(f"=== Organizing {len(targets)} Google Meet raw file(s) ===")
    organized_count = 0
    for path in targets:
        if not path.exists():
            print(f"  Missing Google Meet file, skipping: {path}")
            continue
        day = load_meet_day(path)
        if not day:
            print(f"  Not a Google Meet raw file, skipping: {path}")
            continue
        if write_organized(day, args.force):
            organized_count += 1
    if not args.no_index:
        rebuild_indexes()
    print(f"=== Done! {organized_count}/{len(targets)} organized ===")


if __name__ == "__main__":
    main()
