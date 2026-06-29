#!/usr/bin/env python3
"""Post one approved shorts-factory queue item in a separate worker process."""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from src.config import CONFIG  # noqa: E402
from src import notify, queue_lib  # noqa: E402
from src.platforms import poster  # noqa: E402

WORKER_TIMEOUT_SEC = 900


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _lock_path(item_id: str) -> Path:
    lock_dir = CONFIG.runtime_dir / "post_locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    return lock_dir / f"{item_id}.lock"


def _acquire_lock(item_id: str) -> tuple[int | None, Path]:
    path = _lock_path(item_id)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return None, path
    os.write(fd, str(os.getpid()).encode("utf-8"))
    return fd, path


def _finish_worker(item: dict, *, exit_code: int, error: str | None = None) -> None:
    worker = item.setdefault("posting_worker", {})
    worker["completed_at"] = _now()
    worker["exit_code"] = exit_code
    if error:
        worker["error"] = error[:500]
    else:
        worker.pop("error", None)
    queue_lib.save_item(item)


def _timeout_handler(_signum, _frame) -> None:
    raise TimeoutError(f"post worker timed out after {WORKER_TIMEOUT_SEC}s")


def post_one(item_id: str) -> int:
    fd, lock_path = _acquire_lock(item_id)
    if fd is None:
        print(json.dumps({"id": item_id, "skipped": "locked", "lock": str(lock_path)}, ensure_ascii=False))
        return 0

    try:
        if hasattr(signal, "SIGALRM"):
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(WORKER_TIMEOUT_SEC)
        item = queue_lib.load_item(item_id)
        if item.get("status") != "approved":
            _finish_worker(item, exit_code=0)
            print(json.dumps({"id": item_id, "skipped": item.get("status")}, ensure_ascii=False))
            return 0

        updated = poster.post_item(item, queue_lib, notify)
        _finish_worker(updated, exit_code=0)
        print(json.dumps({"id": item_id, "status": updated.get("status")}, ensure_ascii=False))
        return 0
    except Exception as exc:
        try:
            item = queue_lib.load_item(item_id)
            _finish_worker(item, exit_code=1, error=str(exc))
        except Exception:
            pass
        print(json.dumps({"id": item_id, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
        os.close(fd)
        lock_path.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="承認済みショート動画を1件だけ投稿する")
    ap.add_argument("item_id")
    args = ap.parse_args()
    return post_one(args.item_id)


if __name__ == "__main__":
    raise SystemExit(main())
