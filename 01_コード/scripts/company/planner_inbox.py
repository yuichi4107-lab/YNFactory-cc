#!/usr/bin/env python3
"""完成済みで実装未着手の要件定義（AI共同開発プランナーの出力）を検出する。

/start と /handoff、および ai-planner スキルの3箇所から同じ判定を共有するため、
検出のみを担当し、TODOファイルへの書き込みは行わない。

判定:
  ready_for_nagame … 最終チェック済み かつ 実装未着手（TODOに載せる対象）
  in_progress      … 最終チェック済み だが 実装着手済み
  draft            … 最終チェック未了
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECTS_DIRNAME = "05_プロジェクト"
PLAN_DIRNAME = "01_計画"
REQUIREMENTS_NAME = "REQUIREMENTS.md"
RUN_HISTORY_DIRNAME = "90_実行履歴"
FINAL_CHECK_NAME = "91_final_checked_requirements.md"
ISSUE_CHAPTER_HEADING = "## 14. 争点と統合結果"
PENDING_STATE = "要判断"

DRIVE_ROOT_CANDIDATES = (
    Path.home() / "Library" / "CloudStorage"
    / "GoogleDrive-yuichi4107@gmail.com" / "マイドライブ" / "YNFactory-cc",
    Path("G:/マイドライブ/YNFactory-cc"),
    Path("G:/My Drive/YNFactory-cc"),
)


def detect_git_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        return Path(result.stdout.strip()).resolve()
    except Exception:
        return Path.cwd().resolve()


def find_roots(git_root: Path) -> list[Path]:
    """走査対象の 05_プロジェクト を優先順で返す。

    git ワークツリー本体が主。Drive 側も見るのは、プランナーの default_workspace が
    Drive を指しており、新規プロジェクトが Drive 側に先に現れるため。
    """
    roots: list[Path] = []
    local = git_root / PROJECTS_DIRNAME
    if local.is_dir():
        roots.append(local)
    for candidate in DRIVE_ROOT_CANDIDATES:
        drive = candidate / PROJECTS_DIRNAME
        if drive.is_dir() and drive.resolve() not in {r.resolve() for r in roots}:
            roots.append(drive)
            break
    return roots


def read_pending_decisions(requirements_text: str) -> list[str]:
    """14章の表から、状態が「要判断」の行を抽出する。

    表の形式:
      | 争点ID | 状態 | 統合後の結論 | 立場Aから採った要素 | 立場Bから採った要素 | 要判断の場合の人間への質問 |
    """
    if ISSUE_CHAPTER_HEADING not in requirements_text:
        return []

    chapter = requirements_text.split(ISSUE_CHAPTER_HEADING, 1)[1]
    for line in chapter.splitlines():
        if line.startswith("## "):
            chapter = chapter.split(line, 1)[0]
            break

    pending: list[str] = []
    for line in chapter.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        if set(cells[0]) <= set("-: "):  # 区切り行
            continue
        if cells[1] != PENDING_STATE:
            continue
        question = cells[5] if len(cells) > 5 else ""
        if question in {"", "-"}:
            question = cells[2] if len(cells) > 2 else ""
        pending.append(f"{cells[0]} {question}".strip())
    return pending


def implementation_started(project: Path) -> bool:
    return (project / "docs" / "SRS.md").exists() or (project / "src").is_dir()


def final_check_files(project: Path) -> list[Path]:
    history = project / RUN_HISTORY_DIRNAME
    if not history.is_dir():
        return []
    try:
        return sorted(history.glob(f"*/{FINAL_CHECK_NAME}"))
    except OSError:
        return []


def inspect_project(project: Path, requirements: Path) -> dict:
    try:
        text = requirements.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""

    checks = final_check_files(project)
    if not checks:
        status = "draft"
    elif implementation_started(project):
        status = "in_progress"
    else:
        status = "ready_for_nagame"

    completed_at = ""
    if checks:
        newest = max(check.stat().st_mtime for check in checks)
        completed_at = datetime.fromtimestamp(newest).strftime("%Y-%m-%d")

    return {
        "project_name": project.name,
        "project_path": str(project),
        "requirements_path": str(requirements),
        "plan_dir": str(requirements.parent),
        "completed_at": completed_at,
        "status": status,
        "decisions_pending": read_pending_decisions(text),
    }


def scan(roots: list[Path]) -> list[dict]:
    """2階層固定で走査する。深い再帰はしない（ジャンクション経由でDriveの巨大ツリーを辿るため）。"""
    items: list[dict] = []
    seen: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        try:
            candidates = sorted(root.glob(f"*/{PLAN_DIRNAME}/{REQUIREMENTS_NAME}"))
        except OSError:
            continue
        for requirements in candidates:
            project = requirements.parent.parent
            if project.name in seen:
                continue
            seen.add(project.name)
            try:
                items.append(inspect_project(project, requirements))
            except OSError:
                continue
    return items


def format_text(items: list[dict]) -> str:
    if not items:
        return "完成済みで実装未着手の要件定義はありません。"
    lines = []
    for item in items:
        pending = len(item["decisions_pending"])
        suffix = f" / 要判断{pending}件" if pending else ""
        lines.append(
            f"[{item['status']}] {item['project_name']}"
            f"（完成 {item['completed_at'] or '不明'}{suffix}）\n"
            f"    {item['plan_dir']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="完成済みで実装未着手の要件定義を検出する"
    )
    parser.add_argument("--json", action="store_true", help="JSONで出力")
    parser.add_argument(
        "--status",
        choices=["ready_for_nagame", "in_progress", "draft"],
        help="この状態のものだけを出力",
    )
    parser.add_argument(
        "--root", type=Path, action="append",
        help="走査する 05_プロジェクト を明示指定（複数可）",
    )
    args = parser.parse_args(argv)

    roots = args.root if args.root else find_roots(detect_git_root())
    items = scan(roots)
    if args.status:
        items = [item for item in items if item["status"] == args.status]

    if args.json:
        payload = {
            "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "scanned_roots": [str(root) for root in roots],
            "items": items,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_text(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
