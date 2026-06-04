#!/usr/bin/env python3
"""
Run import_drive_inbox.py repeatedly.

Useful when OS-level scheduling is unavailable.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def run_once() -> int:
    result = subprocess.run([sys.executable, str(BASE_DIR / "import_drive_inbox.py")], cwd=str(BASE_DIR))
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Loop input importer")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between imports")
    args = parser.parse_args()
    while True:
        run_once()
        time.sleep(max(args.interval, 30))


if __name__ == "__main__":
    main()
