#!/usr/bin/env python3
"""
Generate a daily review for accumulated input materials.

Phase 1 intentionally stops at review generation. It does not write to
secretary/todos, HANDOFF, or project state files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent
COMPANY_DIR = BASE_DIR.parent
ROOT_DIR = COMPANY_DIR.parent
CONVERSATIONS_DIR = BASE_DIR / "conversations"
ORGANIZED_DIR = BASE_DIR / "organized"
INDEX_DIR = BASE_DIR / "indexes"
REVIEWS_DIR = BASE_DIR / "reviews"
SECRETARY_INBOX_DIR = COMPANY_DIR / "secretary" / "inbox"

JST = ZoneInfo("Asia/Tokyo")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SECTION_DATE_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$")
SOURCE_RE = re.compile(r"source:`([^`]+)`")
PRIORITY_RE = re.compile(r"(?:priority|優先度)\s*[:：]\s*([^|]+)")
DUE_RE = re.compile(r"(?:due|期限)\s*[:：]\s*([^|]+)")
LONG_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_-])([A-Za-z0-9_-]{24,})(?![A-Za-z0-9_-])")

SENSITIVE_TERMS = [
    "api_key",
    "apikey",
    "bearer",
    "client_secret",
    "gocspx",
    "oauth",
    "password",
    "refresh_token",
    "rootパスワード",
    "secret",
    "sk_live",
    "token",
    "whsec",
    "パスワード",
    "マイナンバー",
    "個人情報",
    "認証",
]


@dataclass
class CommandResult:
    label: str
    command: list[str]
    returncode: int
    output: str


@dataclass
class IndexItem:
    index_name: str
    item_date: dt.date | None
    text: str
    source_path: str
    priority: str
    due: str
    line_no: int


def today_jst() -> dt.date:
    return dt.datetime.now(JST).date()


def now_jst_iso() -> str:
    return dt.datetime.now(JST).isoformat(timespec="seconds")


def parse_date(value: str) -> dt.date:
    if not DATE_RE.match(value):
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD")
    return dt.date.fromisoformat(value)


def workspace_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT_DIR.resolve()))
    except ValueError:
        return str(path)


def count_files(path: Path, pattern: str = "*") -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob(pattern) if p.is_file())


def run_command(label: str, command: list[str], timeout: int) -> CommandResult:
    try:
        result = subprocess.run(
            command,
            cwd=str(BASE_DIR),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        output = (result.stdout + result.stderr).strip()
        return CommandResult(label, command, result.returncode, summarize_output(output))
    except subprocess.TimeoutExpired as exc:
        output = ((exc.stdout or "") + (exc.stderr or "")).strip()
        return CommandResult(label, command, 124, summarize_output(output or "timeout"))
    except OSError as exc:
        return CommandResult(label, command, 127, str(exc))


def summarize_output(output: str, max_lines: int = 12) -> str:
    if not output:
        return ""
    lines = output.splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    head = lines[:4]
    tail = lines[-(max_lines - len(head) - 1) :]
    return "\n".join(head + [f"... omitted {len(lines) - len(head) - len(tail)} lines ..."] + tail)


def refresh_local_indexes(lookback_days: int, timeout: int) -> list[CommandResult]:
    py = sys.executable
    commands = [
        ("drive inbox import", [py, "import_drive_inbox.py"]),
        ("lifelog organize/index", [py, "organize_inputs.py", "--range", str(lookback_days)]),
        ("zoom organize/index", [py, "organize_zoom_inputs.py", "--all"]),
        ("google meet sync", [py, "sync_google_meet.py"]),
        ("google meet organize/index", [py, "organize_google_meet_inputs.py", "--all"]),
    ]
    return [run_command(label, command, timeout) for label, command in commands]


def refresh_external_indexes(lookback_days: int, timeout: int) -> list[CommandResult]:
    py = sys.executable
    commands = [
        ("limitless sync", [py, "sync_limitless.py", "--range", str(lookback_days)]),
        ("lifelog extract", [py, "extract_insights.py", "--range", str(lookback_days)]),
        ("zoom sync", [py, "sync_zoom.py"]),
    ]
    return [run_command(label, command, timeout) for label, command in commands]


def parse_index(path: Path, index_name: str) -> list[IndexItem]:
    if not path.exists():
        return []
    items: list[IndexItem] = []
    current_date: dt.date | None = None
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        section_match = SECTION_DATE_RE.match(raw_line)
        if section_match:
            current_date = dt.date.fromisoformat(section_match.group(1))
            continue
        if not raw_line.startswith("- "):
            continue
        if "source:`" not in raw_line and not raw_line.startswith("- [ ]"):
            continue
        source_match = SOURCE_RE.search(raw_line)
        priority_match = PRIORITY_RE.search(raw_line)
        due_match = DUE_RE.search(raw_line)
        text = clean_item_text(raw_line)
        items.append(
            IndexItem(
                index_name=index_name,
                item_date=current_date,
                text=text,
                source_path=source_match.group(1) if source_match else workspace_path(path),
                priority=normalize_field(priority_match.group(1)) if priority_match else "-",
                due=normalize_field(due_match.group(1)) if due_match else "-",
                line_no=line_no,
            )
        )
    return items


def clean_item_text(raw_line: str) -> str:
    text = raw_line[2:].strip()
    text = re.sub(r"^\[\s*\]\s*", "", text).strip()
    text = re.sub(r"^-\s+", "", text).strip()
    parts = [part.strip() for part in text.split(" | ")]
    metadata_prefixes = ("time:", "priority:", "due:", "source:")
    kept = [part for part in parts if not part.lower().startswith(metadata_prefixes)]
    cleaned = " | ".join(kept).strip()
    return cleaned or text


def normalize_field(value: str) -> str:
    return value.strip().strip("`").strip()


def in_window(item: IndexItem, start: dt.date, end: dt.date) -> bool:
    if item.item_date is None:
        return True
    return start <= item.item_date <= end


def has_due(item: IndexItem) -> bool:
    if item.due in {"", "-", "null", "None"}:
        return False
    return True


def is_high_priority(item: IndexItem) -> bool:
    value = item.priority.lower()
    return "high" in value or "高" in item.priority


def item_score(item: IndexItem, review_date: dt.date) -> tuple[int, str]:
    score = 0
    reason = []
    if is_high_priority(item):
        score += 3
        reason.append("high")
    if has_due(item):
        score += 2
        reason.append("due")
        try:
            due = dt.date.fromisoformat(item.due[:10])
            if due <= review_date:
                score += 2
                reason.append("due-now")
        except ValueError:
            pass
    if item.item_date == review_date or item.item_date == review_date - dt.timedelta(days=1):
        score += 1
        reason.append("recent")
    if contains_sensitive(item.text):
        score += 1
        reason.append("sensitive-check")
    return score, ",".join(reason) or "recent"


def collect_items() -> tuple[list[IndexItem], list[IndexItem], list[IndexItem]]:
    todo_indexes = [
        (INDEX_DIR / "lifelog-todo-candidates.md", "lifelog TODO"),
        (INDEX_DIR / "zoom-next-steps.md", "Zoom next steps"),
        (INDEX_DIR / "google-meet-next-steps.md", "Google Meet next steps"),
        (INDEX_DIR / "external-todo-candidates.md", "external TODO"),
    ]
    decision_indexes = [
        (INDEX_DIR / "lifelog-decisions.md", "lifelog decisions"),
    ]
    topic_indexes = [
        (INDEX_DIR / "lifelog-topics.md", "lifelog topics"),
        (INDEX_DIR / "google-meet-topics.md", "Google Meet topics"),
    ]
    todos = [item for path, name in todo_indexes for item in parse_index(path, name)]
    decisions = [item for path, name in decision_indexes for item in parse_index(path, name)]
    topics = [item for path, name in topic_indexes for item in parse_index(path, name)]
    return todos, decisions, topics


def contains_sensitive(text: str) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in SENSITIVE_TERMS) or bool(LONG_TOKEN_RE.search(text))


def mask_sensitive(text: str) -> str:
    masked = LONG_TOKEN_RE.sub("[redacted-token]", text)
    masked = re.sub(r"(password|token|secret|api_key|client_secret)\s*[:=]\s*[^|\s]+", r"\1=[redacted]", masked, flags=re.IGNORECASE)
    return masked


def sensitive_terms(text: str) -> list[str]:
    lower = text.lower()
    matched = [term for term in SENSITIVE_TERMS if term.lower() in lower]
    if LONG_TOKEN_RE.search(text):
        matched.append("long-token-like-string")
    return sorted(set(matched))


def lifelog_backlog() -> tuple[int, list[str]]:
    raw_dates = {p.name[:10] for p in CONVERSATIONS_DIR.glob("*-lifelogs.md")}
    organized_dates = {p.name[:10] for p in (ORGANIZED_DIR / "lifelogs").glob("*-lifelog-insights.md")}
    missing = sorted(raw_dates - organized_dates)
    return len(missing), missing


def render_command_results(results: list[CommandResult]) -> list[str]:
    if not results:
        return ["- skipped"]
    lines: list[str] = []
    for result in results:
        status = "OK" if result.returncode == 0 else f"WARN({result.returncode})"
        command = " ".join(result.command)
        lines.append(f"- {status}: {result.label} (`{command}`)")
        if result.output:
            for out_line in result.output.splitlines()[:4]:
                lines.append(f"  - {out_line}")
    return lines


def render_items(items: list[IndexItem], empty_text: str, limit: int) -> list[str]:
    if not items:
        return [empty_text]
    lines: list[str] = []
    for item in items[:limit]:
        text = mask_sensitive(item.text)
        date = item.item_date.isoformat() if item.item_date else "-"
        lines.extend(
            [
                f"- [ ] {text}",
                f"  - date: {date}",
                f"  - source: `{item.source_path}`",
                f"  - index: {item.index_name}:{item.line_no}",
                f"  - priority: {item.priority}",
                f"  - due: {item.due}",
                "  - route_decision: 未判定",
            ]
        )
    return lines


def render_sensitive(items: list[IndexItem], limit: int) -> list[str]:
    sensitive = [item for item in items if contains_sensitive(item.text)]
    if not sensitive:
        return ["_該当なし_"]
    lines: list[str] = []
    for item in sensitive[:limit]:
        date = item.item_date.isoformat() if item.item_date else "-"
        terms = ", ".join(sensitive_terms(item.text))
        lines.extend(
            [
                "- [ ] 機密・個人情報候補を確認",
                f"  - date: {date}",
                f"  - matched_terms: {terms}",
                f"  - source: `{item.source_path}`",
                f"  - index: {item.index_name}:{item.line_no}",
                "  - route_decision: 要確認",
            ]
        )
    return lines


def inventory_lines() -> list[str]:
    missing_count, missing_dates = lifelog_backlog()
    latest_missing = ", ".join(missing_dates[-10:]) if missing_dates else "-"
    return [
        f"- raw conversations: {count_files(CONVERSATIONS_DIR, '*.md')}",
        f"- raw lifelogs: {count_files(CONVERSATIONS_DIR, '*-lifelogs.md')}",
        f"- organized lifelogs: {count_files(ORGANIZED_DIR / 'lifelogs', '*-lifelog-insights.md')}",
        f"- unorganized lifelog dates: {missing_count}",
        f"- latest missing lifelog dates: {latest_missing}",
        f"- raw Zoom files: {count_files(CONVERSATIONS_DIR, '*-zoom.md')}",
        f"- organized Zoom files: {count_files(ORGANIZED_DIR / 'zoom', '*-zoom-meetings.md')}",
        f"- raw Google Meet files: {count_files(CONVERSATIONS_DIR, '*-google-meet.md')}",
        f"- organized Google Meet files: {count_files(ORGANIZED_DIR / 'google-meet', '*-google-meet-meetings.md')}",
        f"- external organized inputs: {count_files(ORGANIZED_DIR / 'external', '*.md')}",
        f"- indexes: {count_files(INDEX_DIR, '*.md')}",
        f"- secretary inbox lifelog insights: {count_files(SECRETARY_INBOX_DIR, '*-lifelog-insights.md')}",
    ]


def render_review(args: argparse.Namespace, command_results: list[CommandResult]) -> str:
    review_date = args.date
    start_date = review_date - dt.timedelta(days=args.lookback_days)
    todos, decisions, topics = collect_items()
    window_todos = [item for item in todos if in_window(item, start_date, review_date)]
    scored_todos = sorted(
        window_todos,
        key=lambda item: item_score(item, review_date),
        reverse=True,
    )
    action_todos = [
        item
        for item in scored_todos
        if is_high_priority(item) or has_due(item) or contains_sensitive(item.text)
    ]
    if not action_todos:
        action_todos = scored_todos[: args.todo_limit]

    window_decisions = [item for item in decisions if in_window(item, start_date, review_date)]
    window_topics = [item for item in topics if in_window(item, start_date, review_date)]
    all_for_sensitive = window_todos + window_decisions + window_topics
    missing_count, missing_dates = lifelog_backlog()

    lines = [
        "---",
        f"date: {review_date.isoformat()}",
        "type: input-review",
        "source: process_daily_inputs.py",
        f"generated_at: {now_jst_iso()}",
        f"lookback_days: {args.lookback_days}",
        "todo_auto_apply: false",
        "---",
        "",
        f"# Input Review - {review_date.isoformat()}",
        "",
        "## 判定",
        "",
        "- Phase 1 output only: 日別TODO、HANDOFF、プロジェクト状態ファイルは自動更新しない。",
        "- TODO候補は未判定として扱い、重複・完了済み・優先度を確認してから別工程で反映する。",
        "- 機密・個人情報候補は本文を広げず、出典と検出語だけを確認対象にする。",
        "",
        "## 更新結果",
        "",
        *render_command_results(command_results),
        "",
        "## 在庫サマリ",
        "",
        *inventory_lines(),
        "",
        "## 今日見るべきTODO候補",
        "",
        *render_items(action_todos, "_該当なし_", args.todo_limit),
        "",
        "## 決定事項候補",
        "",
        *render_items(window_decisions, "_該当なし_", args.decision_limit),
        "",
        "## 機密・個人情報候補",
        "",
        *render_sensitive(all_for_sensitive, args.sensitive_limit),
        "",
        "## 未整理バックログ",
        "",
        f"- unorganized lifelog dates: {missing_count}",
        f"- sample: {', '.join(missing_dates[:8]) if missing_dates else '-'}",
        f"- latest: {', '.join(missing_dates[-8:]) if missing_dates else '-'}",
        "",
        "## 次の処理",
        "",
        "- レビュー内の `route_decision` を見て、必要なものだけ今日のTODO・プロジェクトファイル・保留へ振り分ける。",
        "- `--force` で再生成するとこのファイルは上書きされるため、手動判定を書き込んだ後は再生成しない。",
        "- Phase 2 で承認付きの TODO 反映コマンドを追加する。",
        "",
    ]
    return "\n".join(lines)


def write_review(args: argparse.Namespace, text: str) -> Path:
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    path = REVIEWS_DIR / f"{args.date.isoformat()}-input-review.md"
    if path.exists() and not args.force:
        raise FileExistsError(f"review already exists; use --force to overwrite: {workspace_path(path)}")
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate daily input review")
    parser.add_argument("--date", type=parse_date, default=today_jst(), help="Review date YYYY-MM-DD")
    parser.add_argument("--lookback-days", type=int, default=14, help="Recent window for review candidates")
    parser.add_argument("--todo-limit", type=int, default=30, help="Maximum TODO candidates in the review")
    parser.add_argument("--decision-limit", type=int, default=20, help="Maximum decision candidates in the review")
    parser.add_argument("--sensitive-limit", type=int, default=20, help="Maximum sensitive candidates in the review")
    parser.add_argument("--command-timeout", type=int, default=120, help="Timeout per refresh command")
    parser.add_argument("--skip-refresh", action="store_true", help="Do not run local index refresh commands")
    parser.add_argument("--allow-external", action="store_true", help="Also run external/API sync and extraction commands")
    parser.add_argument("--force", action="store_true", help="Overwrite existing review file")
    args = parser.parse_args()

    command_results: list[CommandResult] = []
    if not args.skip_refresh:
        command_results.extend(refresh_local_indexes(args.lookback_days, args.command_timeout))
    if args.allow_external:
        command_results.extend(refresh_external_indexes(args.lookback_days, args.command_timeout))

    review = render_review(args, command_results)
    path = write_review(args, review)
    print(f"Saved input review: {workspace_path(path)}")


if __name__ == "__main__":
    main()
