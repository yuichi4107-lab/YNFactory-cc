#!/usr/bin/env python3
"""
Zoom meeting summaries -> organized inputs and Zoom indexes.

Usage:
    python organize_zoom_inputs.py                 # organize yesterday
    python organize_zoom_inputs.py 2026-02-26      # organize one date
    python organize_zoom_inputs.py --range 30      # organize past N days
    python organize_zoom_inputs.py --all           # organize all Zoom raw files
    python organize_zoom_inputs.py --force         # overwrite organized daily files
"""
import argparse
import ast
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
COMPANY_DIR = BASE_DIR.parent
CONVERSATIONS_DIR = BASE_DIR / "conversations"
ORGANIZED_DIR = BASE_DIR / "organized" / "zoom"
INDEX_DIR = BASE_DIR / "indexes"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ZOOM_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-zoom\.md$")
MEETING_RE = re.compile(r"^## Meeting\s+(\d+):\s*(.+)$", re.MULTILINE)


@dataclass
class ZoomMeeting:
    date: str
    number: int
    title: str
    start: str
    end: str
    overview: str
    next_steps: list[str]
    raw_path: Path


@dataclass
class ZoomDay:
    date: str
    meetings: list[ZoomMeeting]
    raw_path: Path

    @property
    def organized_path(self) -> Path:
        return ORGANIZED_DIR / f"{self.date}-zoom-meetings.md"


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
    lines = [line.rstrip() for line in value.strip().splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines).strip()


def excerpt(value: str, limit: int = 140) -> str:
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


def clean_step(value: object) -> str:
    step = str(value).strip()
    step = re.sub(r"^[-*]\s*", "", step).strip()
    if step.lower() in {"", "-", "--", "---", "[]", "none", "null", "n/a"}:
        return ""
    if step in {"なし", "該当なし", "_該当なし_"}:
        return ""
    return step


def parse_literal_steps(value: str) -> list[str] | None:
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return None
    if isinstance(parsed, list):
        return [step for item in parsed if (step := clean_step(item))]
    if isinstance(parsed, str):
        step = clean_step(parsed)
        return [step] if step else []
    return None


def parse_next_steps(raw: str) -> list[str]:
    if not raw:
        return []
    stripped = raw.strip()

    literal_steps = parse_literal_steps(stripped)
    if literal_steps is not None:
        return literal_steps

    steps = []
    for line in stripped.splitlines():
        line = clean_step(line)
        if not line:
            continue
        literal_line_steps = parse_literal_steps(line)
        if literal_line_steps is not None:
            steps.extend(literal_line_steps)
        else:
            steps.append(line)
    return steps


def split_meetings(text: str) -> list[tuple[int, str, str]]:
    matches = list(MEETING_RE.finditer(text))
    meetings = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        meetings.append((int(match.group(1)), match.group(2).strip(), text[start:end]))
    return meetings


def load_zoom_day(path: Path) -> ZoomDay | None:
    match = ZOOM_FILE_RE.match(path.name)
    if not match:
        return None
    date = match.group(1)
    text = path.read_text(encoding="utf-8", errors="replace")

    meetings = []
    for number, title, block in split_meetings(text):
        overview = extract_heading_block(block, "Overview")
        next_steps = parse_next_steps(extract_heading_block(block, "Next Steps"))
        meetings.append(
            ZoomMeeting(
                date=date,
                number=number,
                title=title,
                start=extract_field(block, "Start"),
                end=extract_field(block, "End"),
                overview=overview,
                next_steps=next_steps,
                raw_path=path,
            )
        )

    return ZoomDay(date=date, meetings=meetings, raw_path=path)


def tags_for(day: ZoomDay) -> list[str]:
    tags = ["zoom", "meeting-summary", "organized-input"]
    if any(meeting.next_steps for meeting in day.meetings):
        tags.append("todo-candidates")
    if any("面接" in meeting.title for meeting in day.meetings):
        tags.append("interview")
    if any("採用" in meeting.overview or "採用" in meeting.title for meeting in day.meetings):
        tags.append("recruiting")
    return tags


def render_next_steps(steps: list[str]) -> list[str]:
    if not steps:
        return ["_該当なし_"]
    return [f"- [ ] {step}" for step in steps]


def render_organized(day: ZoomDay) -> str:
    generated_at = dt.datetime.now().isoformat(timespec="seconds")
    tags = "\n".join(f"  - {tag}" for tag in tags_for(day))
    meeting_count = len(day.meetings)

    lines = [
        "---",
        f"date: {day.date}",
        "source: zoom",
        "type: organized-input",
        "input_type: zoom-meeting-summaries",
        f"meeting_count: {meeting_count}",
        f"generated_at: {generated_at}",
        f"raw_source: {workspace_path(day.raw_path)}",
        "tags:",
        tags,
        "---",
        "",
        f"# Zoom 整理済みインプット - {day.date}",
        "",
        "## 出典",
        "",
        f"- 原本: `{workspace_path(day.raw_path)}`",
        f"- 会議数: {meeting_count}",
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
                "",
                "### 概要",
                "",
                meeting.overview or "_概要なし_",
                "",
                "### Next Steps / TODO候補",
                "",
                *render_next_steps(meeting.next_steps),
                "",
                "### 活用メモ",
                "",
                "- Next Steps はそのまま日別TODOへ入れず、相手・案件・完了状況を確認してから反映する。",
                "- 商談・面接・顧客情報として継続利用する場合は、案件別ファイルや顧客別メモへ昇格する。",
                "- 原文確認が必要な場合は raw Zoom 議事録を参照する。",
                "",
            ]
        )

    return "\n".join(lines)


def write_organized(day: ZoomDay, force: bool) -> bool:
    ORGANIZED_DIR.mkdir(parents=True, exist_ok=True)
    if day.organized_path.exists() and not force:
        print(f"  [{day.date}] Already organized, skipping: {day.organized_path}")
        return False
    day.organized_path.write_text(render_organized(day), encoding="utf-8")
    print(f"  [{day.date}] Organized → {day.organized_path}")
    return True


def iter_all_zoom_files() -> list[Path]:
    return sorted(CONVERSATIONS_DIR.glob("*-zoom.md"))


def zoom_path_for(date: dt.date) -> Path:
    return CONVERSATIONS_DIR / f"{date.strftime('%Y-%m-%d')}-zoom.md"


def resolve_targets(args: argparse.Namespace) -> list[Path]:
    if args.all:
        return iter_all_zoom_files()
    if args.range:
        return [zoom_path_for(today() - dt.timedelta(days=i + 1)) for i in range(args.range)]
    if args.date:
        return [zoom_path_for(args.date)]
    return [zoom_path_for(today() - dt.timedelta(days=1))]


def collect_existing_days() -> list[ZoomDay]:
    days = []
    for path in iter_all_zoom_files():
        day = load_zoom_day(path)
        if day:
            days.append(day)
    return days


def index_header(title: str, description: str) -> list[str]:
    generated_at = dt.datetime.now().isoformat(timespec="seconds")
    return [
        "---",
        "source: organize_zoom_inputs.py",
        "type: input-index",
        "scope: zoom-meeting-summaries",
        f"generated_at: {generated_at}",
        "---",
        "",
        f"# {title}",
        "",
        description,
        "",
        "> 自動生成ファイル。必要な修正は元の organized input または organizer に反映する。",
        "",
    ]


def source_suffix(day: ZoomDay) -> str:
    return f"`{workspace_path(day.organized_path)}`"


def render_meetings_index(days: list[ZoomDay]) -> str:
    lines = index_header(
        "Zoom Meetings",
        "Zoom AI Companion 議事録の会議一覧。詳細確認は source の organized input と raw 議事録を参照する。",
    )
    for day in sorted(days, key=lambda item: item.date, reverse=True):
        if not day.meetings:
            continue
        lines.extend([f"## {day.date}", ""])
        for meeting in day.meetings:
            lines.append(
                f"- {meeting.title} | start:{meeting.start or '-'} | end:{meeting.end or '-'} | source:{source_suffix(day)}"
            )
        lines.append("")
    return "\n".join(lines)


def render_next_steps_index(days: list[ZoomDay]) -> str:
    lines = index_header(
        "Zoom Next Steps",
        "Zoom 議事録由来の Next Steps。日別TODOへ反映する前に案件状態と完了状況を確認する。",
    )
    for day in sorted(days, key=lambda item: item.date, reverse=True):
        items = [(meeting, step) for meeting in day.meetings for step in meeting.next_steps]
        if not items:
            continue
        lines.extend([f"## {day.date}", ""])
        for meeting, step in items:
            lines.append(f"- [ ] {step} | meeting:{meeting.title} | source:{source_suffix(day)}")
        lines.append("")
    return "\n".join(lines)


def render_clients_index(days: list[ZoomDay]) -> str:
    lines = index_header(
        "Zoom Clients and Counterparties",
        "Zoom 議事録に出てくる商談相手・面接・顧客候補の入口。",
    )
    for day in sorted(days, key=lambda item: item.date, reverse=True):
        if not day.meetings:
            continue
        lines.extend([f"## {day.date}", ""])
        for meeting in day.meetings:
            summary = excerpt(meeting.overview) if meeting.overview else "概要なし"
            lines.append(f"- {meeting.title} | summary:{summary} | source:{source_suffix(day)}")
        lines.append("")
    return "\n".join(lines)


def rebuild_indexes() -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    days = collect_existing_days()
    outputs = {
        "zoom-meetings.md": render_meetings_index(days),
        "zoom-next-steps.md": render_next_steps_index(days),
        "zoom-clients.md": render_clients_index(days),
    }
    for filename, content in outputs.items():
        path = INDEX_DIR / filename
        path.write_text(content + "\n", encoding="utf-8")
        print(f"  Rebuilt index → {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Organize Zoom meeting summaries")
    parser.add_argument("date", nargs="?", type=parse_date, help="YYYY-MM-DD (default: yesterday)")
    parser.add_argument("--range", type=int, help="Organize past N days")
    parser.add_argument("--all", action="store_true", help="Organize all Zoom raw files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing organized daily files")
    parser.add_argument("--no-index", action="store_true", help="Do not rebuild Zoom indexes")
    args = parser.parse_args()

    targets = resolve_targets(args)
    print(f"=== Organizing {len(targets)} Zoom raw file(s) ===")

    organized_count = 0
    for path in targets:
        if not path.exists():
            print(f"  Missing Zoom file, skipping: {path}")
            continue
        day = load_zoom_day(path)
        if not day:
            print(f"  Not a Zoom raw file, skipping: {path}")
            continue
        if write_organized(day, args.force):
            organized_count += 1

    if not args.no_index:
        rebuild_indexes()

    print(f"=== Done! {organized_count}/{len(targets)} organized ===")


if __name__ == "__main__":
    main()
