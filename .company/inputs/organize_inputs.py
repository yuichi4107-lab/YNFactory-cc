#!/usr/bin/env python3
"""
Extracted lifelog insights -> organized inputs and lifelog indexes.

Usage:
    python organize_inputs.py                 # organize yesterday
    python organize_inputs.py 2026-06-02      # organize one date
    python organize_inputs.py --range 16      # organize past N days
    python organize_inputs.py --all           # organize all extracted lifelog insights
    python organize_inputs.py --force         # overwrite organized daily files
"""
import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
COMPANY_DIR = BASE_DIR.parent
INBOX_DIR = COMPANY_DIR / "secretary" / "inbox"
CONVERSATIONS_DIR = BASE_DIR / "conversations"
ORGANIZED_DIR = BASE_DIR / "organized" / "lifelogs"
INDEX_DIR = BASE_DIR / "indexes"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
INSIGHT_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-lifelog-insights\.md$")


@dataclass
class Insight:
    date: str
    summary: str
    business_ideas: list[str]
    action_items: list[str]
    research_topics: list[str]
    contacts: list[str]
    decisions: list[str]
    source_path: Path
    raw_path: Path

    @property
    def organized_path(self) -> Path:
        return ORGANIZED_DIR / f"{self.date}-lifelog-insights.md"


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


def strip_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1 :])
    return text


def classify_heading(heading: str) -> str | None:
    if "Summary" in heading:
        return "summary"
    if "Business Ideas" in heading:
        return "business_ideas"
    if "Action Items" in heading:
        return "action_items"
    if "Research Topics" in heading:
        return "research_topics"
    if "Contacts" in heading:
        return "contacts"
    if "Decisions" in heading:
        return "decisions"
    return None


def parse_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {
        "summary": [],
        "business_ideas": [],
        "action_items": [],
        "research_topics": [],
        "contacts": [],
        "decisions": [],
    }
    current: str | None = None

    for line in strip_frontmatter(text).splitlines():
        if line.startswith("## "):
            current = classify_heading(line)
            continue
        if current:
            sections[current].append(line.rstrip())

    return sections


def clean_lines(lines: list[str]) -> list[str]:
    cleaned = []
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            continue
        if stripped == "_(none)_":
            continue
        cleaned.append(stripped)
    return cleaned


def clean_summary(lines: list[str]) -> str:
    cleaned = clean_lines(lines)
    return "\n".join(cleaned).strip() or "該当する要約なし。"


def load_insight(path: Path) -> Insight | None:
    match = INSIGHT_FILE_RE.match(path.name)
    if not match:
        return None

    date = match.group(1)
    text = path.read_text(encoding="utf-8")
    sections = parse_sections(text)
    raw_path = CONVERSATIONS_DIR / f"{date}-lifelogs.md"

    return Insight(
        date=date,
        summary=clean_summary(sections["summary"]),
        business_ideas=clean_lines(sections["business_ideas"]),
        action_items=clean_lines(sections["action_items"]),
        research_topics=clean_lines(sections["research_topics"]),
        contacts=clean_lines(sections["contacts"]),
        decisions=clean_lines(sections["decisions"]),
        source_path=path,
        raw_path=raw_path,
    )


def tags_for(insight: Insight) -> list[str]:
    tags = ["lifelog", "limitless-ai", "organized-input"]
    if insight.action_items:
        tags.append("todo-candidates")
    if insight.decisions:
        tags.append("decisions")
    if insight.contacts:
        tags.append("contacts")
    if insight.research_topics:
        tags.append("research-topics")
    if insight.business_ideas:
        tags.append("business-ideas")
    return tags


def render_list(items: list[str], empty_text: str) -> list[str]:
    if not items:
        return [empty_text]
    return items


def render_organized(insight: Insight) -> str:
    generated_at = dt.datetime.now().isoformat(timespec="seconds")
    tags = "\n".join(f"  - {tag}" for tag in tags_for(insight))

    lines = [
        "---",
        f"date: {insight.date}",
        "source: limitless-ai-extraction",
        "type: organized-input",
        "input_type: lifelog-insights",
        f"generated_at: {generated_at}",
        f"raw_source: {workspace_path(insight.raw_path)}",
        f"extraction_source: {workspace_path(insight.source_path)}",
        "tags:",
        tags,
        "---",
        "",
        f"# Limitless AI 整理済みインプット - {insight.date}",
        "",
        "## 要約",
        "",
        insight.summary,
        "",
        "## 出典",
        "",
        f"- 原本: `{workspace_path(insight.raw_path)}`",
        f"- 抽出元: `{workspace_path(insight.source_path)}`",
        "",
        "## TODO候補",
        "",
        *render_list(
            insight.action_items,
            "_該当なし_",
        ),
        "",
        "## 決定事項",
        "",
        *render_list(
            insight.decisions,
            "_該当なし_",
        ),
        "",
        "## 人物・連絡先",
        "",
        *render_list(
            insight.contacts,
            "_該当なし_",
        ),
        "",
        "## 調査トピック",
        "",
        *render_list(
            insight.research_topics,
            "_該当なし_",
        ),
        "",
        "## 事業アイデア",
        "",
        *render_list(
            insight.business_ideas,
            "_該当なし_",
        ),
        "",
        "## 活用メモ",
        "",
        "- TODO候補はそのまま日別TODOへ入れず、既存タスク・完了状況・今日の優先度を確認してから反映する。",
        "- 決定事項や人物情報が継続的に重要な場合は、該当プロジェクトの状態ファイルや長期メモリへ昇格する。",
        "- 原文確認が必要な場合は、必ず原本ファイルを参照する。",
        "",
    ]

    return "\n".join(lines)


def write_organized(insight: Insight, force: bool) -> bool:
    ORGANIZED_DIR.mkdir(parents=True, exist_ok=True)
    if insight.organized_path.exists() and not force:
        print(f"  [{insight.date}] Already organized, skipping: {insight.organized_path}")
        return False
    insight.organized_path.write_text(render_organized(insight), encoding="utf-8")
    print(f"  [{insight.date}] Organized → {insight.organized_path}")
    return True


def iter_all_insight_files() -> list[Path]:
    return sorted(INBOX_DIR.glob("*-lifelog-insights.md"))


def insight_path_for(date: dt.date) -> Path:
    return INBOX_DIR / f"{date.strftime('%Y-%m-%d')}-lifelog-insights.md"


def resolve_targets(args: argparse.Namespace) -> list[Path]:
    if args.all:
        return iter_all_insight_files()
    if args.range:
        return [insight_path_for(today() - dt.timedelta(days=i + 1)) for i in range(args.range)]
    if args.date:
        return [insight_path_for(args.date)]
    return [insight_path_for(today() - dt.timedelta(days=1))]


def collect_existing_insights() -> list[Insight]:
    insights = []
    for path in iter_all_insight_files():
        insight = load_insight(path)
        if insight:
            insights.append(insight)
    return insights


def index_header(title: str, description: str) -> list[str]:
    generated_at = dt.datetime.now().isoformat(timespec="seconds")
    return [
        "---",
        "source: organize_inputs.py",
        "type: input-index",
        "scope: lifelog-insights",
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


def extract_time(line: str) -> str:
    match = re.search(r"\((\d{1,2}:\d{2})\)\s*$", line)
    return match.group(1) if match else "-"


def priority_of(line: str) -> str:
    match = re.search(r"優先度:([^|()\s]+)", line)
    return match.group(1) if match else "-"


def due_of(line: str) -> str:
    match = re.search(r"期限:([^|()\s]+)", line)
    return match.group(1) if match else "-"


def clean_item_text(line: str) -> str:
    text = re.sub(r"^- \[ \]\s*", "", line).strip()
    text = re.sub(r"\s*\|\s*優先度:[^|()]+", "", text)
    text = re.sub(r"\s*\|\s*期限:[^|()]+", "", text)
    text = re.sub(r"\s*\(\d{1,2}:\d{2}\)\s*$", "", text)
    return text.strip()


def source_suffix(insight: Insight) -> str:
    return f"`{workspace_path(insight.organized_path)}`"


def render_todo_index(insights: list[Insight]) -> str:
    lines = index_header(
        "Lifelog TODO Candidates",
        "Limitless由来のTODO候補。日別TODOへ反映する前に重複、完了済み、優先度を確認する。",
    )
    for insight in sorted(insights, key=lambda item: item.date, reverse=True):
        if not insight.action_items:
            continue
        lines.extend([f"## {insight.date}", ""])
        for item in insight.action_items:
            lines.append(
                f"- [ ] {clean_item_text(item)} | time:{extract_time(item)} | priority:{priority_of(item)} | due:{due_of(item)} | source:{source_suffix(insight)}"
            )
        lines.append("")
    return "\n".join(lines)


def render_decisions_index(insights: list[Insight]) -> str:
    lines = index_header(
        "Lifelog Decisions",
        "Limitless由来の決定事項。継続的に重要なものは該当プロジェクトの状態ファイルへ反映する。",
    )
    for insight in sorted(insights, key=lambda item: item.date, reverse=True):
        if not insight.decisions:
            continue
        lines.extend([f"## {insight.date}", ""])
        for item in insight.decisions:
            lines.append(f"- {clean_item_text(item)} | time:{extract_time(item)} | source:{source_suffix(insight)}")
        lines.append("")
    return "\n".join(lines)


def render_people_index(insights: list[Insight]) -> str:
    lines = index_header(
        "Lifelog People and Contacts",
        "Limitless由来の人物・会社・連絡先候補。関係性が継続する場合は個別メモへ昇格する。",
    )
    for insight in sorted(insights, key=lambda item: item.date, reverse=True):
        if not insight.contacts:
            continue
        lines.extend([f"## {insight.date}", ""])
        for item in insight.contacts:
            lines.append(f"- {item} | source:{source_suffix(insight)}")
        lines.append("")
    return "\n".join(lines)


def render_topics_index(insights: list[Insight]) -> str:
    lines = index_header(
        "Lifelog Topics",
        "Limitless由来の調査トピックと事業アイデア。企画化する前に原本と既存プロジェクトを確認する。",
    )
    for insight in sorted(insights, key=lambda item: item.date, reverse=True):
        items = insight.research_topics + insight.business_ideas
        if not items:
            continue
        lines.extend([f"## {insight.date}", ""])
        for item in items:
            lines.append(f"- {item} | source:{source_suffix(insight)}")
        lines.append("")
    return "\n".join(lines)


def rebuild_indexes() -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    insights = collect_existing_insights()
    outputs = {
        "lifelog-todo-candidates.md": render_todo_index(insights),
        "lifelog-decisions.md": render_decisions_index(insights),
        "lifelog-people.md": render_people_index(insights),
        "lifelog-topics.md": render_topics_index(insights),
    }
    for filename, content in outputs.items():
        path = INDEX_DIR / filename
        path.write_text(content + "\n", encoding="utf-8")
        print(f"  Rebuilt index → {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Organize extracted lifelog insights")
    parser.add_argument("date", nargs="?", type=parse_date, help="YYYY-MM-DD (default: yesterday)")
    parser.add_argument("--range", type=int, help="Organize past N days")
    parser.add_argument("--all", action="store_true", help="Organize all extracted lifelog insights")
    parser.add_argument("--force", action="store_true", help="Overwrite existing organized daily files")
    parser.add_argument("--no-index", action="store_true", help="Do not rebuild lifelog indexes")
    args = parser.parse_args()

    targets = resolve_targets(args)
    print(f"=== Organizing {len(targets)} lifelog insight file(s) ===")

    organized_count = 0
    for path in targets:
        if not path.exists():
            print(f"  Missing insight file, skipping: {path}")
            continue
        insight = load_insight(path)
        if not insight:
            print(f"  Not a lifelog insight file, skipping: {path}")
            continue
        if write_organized(insight, args.force):
            organized_count += 1

    if not args.no_index:
        rebuild_indexes()

    print(f"=== Done! {organized_count}/{len(targets)} organized ===")


if __name__ == "__main__":
    main()
