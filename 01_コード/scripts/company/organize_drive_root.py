#!/usr/bin/env python3
"""Apply the 6-bucket root layout to the Drive-side YNFactory-cc worktree.

The Git worktree was restructured on 2026-08-05 into 01_コード / 02_設定 /
03_成果物 / 04_インプット / 05_プロジェクト / 99_その他 (see CLAUDE.md
「フォルダ構成」). sync_drive_git.py mirrors Drive and Git at identical relative
paths, so the Drive side has to be moved into the same shape. This script does
that, and sweeps the Drive-only junk (screenshots, caches, scratch files) into
99_その他/.

Run it from the local Git worktree. The Drive root is resolved exactly like
sync_drive_git.py: --drive-root, then $YNFACTORY_DRIVE_ROOT, then the per-OS
defaults. Nothing is written without --apply.
"""

from __future__ import annotations

import argparse
import os
import shutil
from datetime import date
from pathlib import Path

from sync_drive_git import detect_drive_root


# Never touched, whatever the rules below say. Git metadata must not move, and
# tool-discovered config has to stay at the root or Claude Code / Codex stop
# finding the skills.
PROTECTED = {
    ".git", ".git_drivebackup", ".git.disabled-20260615",
    ".claude", ".agents", ".codex", ".company",
    "CLAUDE.md", "AGENTS.md", ".gitignore", ".vscode",
}

BUCKETS = ["01_コード", "02_設定", "03_成果物", "04_インプット", "05_プロジェクト", "99_その他"]

# (source, destination directory) — the source is moved *into* the destination.
MOVES: list[tuple[str, str]] = [
    ("scripts", "01_コード"),
    ("docs", "02_設定"),
    ("ebooks", "03_成果物"),
    ("ebook-produce", "03_成果物"),
]

# Directories whose *contents* are moved one by one, then the empty source is
# removed. Used where both sides already exist, or to flatten a wrapper dir.
MERGES: list[tuple[str, str]] = [
    ("_scripts", "01_コード/scripts"),
    (".company/outputs", "03_成果物/outputs"),
    (".company/inputs", "04_インプット/inputs"),
    (".company/context", "04_インプット/context"),
    ("tools", "05_プロジェクト"),
    ("codex/queue", ".company/codex/queue"),
]

# 2026-08-06: the company-org metaphor was dropped, so `.company/` dissolves into
# the buckets. Only `secretary/` and the dashboards stay — their paths are baked
# into the handoff skill, the morning notifier and the task scheduler.
COMPANY_MOVES: list[tuple[str, str]] = [
    (".company/scripts", "01_コード/scripts/company"),
    (".company/requirements", "02_設定/requirements"),
    (".company/engineering/docs", "02_設定/docs/engineering/engineering-docs"),
]
COMPANY_RECORDS = [
    "projects", "pm", "sales", "marketing", "research", "ceo", "automation",
    "services", "engineering", "genspark", "manus", "creative", "editorial",
    "finance", "reviews",
]

# Everything here becomes 05_プロジェクト/<name>/. Includes the three projects
# that exist only on the Drive side (quant-bot, blockcraft-lite,
# multi-ai-sparring).
PROJECTS = [
    "ai-news-system", "ai-trade-system", "biz_idea_generator", "blockcraft-lite",
    "comicle-pipeline", "gourmet-share", "internal-tool-starter-kit",
    "iphone-screenshot-share", "jp-daytrade", "keiba-unified",
    "multi-ai-sparring", "notebooklm-sync", "pdf-annotator", "quant-bot",
    "rakuten-room-auto", "sales-ops", "sengoku-game", "shorts-factory",
    "voice-journal", "voice-recorder", "weather-nagoya-app", "yn-tools",
]

# Drive-only leftovers swept into 99_その他/<date>-cleanup/.
JUNK_FILES = [
    "mobile_full.png", "desktop_full.png", "existing_lp_top.png",
    "geo_mobile_header.png", "geo_mobile_full.png", "geo_desktop_full.png",
    "keiba-dash-light.png", "skills-bundle-20260726.zip",
]
JUNK_GLOBS = [".company/tmp_*.txt"]
JUNK_DIRS = [".company/tmp", "_archive"]

# Regenerable. Archived by default; deleted with --purge-cache.
CACHE_DIRS = [".playwright-mcp", ".pytest_cache", ".wrangler", "test-results",
              "01_コード/scripts/__pycache__", "scripts/__pycache__"]


class Planner:
    """Collects actions first so --dry-run can show the whole plan."""

    def __init__(self, drive_root: Path, junk_root: Path, purge_cache: bool):
        self.drive_root = drive_root
        self.junk_root = junk_root
        self.purge_cache = purge_cache
        self.actions: list[tuple[str, Path, Path | None]] = []
        self.skipped: list[str] = []

    def _resolve(self, rel: str) -> Path:
        clean = Path(os.path.normpath(rel))
        if clean.is_absolute() or str(clean).startswith("..") or str(clean) in (".", ""):
            raise SystemExit(f"Invalid rule path: {rel}")
        if clean.parts[0] in PROTECTED and clean.parts[0] != ".company":
            raise SystemExit(f"Refusing to touch protected path: {rel}")
        return self.drive_root / clean

    def _exists(self, path: Path) -> bool:
        return path.exists() or path.is_symlink()

    def move(self, rel: str, dest_dir: str) -> None:
        src = self._resolve(rel)
        if not self._exists(src):
            self.skipped.append(rel)
            return
        dst = unique(self.drive_root / dest_dir / src.name)
        self.actions.append(("move", src, dst))

    def merge(self, src_rel: str, dst_rel: str) -> None:
        src = self._resolve(src_rel)
        dst = self._resolve(dst_rel)
        if not src.is_dir():
            self.skipped.append(src_rel)
            return
        for child in sorted(src.iterdir()):
            self.actions.append(("merge", child, unique(dst / child.name)))
        self.actions.append(("rmdir", src, None))

    def junk(self, rel: str) -> None:
        src = self._resolve(rel)
        if not self._exists(src):
            self.skipped.append(rel)
            return
        self.actions.append(("junk", src, unique(self.junk_root / flatten(rel))))

    def cache(self, rel: str) -> None:
        src = self._resolve(rel)
        if not self._exists(src):
            self.skipped.append(rel)
            return
        if self.purge_cache:
            self.actions.append(("delete", src, None))
        else:
            self.actions.append(("junk", src, unique(self.junk_root / flatten(rel))))

    def _prune_empty_parents(self, path: Path) -> None:
        """After a merge empties `codex/queue`, drop the leftover `codex/` too."""
        while path != self.drive_root and path.is_dir() and not any(path.iterdir()):
            if path.name in PROTECTED:
                return
            path.rmdir()
            path = path.parent

    def run(self, apply: bool) -> None:
        for kind, src, dst in self.actions:
            rel_src = src.relative_to(self.drive_root)
            # The plan is built against the pre-move tree, so an earlier action
            # may already have consumed this source (e.g. extracting
            # `.company/engineering/docs` can empty and prune `.company/engineering`).
            if apply and not self._exists(src):
                print(f"skip   : {rel_src} (already handled)")
                continue
            if kind == "delete":
                print(f"delete : {rel_src}")
                if apply:
                    remove(src)
                continue
            if kind == "rmdir":
                if any(src.iterdir()):
                    print(f"keep   : {rel_src} (not empty after merge)")
                    continue
                print(f"rmdir  : {rel_src}")
                if apply:
                    src.rmdir()
                    self._prune_empty_parents(src.parent)
                continue

            assert dst is not None
            label = {"move": "move   ", "merge": "merge  ", "junk": "junk   "}[kind]
            print(f"{label}: {rel_src} -> {dst.relative_to(self.drive_root)}")
            if apply:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))


def flatten(rel: str) -> str:
    """`.company/tmp` -> `company-tmp`, so junk lands flat and unhidden."""
    return "-".join(part.lstrip(".") or "dot" for part in Path(rel).parts)


def unique(dst: Path) -> Path:
    """Never overwrite: append -2, -3 ... until the name is free."""
    if not (dst.exists() or dst.is_symlink()):
        return dst
    for index in range(2, 1000):
        candidate = dst.with_name(f"{dst.stem}-{index}{dst.suffix}")
        if not (candidate.exists() or candidate.is_symlink()):
            return candidate
    raise SystemExit(f"Could not find a free name for {dst}")


def remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def build_planner(drive_root: Path, today: str, purge_cache: bool) -> Planner:
    planner = Planner(drive_root, drive_root / "99_その他" / f"{today}-cleanup", purge_cache)

    # Sweep first: the plan is built against the pre-move tree, so a cache like
    # `scripts/__pycache__` has to be dealt with before `scripts/` itself moves.
    for rel in JUNK_FILES + JUNK_DIRS:
        planner.junk(rel)
    for pattern in JUNK_GLOBS:
        for match in sorted(drive_root.glob(pattern)):
            planner.junk(match.relative_to(drive_root).as_posix())
    for rel in CACHE_DIRS:
        planner.cache(rel)

    # Then restructure what remains.
    for rel, dest in MOVES:
        planner.move(rel, dest)
    for name in PROJECTS:
        planner.move(name, "05_プロジェクト")
    for src_rel, dst_rel in MERGES:
        planner.merge(src_rel, dst_rel)

    # Finally dissolve `.company/` — after the merges above have emptied its
    # outputs/inputs/context, so only the org-record folders are left.
    for src_rel, dst_rel in COMPANY_MOVES:
        planner.merge(src_rel, dst_rel)
    for name in COMPANY_RECORDS:
        planner.move(f".company/{name}", "99_その他/company-records")

    return planner


def write_manifest(planner: Planner, today: str) -> Path:
    lines = [
        f"# Drive root restructure {today}", "",
        f"Drive root: `{planner.drive_root}`",
        f"Cache handling: {'deleted (--purge-cache)' if planner.purge_cache else 'moved to 99_その他'}",
        "", "| action | from | to |", "|---|---|---|",
    ]
    for kind, src, dst in planner.actions:
        rel_src = src.relative_to(planner.drive_root).as_posix()
        rel_dst = dst.relative_to(planner.drive_root).as_posix() if dst else "-"
        lines.append(f"| {kind} | `{rel_src}` | `{rel_dst}` |")
    lines.append("")

    planner.junk_root.mkdir(parents=True, exist_ok=True)
    path = planner.junk_root / "MANIFEST.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drive-root", help="Override the Drive worktree path.")
    parser.add_argument("--date", help="Cleanup folder date (default: today).")
    parser.add_argument("--purge-cache", action="store_true",
                        help="Delete regenerable caches instead of keeping them.")
    parser.add_argument("--apply", action="store_true",
                        help="Actually move files. Without this the run is a dry run.")
    args = parser.parse_args()

    drive_root = detect_drive_root(args.drive_root)
    today = args.date or date.today().isoformat()

    if (drive_root / ".git").is_dir():
        print("warning: a real .git directory exists on the Drive side; leaving it untouched.")

    planner = build_planner(drive_root, today, args.purge_cache)

    print(f"drive:       {drive_root}")
    print(f"dry-run:     {not args.apply}")
    print(f"purge-cache: {args.purge_cache}")
    print("")

    if not planner.actions:
        print("nothing to do — the Drive root already matches the bucket layout.")
        return

    if args.apply:
        for bucket in BUCKETS:
            (drive_root / bucket).mkdir(exist_ok=True)

    planner.run(apply=args.apply)

    print("")
    print(f"{len(planner.actions)} action(s); {len(planner.skipped)} rule(s) skipped (already moved or absent).")
    if args.apply:
        print(f"manifest: {write_manifest(planner, today).relative_to(drive_root)}")
    else:
        print("dry-run: nothing was moved. Re-run with --apply to execute.")


if __name__ == "__main__":
    main()
