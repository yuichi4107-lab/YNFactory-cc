#!/usr/bin/env python3
"""Safely create the approved macOS links from the local clone to Drive."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "02_設定/config/mac-drive-links.txt"
DEFAULT_DRIVE_ROOT = (
    Path.home()
    / "Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc"
)


def tracked_files(relative: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--", f"{relative}/**", relative],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def manifest_paths() -> list[str]:
    return [
        line.strip()
        for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="create links; default is check only")
    parser.add_argument("--drive-root", type=Path, default=DEFAULT_DRIVE_ROOT)
    args = parser.parse_args()

    errors: list[str] = []
    ready: list[tuple[Path, Path]] = []
    for relative in manifest_paths():
        local = REPO_ROOT / relative
        drive = args.drive_root / relative
        tracked = tracked_files(relative)
        if tracked:
            errors.append(f"BLOCK tracked={len(tracked)}: {relative}")
            continue
        if not drive.is_dir():
            errors.append(f"BLOCK Drive directory missing: {relative}")
            continue
        if local.is_symlink():
            if local.resolve() == drive.resolve():
                print(f"OK existing: {relative}")
            else:
                errors.append(f"BLOCK different symlink: {relative}")
            continue
        if local.exists():
            errors.append(f"BLOCK local path exists: {relative}")
            continue
        ready.append((local, drive))

    for message in errors:
        print(message)
    if errors:
        return 1
    for local, drive in ready:
        if args.apply:
            local.parent.mkdir(parents=True, exist_ok=True)
            local.symlink_to(drive, target_is_directory=True)
            print(f"CREATED: {local.relative_to(REPO_ROOT)}")
        else:
            print(f"READY: {local.relative_to(REPO_ROOT)}")
    if ready and not args.apply:
        print("Check passed. Re-run with --apply to create links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
