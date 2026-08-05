#!/usr/bin/env python3
"""
Google Meet notes/transcripts -> 04_インプット/inputs/conversations/.

Google Meet often stores transcripts and meeting notes as Google Docs. This
script ingests exported or synced files from 04_インプット/inputs/00_GOOGLE_MEET_BOX,
keeps raw copies, writes normalized text, and rebuilds daily conversation files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from import_drive_inbox import (
    build_import_item,
    copy_raw_files,
    normalize_tags,
    normalize_todos,
    read_json,
    should_ignore,
    workspace_path,
    write_json,
    write_normalized_files,
)


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
SOURCE_DIR = BASE_DIR / "00_GOOGLE_MEET_BOX"
RAW_BASE_DIR = BASE_DIR / "intake" / "google_meet" / "raw"
STATE_FILE = BASE_DIR / "intake" / "state" / "google_meet_imported.json"
CONVERSATIONS_DIR = BASE_DIR / "conversations"

DATE_RE = re.compile(r"(\d{4})[-_/年.]?(\d{1,2})[-_/月.]?(\d{1,2})")
TIME_RE = re.compile(r"(\d{1,2})[:時](\d{2})")


@dataclass
class MeetEntry:
    input_id: str
    title: str
    date: str
    start: str
    end: str
    participants: list[str]
    tags: list[str]
    todo_candidates: list[str]
    source_path: str
    raw_dir: str
    normalized_path: str
    normalized_text: str


def now_jst() -> dt.datetime:
    return dt.datetime.now().astimezone()


def slugify(value: str, fallback: str = "google-meet") -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:48] or fallback


def iter_source_items(source_dir: Path) -> list[Path]:
    if not source_dir.exists():
        return []
    return sorted(path for path in source_dir.iterdir() if not should_ignore(path))


def infer_date(path: Path, metadata: dict[str, Any]) -> str:
    value = str(metadata.get("date", "")).strip()
    if value:
        try:
            return dt.date.fromisoformat(value[:10]).isoformat()
        except ValueError:
            pass
    for candidate in [path.name, str(path)]:
        match = DATE_RE.search(candidate)
        if match:
            year, month, day = [int(part) for part in match.groups()]
            try:
                return dt.date(year, month, day).isoformat()
            except ValueError:
                pass
    return dt.datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()


def infer_time(path: Path, metadata: dict[str, Any], key: str) -> str:
    value = str(metadata.get(key, "")).strip()
    if value:
        return value
    match = TIME_RE.search(path.name)
    if match and key == "start":
        hour, minute = match.groups()
        return f"{int(hour):02d}:{minute}"
    return ""


def title_for(path: Path, metadata: dict[str, Any]) -> str:
    title = str(metadata.get("title", "")).strip()
    if title:
        return title
    return path.stem if path.is_file() else path.name


def participants_for(metadata: dict[str, Any]) -> list[str]:
    value = metadata.get("participants", [])
    if isinstance(value, str):
        return [part.strip() for part in re.split(r"[,、\n]", value) if part.strip()]
    if isinstance(value, list):
        return [str(part).strip() for part in value if str(part).strip()]
    return []


def combined_normalized_text(raw_dir: Path) -> str:
    path = raw_dir / "normalized" / "all-normalized-content.md"
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    return ""


def imported_entry_from_raw(raw_dir: Path) -> MeetEntry | None:
    metadata_path = raw_dir / "metadata.json"
    if not metadata_path.exists():
        return None
    metadata = read_json(metadata_path, {})
    if not isinstance(metadata, dict):
        return None
    normalized_path = raw_dir / "normalized" / "all-normalized-content.md"
    return MeetEntry(
        input_id=str(metadata.get("input_id", raw_dir.name)),
        title=str(metadata.get("title", raw_dir.name)),
        date=str(metadata.get("date", raw_dir.parent.name)),
        start=str(metadata.get("start", "")),
        end=str(metadata.get("end", "")),
        participants=[str(item) for item in metadata.get("participants", [])],
        tags=[str(item) for item in metadata.get("tags", [])],
        todo_candidates=[str(item) for item in metadata.get("todo_candidates", [])],
        source_path=str(metadata.get("source_path", "")),
        raw_dir=workspace_path(raw_dir),
        normalized_path=workspace_path(normalized_path),
        normalized_text=combined_normalized_text(raw_dir),
    )


def render_meet_day(date: str, entries: list[MeetEntry]) -> str:
    lines = [
        "---",
        f"date: {date}",
        "source: google-meet",
        "type: meeting-notes",
        f"count: {len(entries)}",
        f"synced_at: {now_jst().isoformat(timespec='seconds')}",
        "---",
        "",
        f"# Google Meet - {date}",
        "",
    ]
    for index, entry in enumerate(entries, 1):
        text = entry.normalized_text.strip()
        overview = re.sub(r"\s+", " ", text).strip()
        if len(overview) > 800:
            overview = overview[:800].rstrip() + "..."
        lines.extend(
            [
                "---",
                "",
                f"## Meeting {index}: {entry.title}",
                f"- **Start**: {entry.start or '-'}",
                f"- **End**: {entry.end or '-'}",
                f"- **Participants**: {', '.join(entry.participants) if entry.participants else '-'}",
                f"- **Raw Dir**: `{entry.raw_dir}`",
                f"- **Normalized**: `{entry.normalized_path}`",
                f"- **Source**: `{entry.source_path}`",
                "",
                "### Overview",
                overview or "_概要なし_",
                "",
                "### Notes / Transcript",
                text or "_抽出テキストなし。raw 原本を参照してください。_",
                "",
                "### Next Steps",
            ]
        )
        if entry.todo_candidates:
            lines.extend(f"- {todo}" for todo in entry.todo_candidates)
        else:
            lines.append("_明示されたNext Stepsなし_")
        lines.append("")
    return "\n".join(lines)


def rebuild_conversations() -> None:
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    by_date: dict[str, list[MeetEntry]] = {}
    for raw_dir in sorted(RAW_BASE_DIR.glob("*/*")):
        if not raw_dir.is_dir():
            continue
        entry = imported_entry_from_raw(raw_dir)
        if entry:
            by_date.setdefault(entry.date, []).append(entry)
    for date, entries in by_date.items():
        path = CONVERSATIONS_DIR / f"{date}-google-meet.md"
        path.write_text(render_meet_day(date, entries), encoding="utf-8")
        print(f"  Rebuilt conversation → {path}")


def import_item(path: Path, force: bool) -> bool:
    item = build_import_item(path, SOURCE_DIR)
    if not item:
        print(f"  Skipped empty item: {path}")
        return False
    state = read_json(STATE_FILE, {"imported": {}})
    imported = state.setdefault("imported", {})
    key = f"{item.relative_path}:{item.signature}"
    if key in imported and not force:
        print(f"  Already imported, skipping: {item.relative_path}")
        return False

    metadata = item.metadata
    date = infer_date(path, metadata)
    title = title_for(path, metadata)
    input_id = f"{now_jst().strftime('%Y%m%d-%H%M%S')}-{slugify(title)}-{item.signature[:8]}"
    raw_dir = RAW_BASE_DIR / date / input_id
    if raw_dir.exists() and force:
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    copied_files = copy_raw_files(item, raw_dir)
    normalized_files = write_normalized_files(item, raw_dir)
    raw_metadata = {
        "input_id": input_id,
        "imported_at": now_jst().isoformat(timespec="seconds"),
        "source_path": item.relative_path,
        "source_is_directory": item.is_directory,
        "signature": item.signature,
        "title": title,
        "date": date,
        "start": infer_time(path, metadata, "start"),
        "end": infer_time(path, metadata, "end"),
        "participants": participants_for(metadata),
        "tags": normalize_tags(metadata.get("tags", [])),
        "todo_candidates": normalize_todos(metadata),
        "metadata": metadata,
        "files": copied_files,
        "normalized_files": normalized_files,
    }
    write_json(raw_dir / "metadata.json", raw_metadata)
    imported[key] = {
        "input_id": input_id,
        "raw_dir": workspace_path(raw_dir),
        "imported_at": raw_metadata["imported_at"],
        "source_path": item.relative_path,
        "signature": item.signature,
    }
    state["updated_at"] = now_jst().isoformat(timespec="seconds")
    write_json(STATE_FILE, state)
    print(f"  Imported: {item.relative_path} -> {raw_dir}")
    return True


def main() -> None:
    global SOURCE_DIR, RAW_BASE_DIR, STATE_FILE, CONVERSATIONS_DIR

    parser = argparse.ArgumentParser(description="Sync Google Meet notes/transcripts")
    parser.add_argument("--all", action="store_true", help="Import all source items")
    parser.add_argument("--force", action="store_true", help="Re-import even if already imported")
    parser.add_argument("--no-rebuild", action="store_true", help="Do not rebuild conversation files")
    parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR, help="Google Meet source box")
    parser.add_argument("--raw-base", type=Path, default=RAW_BASE_DIR, help="Raw output base directory")
    parser.add_argument("--state-file", type=Path, default=STATE_FILE, help="Import state JSON path")
    parser.add_argument("--conversations-dir", type=Path, default=CONVERSATIONS_DIR, help="Conversation output directory")
    args = parser.parse_args()

    SOURCE_DIR = args.source_dir
    RAW_BASE_DIR = args.raw_base
    STATE_FILE = args.state_file
    CONVERSATIONS_DIR = args.conversations_dir

    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    targets = iter_source_items(SOURCE_DIR)
    print(f"=== Sync Google Meet source items: {len(targets)} ===")
    imported_count = 0
    for target in targets:
        if import_item(target, args.force):
            imported_count += 1
    if not args.no_rebuild:
        rebuild_conversations()
    print(f"=== Done! imported={imported_count} ===")


if __name__ == "__main__":
    main()
