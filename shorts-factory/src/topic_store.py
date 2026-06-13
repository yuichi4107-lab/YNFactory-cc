"""ネタ帳（topics.json）の管理。重複防止と残量管理を担う。

構造:
{
  "backlog": [{"topic": "...", "note": "..."}, ...],
  "used":    [{"topic": "...", "date": "YYYY-MM-DD", "slug": "...", "title": "..."}, ...]
}
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from pathlib import Path

from .config import CONFIG

LOW_STOCK_THRESHOLD = 7


def _load() -> dict:
    if CONFIG.topics_path.exists():
        with open(CONFIG.topics_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"backlog": [], "used": []}


def _save(data: dict) -> None:
    CONFIG.topics_path.parent.mkdir(parents=True, exist_ok=True)
    # Drive同期との競合を避けるため atomic rename で書き込む
    fd, tmp = tempfile.mkstemp(dir=str(CONFIG.topics_path.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONFIG.topics_path)


def next_topic() -> tuple[str | None, int]:
    """backlog 先頭のトピックと残数を返す（取り出しはまだしない）。"""
    data = _load()
    backlog = data.get("backlog", [])
    if not backlog:
        return None, 0
    return backlog[0]["topic"], len(backlog)


def consume_topic(topic: str, slug: str, title: str) -> int:
    """トピックを used へ移動し、残数を返す。"""
    data = _load()
    data["backlog"] = [t for t in data.get("backlog", []) if t.get("topic") != topic]
    data.setdefault("used", []).append(
        {"topic": topic, "date": date.today().isoformat(), "slug": slug, "title": title}
    )
    _save(data)
    return len(data["backlog"])


def recent_titles(n: int = 30) -> list[str]:
    data = _load()
    used = data.get("used", [])
    return [u.get("title") or u.get("topic", "") for u in used[-n:]]


def add_topics(topics: list[str]) -> int:
    data = _load()
    existing = {t.get("topic") for t in data.get("backlog", [])} | {
        u.get("topic") for u in data.get("used", [])
    }
    for t in topics:
        t = t.strip()
        if t and t not in existing:
            data.setdefault("backlog", []).append({"topic": t})
            existing.add(t)
    _save(data)
    return len(data["backlog"])


def backlog_count() -> int:
    return len(_load().get("backlog", []))
