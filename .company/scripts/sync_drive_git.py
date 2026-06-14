#!/usr/bin/env python3
"""Sync selected files between the Drive worktree and the local Git worktree."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_DRIVE_ROOT_CANDIDATES = [
    Path.home()
    / "Library"
    / "CloudStorage"
    / "GoogleDrive-yuichi4107@gmail.com"
    / "マイドライブ"
    / "YNFactory-cc",
    Path("G:/マイドライブ/YNFactory-cc"),
    Path("G:/My Drive/YNFactory-cc"),
]


def run_git(local_root: Path, args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=local_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def detect_local_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return Path(result.stdout.strip()).resolve()


def detect_drive_root(value: str | None) -> Path:
    if value:
        root = Path(value).expanduser()
        if root.exists():
            return root.resolve()
        raise SystemExit(f"Drive root does not exist: {root}")

    env_value = os.environ.get("YNFACTORY_DRIVE_ROOT")
    if env_value:
        root = Path(env_value).expanduser()
        if root.exists():
            return root.resolve()
        raise SystemExit(f"YNFACTORY_DRIVE_ROOT does not exist: {root}")

    for candidate in DEFAULT_DRIVE_ROOT_CANDIDATES:
        if candidate.exists():
            return candidate.resolve()

    raise SystemExit(
        "Drive root not found. Set YNFACTORY_DRIVE_ROOT or pass --drive-root."
    )


def normalized_paths(args: argparse.Namespace, local_root: Path) -> list[Path]:
    paths = [Path(path) for path in args.paths]

    if args.from_last_commit:
        paths.extend(Path(path) for path in run_git(local_root, ["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"]))

    if args.from_last_pull:
        paths.extend(Path(path) for path in run_git(local_root, ["diff", "--name-only", "ORIG_HEAD..HEAD"]))

    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        if path.is_absolute():
            raise SystemExit(f"Use repo-relative paths only: {path}")
        clean = Path(os.path.normpath(str(path)))
        if str(clean) in (".", "") or str(clean).startswith(".."):
            raise SystemExit(f"Invalid path: {path}")
        if ".git" in clean.parts:
            raise SystemExit(f"Refusing to sync .git paths: {path}")
        key = clean.as_posix()
        if key not in seen:
            seen.add(key)
            result.append(clean)

    if not result:
        raise SystemExit("No paths selected. Pass paths or use --from-last-commit/--from-last-pull.")

    return result


def remove_destination(dst: Path, dry_run: bool) -> None:
    if not dst.exists() and not dst.is_symlink():
        return
    print(f"remove: {dst}")
    if dry_run:
        return
    if dst.is_dir() and not dst.is_symlink():
        shutil.rmtree(dst)
    else:
        dst.unlink()


def copy_path(src: Path, dst: Path, dry_run: bool, delete_missing: bool) -> None:
    if not src.exists() and not src.is_symlink():
        if delete_missing:
            remove_destination(dst, dry_run)
            return
        print(f"missing source, skipped: {src}")
        return

    print(f"copy: {src} -> {dst}")
    if dry_run:
        return

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        remove_destination(dst, dry_run=False)

    if src.is_dir() and not src.is_symlink():
        shutil.copytree(
            src,
            dst,
            symlinks=True,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".DS_Store"),
        )
    else:
        shutil.copy2(src, dst, follow_symlinks=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync selected repo-relative paths between Drive and local Git."
    )
    parser.add_argument(
        "direction",
        choices=["drive-to-local", "local-to-drive"],
        help="drive-to-local is used before commit; local-to-drive is used after pull or after local changes.",
    )
    parser.add_argument("paths", nargs="*", help="Repo-relative file or directory paths.")
    parser.add_argument("--drive-root", help="Google Drive YNFactory-cc root.")
    parser.add_argument("--local-root", help="Local Git YNFactory-cc root. Defaults to current Git root.")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without copying.")
    parser.add_argument("--delete-missing", action="store_true", help="Delete destination paths when source paths are missing.")
    parser.add_argument("--from-last-commit", action="store_true", help="Use paths changed in HEAD.")
    parser.add_argument("--from-last-pull", action="store_true", help="Use paths changed by the last pull, based on ORIG_HEAD..HEAD.")
    args = parser.parse_args()

    local_root = Path(args.local_root).expanduser().resolve() if args.local_root else detect_local_root()
    drive_root = detect_drive_root(args.drive_root)

    if not (local_root / ".git").exists():
        raise SystemExit(f"Local root is not a Git worktree: {local_root}")
    if (drive_root / ".git").exists():
        print(
            f"warning: Drive root contains .git; do not run git commands there: {drive_root}",
            file=sys.stderr,
        )
    if local_root == drive_root:
        raise SystemExit("Local root and Drive root must be different directories.")

    paths = normalized_paths(args, local_root)

    if args.direction == "drive-to-local":
        source_root, destination_root = drive_root, local_root
    else:
        source_root, destination_root = local_root, drive_root

    print(f"direction: {args.direction}")
    print(f"local:    {local_root}")
    print(f"drive:    {drive_root}")
    print(f"dry-run:  {args.dry_run}")

    for rel_path in paths:
        copy_path(
            source_root / rel_path,
            destination_root / rel_path,
            dry_run=args.dry_run,
            delete_missing=args.delete_missing,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
