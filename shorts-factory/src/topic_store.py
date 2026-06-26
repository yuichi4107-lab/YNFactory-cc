"""ネタ帳（topics.json）の管理。重複防止と残量管理を担う。

構造:
{
  "backlog": [{"topic": "...", "difficulty": "beginner|intermediate", "note": "..."}, ...],
  "used":    [{"topic": "...", "difficulty": "...", "date": "YYYY-MM-DD", "slug": "...", "title": "..."}, ...]
}
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from pathlib import Path

from .config import CONFIG
from .fs_retry import is_transient_io_error, retry_io

LOW_STOCK_THRESHOLD = 7
VALID_DIFFICULTIES = {"beginner", "intermediate"}
TOPICS_CACHE_PATH = CONFIG.runtime_dir / "cache" / "topics.json"


def normalize_difficulty(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().lower()
    if value in VALID_DIFFICULTIES:
        return value
    if value in {"初級", "初心者", "beginner_jp"}:
        return "beginner"
    if value in {"中級", "中級者", "mid", "middle"}:
        return "intermediate"
    return None


def _difficulty(entry: dict) -> str:
    return normalize_difficulty(entry.get("difficulty")) or "beginner"


def _load_once() -> dict:
    if CONFIG.topics_path.exists():
        with open(CONFIG.topics_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _write_cache(data)
        return data
    return {"backlog": [], "used": []}


def _write_cache(data: dict) -> None:
    try:
        TOPICS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TOPICS_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _load_cache_once() -> dict:
    with open(TOPICS_CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load(allow_cache: bool = True) -> dict:
    try:
        return retry_io(_load_once, attempts=8, delay_sec=3.0)
    except OSError as exc:
        if not allow_cache or not is_transient_io_error(exc):
            raise
        if TOPICS_CACHE_PATH.exists():
            return retry_io(_load_cache_once, attempts=3, delay_sec=1.0)
        raise


def _save_once(data: dict) -> None:
    CONFIG.topics_path.parent.mkdir(parents=True, exist_ok=True)
    # Drive同期との競合を避けるため atomic rename で書き込む
    tmp_path: Path | None = None
    fd, tmp = tempfile.mkstemp(dir=str(CONFIG.topics_path.parent), suffix=".tmp")
    tmp_path = Path(tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CONFIG.topics_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def _save(data: dict) -> None:
    retry_io(lambda: _save_once(data), attempts=8, delay_sec=3.0)
    _write_cache(data)


def next_topic(difficulty: str | None = None) -> tuple[str | None, int]:
    """指定難易度のトピックと残数を返す（取り出しはまだしない）。"""
    data = _load()
    backlog = data.get("backlog", [])
    if not backlog:
        return None, 0
    normalized = normalize_difficulty(difficulty)
    if normalized:
        for entry in backlog:
            if _difficulty(entry) == normalized:
                return entry["topic"], backlog_count(normalized)
        return None, 0
    return backlog[0]["topic"], len(backlog)


def consume_topic(topic: str, slug: str, title: str, difficulty: str | None = None) -> int:
    """トピックを used へ移動し、残数を返す。"""
    data = _load(allow_cache=False)
    used = data.setdefault("used", [])
    if any(u.get("slug") == slug for u in used):
        return len(data.get("backlog", []))
    matched = next((t for t in data.get("backlog", []) if t.get("topic") == topic), {})
    if not matched and any(u.get("topic") == topic for u in used):
        return len(data.get("backlog", []))
    topic_difficulty = normalize_difficulty(difficulty) or _difficulty(matched)
    data["backlog"] = [t for t in data.get("backlog", []) if t.get("topic") != topic]
    used.append(
        {
            "topic": topic,
            "difficulty": topic_difficulty,
            "date": date.today().isoformat(),
            "slug": slug,
            "title": title,
        }
    )
    _save(data)
    return len(data["backlog"])


def recent_titles(n: int = 30) -> list[str]:
    try:
        data = _load()
    except OSError as exc:
        if is_transient_io_error(exc):
            return []
        raise
    used = data.get("used", [])
    return [u.get("title") or u.get("topic", "") for u in used[-n:]]


def add_topics(topics: list[str | dict]) -> int:
    data = _load()
    existing = {t.get("topic") for t in data.get("backlog", [])} | {
        u.get("topic") for u in data.get("used", [])
    }
    for item in topics:
        if isinstance(item, dict):
            topic = str(item.get("topic", "")).strip()
            difficulty = normalize_difficulty(item.get("difficulty")) or "beginner"
            entry = {**item, "topic": topic, "difficulty": difficulty}
        else:
            topic = str(item).strip()
            entry = {"topic": topic, "difficulty": "beginner"}
        if topic and topic not in existing:
            data.setdefault("backlog", []).append(entry)
            existing.add(topic)
    _save(data)
    return len(data["backlog"])


def backlog_count(difficulty: str | None = None) -> int:
    backlog = _load().get("backlog", [])
    normalized = normalize_difficulty(difficulty)
    if not normalized:
        return len(backlog)
    return sum(1 for entry in backlog if _difficulty(entry) == normalized)
