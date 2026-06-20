"""投稿キュー（.company/marketing/shorts-factory/queue/）の管理。

social-auto-ops のステータス設計を踏襲:
  draft → ready_for_review → approved → posted / failed / skipped / blocked

Drive同期との競合を避けるため、書き込みは必ず atomic rename で行う。
このMacが単一ライター（他端末からはqueueを書き換えない運用）。
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from .config import CONFIG
from .platform_copy import build_platform_copy_set

STATUSES = {
    "draft",
    "ready_for_review",
    "approved",
    "posted",
    "partial_failed",
    "failed",
    "skipped",
    "blocked",
}


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def queue_path(item_id: str) -> Path:
    return CONFIG.queue_dir / f"{item_id}.json"


def save_item(item: dict) -> Path:
    CONFIG.queue_dir.mkdir(parents=True, exist_ok=True)
    path = queue_path(item["id"])
    fd, tmp = tempfile.mkstemp(dir=str(CONFIG.queue_dir), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(item, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return path


def load_item(item_id: str) -> dict:
    with open(queue_path(item_id), "r", encoding="utf-8") as f:
        return json.load(f)


def list_items(status: str | None = None) -> list[dict]:
    if not CONFIG.queue_dir.exists():
        return []
    items = []
    for p in sorted(CONFIG.queue_dir.glob("*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                item = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if status is None or item.get("status") == status:
            items.append(item)
    return items


def new_item(
    item_id: str,
    topic: str,
    script: dict,
    video_path: Path,
    duration: float,
    size_mb: float,
    quality_report_path: Path,
    quality_pass: bool,
    avg_cer: float,
    output_dir: Path,
) -> dict:
    platforms = {}
    for p in ("x", "youtube", "instagram", "tiktok"):
        platforms[p] = {
            "enabled": p in (CONFIG.get("queue", "platforms", default=["x"]) or []),
            "status": "pending",
            "url": None,
            "error": None,
            "posted_at": None,
            "attempts": 0,
            "last_attempt_at": None,
            "last_retry_at": None,
        }
    item = {
        "id": item_id,
        "created_at": _now(),
        "topic": topic,
        "difficulty": script.get("difficulty", "beginner"),
        "title": script["title"],
        "caption": script["caption"],
        "hashtags": script["hashtags"],
        "video": {
            "path": str(video_path),
            "duration": round(duration, 2),
            "size_mb": round(size_mb, 2),
        },
        "output_dir": str(output_dir),
        "quality": {
            "pass": quality_pass,
            "avg_cer": avg_cer,
            "report_path": str(quality_report_path),
        },
        "status": "draft",
        "review": {"owner_approved": False, "decided_at": None, "via": None},
        "telegram": {"message_id": None},
        "platforms": platforms,
        "history": [{"ts": _now(), "event": "created"}],
    }
    item["platform_copy"] = build_platform_copy_set(item)
    save_item(item)
    return item


def transition(item: dict, status: str, event: str | None = None) -> dict:
    assert status in STATUSES, f"不正なstatus: {status}"
    item["status"] = status
    item.setdefault("history", []).append({"ts": _now(), "event": event or status})
    save_item(item)
    return item


def mark_platform(item: dict, platform: str, status: str, url: str | None = None,
                  error: str | None = None) -> dict:
    p = item["platforms"][platform]
    p["status"] = status
    if url:
        p["url"] = url
    if status == "posted":
        p["error"] = None
    elif error:
        p["error"] = error[:500]
    if status == "posted":
        p["posted_at"] = _now()
    item.setdefault("history", []).append(
        {"ts": _now(), "event": f"{platform}:{status}" + (f" {url}" if url else "")}
    )
    save_item(item)
    return item
