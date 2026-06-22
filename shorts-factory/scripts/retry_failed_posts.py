#!/usr/bin/env python3
"""Retry failed shorts-factory platform posts without duplicating posted media."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from src import queue_lib  # noqa: E402


RETRYABLE_STATUSES = {"failed", "partial_failed"}


def pending_platforms(item: dict) -> list[str]:
    return [
        name
        for name, info in item.get("platforms", {}).items()
        if info.get("enabled") and info.get("status") != "posted" and not info.get("non_retryable")
    ]


def load_targets(item_ids: list[str], include_all: bool) -> list[dict]:
    if item_ids:
        return [queue_lib.load_item(item_id) for item_id in item_ids]
    if include_all:
        return [
            item
            for item in queue_lib.list_items()
            if item.get("status") in RETRYABLE_STATUSES and pending_platforms(item)
        ]
    raise SystemExit("item_id を指定するか --all を付けてください")


def main() -> int:
    ap = argparse.ArgumentParser(description="失敗した投稿先だけを再試行する")
    ap.add_argument("item_ids", nargs="*", help="再試行するqueue item id")
    ap.add_argument("--all", action="store_true", help="failed/partial_failed を全件対象にする")
    ap.add_argument("--execute", action="store_true", help="実際に投稿する。未指定ならdry-run")
    args = ap.parse_args()

    targets = load_targets(args.item_ids, args.all)
    plan = [
        {"id": item["id"], "status": item.get("status"), "platforms": pending_platforms(item)}
        for item in targets
        if pending_platforms(item)
    ]
    print(json.dumps({"execute": args.execute, "targets": plan}, ensure_ascii=False, indent=2))
    if not args.execute:
        return 0

    from src import notify  # noqa: WPS433
    from src.platforms import poster  # noqa: WPS433

    for item in targets:
        if not pending_platforms(item):
            continue
        queue_lib.transition(item, "approved", "失敗媒体の手動再試行")
        updated = poster.post_item(item, queue_lib, notify)
        print(json.dumps({"id": updated["id"], "status": updated["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
