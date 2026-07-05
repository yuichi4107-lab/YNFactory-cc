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
import re
import tempfile
import unicodedata
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

from .config import CONFIG
from .fs_retry import is_transient_io_error, retry_io, run_with_timeout

LOW_STOCK_THRESHOLD = 7
VALID_DIFFICULTIES = {"beginner", "intermediate"}
TOPICS_CACHE_PATH = CONFIG.runtime_dir / "cache" / "topics.json"
TOPIC_SIMILARITY_THRESHOLD = 0.82
TOPIC_JACCARD_THRESHOLD = 0.74
_TOPIC_NOISE_WORDS = (
    "chatgpt",
    "チャットgpt",
    "チャットジーピーティー",
    "生成ai",
    "ai",
    "方法",
    "術",
    "使い方",
    "活用",
    "させる",
    "させ",
    "して",
    "する",
    "作らせ",
    "作る",
    "作り",
    "変える",
    "できる",
    "ため",
    "まで",
    "から",
)
_TOPIC_SYNONYMS = {
    "型化": "標準化",
    "型を作る": "標準化",
    "型をつくる": "標準化",
    "テンプレ化": "標準化",
    "テンプレート化": "標準化",
    "パターン化": "標準化",
    "仕組み化": "標準化",
    "型": "標準化",
}


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


def normalize_topic_key(topic: str | None) -> str:
    """重複判定用に、言い回しの揺れを落としたキーへ正規化する。"""
    text = unicodedata.normalize("NFKC", str(topic or "")).lower()
    for src, dest in _TOPIC_SYNONYMS.items():
        text = text.replace(src, dest)
    for word in _TOPIC_NOISE_WORDS:
        text = text.replace(word, "")
    text = re.sub(r"[\s\u3000、。・／/｜|（）()［］\[\]「」『』:：,，.!！？?ー\-]+", "", text)
    return text


def _char_grams(text: str, n: int = 2) -> set[str]:
    if len(text) <= n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def _topic_similarity(a: str, b: str) -> float:
    ka = normalize_topic_key(a)
    kb = normalize_topic_key(b)
    if not ka or not kb:
        return 0.0
    if ka == kb:
        return 1.0
    ratio = SequenceMatcher(None, ka, kb).ratio()
    grams_a = _char_grams(ka)
    grams_b = _char_grams(kb)
    jaccard = 0.0
    if grams_a and grams_b:
        jaccard = len(grams_a & grams_b) / len(grams_a | grams_b)
    return max(ratio, jaccard)


def is_duplicate_topic(topic: str | None, existing_topics: list[str]) -> bool:
    return duplicate_topic_match(topic, existing_topics) is not None


def duplicate_topic_match(topic: str | None, existing_topics: list[str]) -> str | None:
    key = normalize_topic_key(topic)
    if not key:
        return None
    for existing in existing_topics:
        existing_key = normalize_topic_key(existing)
        if not existing_key:
            continue
        if key == existing_key:
            return existing
        similarity = _topic_similarity(topic or "", existing)
        if similarity >= TOPIC_SIMILARITY_THRESHOLD:
            return existing
        grams_a = _char_grams(key)
        grams_b = _char_grams(existing_key)
        if grams_a and grams_b:
            jaccard = len(grams_a & grams_b) / len(grams_a | grams_b)
            if jaccard >= TOPIC_JACCARD_THRESHOLD:
                return existing
    return None


def _queue_topic_entries() -> list[dict]:
    if not CONFIG.queue_dir.exists():
        return []
    entries: list[dict] = []
    for path in sorted(CONFIG.queue_dir.glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                item = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        topic = str(item.get("topic") or "").strip()
        title = str(item.get("title") or "").strip()
        if not topic and not title:
            continue
        entries.append(
            {
                "topic": topic,
                "title": title,
                "slug": item.get("id") or path.stem,
                "status": item.get("status"),
                "created_at": item.get("created_at"),
            }
        )
    return entries


def _reserved_topics(data: dict) -> list[str]:
    topics: list[str] = []
    for entry in data.get("used", []):
        topic = str(entry.get("topic") or "").strip()
        title = str(entry.get("title") or "").strip()
        if topic:
            topics.append(topic)
        if title:
            topics.append(title)
    for entry in _queue_topic_entries():
        topic = str(entry.get("topic") or "").strip()
        title = str(entry.get("title") or "").strip()
        if topic:
            topics.append(topic)
        if title:
            topics.append(title)
    deduped: list[str] = []
    seen: set[str] = set()
    for topic in topics:
        key = normalize_topic_key(topic)
        if key and key not in seen:
            seen.add(key)
            deduped.append(topic)
    return deduped


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
        return retry_io(
            lambda: run_with_timeout(
                _load_once,
                timeout_sec=5.0,
                label="read topics.json",
            ),
            attempts=8,
            delay_sec=3.0,
        )
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
    retry_io(
        lambda: run_with_timeout(
            lambda: _save_once(data),
            timeout_sec=8.0,
            label="write topics.json",
        ),
        attempts=8,
        delay_sec=3.0,
    )
    _write_cache(data)


def _public_topic_entry(entry: dict) -> dict:
    copied = dict(entry)
    copied["difficulty"] = _difficulty(copied)
    return copied


def next_topic_entry(difficulty: str | None = None) -> tuple[dict | None, int]:
    """指定難易度のトピックentryと残数を返す（取り出しはまだしない）。"""
    data = _load()
    backlog = data.get("backlog", [])
    if not backlog:
        return None, 0
    normalized = normalize_difficulty(difficulty)
    reserved = _reserved_topics(data)
    if normalized:
        for entry in backlog:
            if _difficulty(entry) == normalized and not is_duplicate_topic(entry.get("topic"), reserved):
                return _public_topic_entry(entry), backlog_count(normalized)
        return None, 0
    for entry in backlog:
        if not is_duplicate_topic(entry.get("topic"), reserved):
            return _public_topic_entry(entry), len(backlog)
    return None, 0


def next_topic(difficulty: str | None = None) -> tuple[str | None, int]:
    """指定難易度のトピック文字列と残数を返す（後方互換API）。"""
    entry, remaining = next_topic_entry(difficulty)
    if not entry:
        return None, remaining
    return entry.get("topic"), remaining


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
    used_entry = {
        "topic": topic,
        "difficulty": topic_difficulty,
        "date": date.today().isoformat(),
        "slug": slug,
        "title": title,
    }
    for key in (
        "domain",
        "business_function",
        "primary_tools",
        "expertise_angle",
        "target_persona",
        "platform_angles",
        "avoid_angles",
    ):
        if key in matched:
            used_entry[key] = matched[key]
    used.append(used_entry)
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
    existing = [t.get("topic") for t in data.get("backlog", [])] + _reserved_topics(data)
    for item in topics:
        if isinstance(item, dict):
            topic = str(item.get("topic", "")).strip()
            difficulty = normalize_difficulty(item.get("difficulty")) or "beginner"
            entry = {**item, "topic": topic, "difficulty": difficulty}
        else:
            topic = str(item).strip()
            entry = {"topic": topic, "difficulty": "beginner"}
        if topic and not is_duplicate_topic(topic, existing):
            data.setdefault("backlog", []).append(entry)
            existing.append(topic)
    _save(data)
    return len(data["backlog"])


def backlog_count(difficulty: str | None = None) -> int:
    backlog = _load().get("backlog", [])
    normalized = normalize_difficulty(difficulty)
    if not normalized:
        return len(backlog)
    return sum(1 for entry in backlog if _difficulty(entry) == normalized)
