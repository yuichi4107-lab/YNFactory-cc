from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from src.logging_utils import redact_secrets
from src.pipeline import scheduled_difficulty
from src.platforms import poster


def make_item() -> dict:
    return {
        "id": "item-1",
        "title": "title",
        "platforms": {
            "x": {"enabled": True, "status": "pending", "url": None, "error": None},
            "youtube": {"enabled": True, "status": "pending", "url": None, "error": None},
            "instagram": {"enabled": False, "status": "pending", "url": None, "error": None},
        },
        "history": [],
    }


class FakeQueue:
    @staticmethod
    def mark_platform(item, platform, status, url=None, error=None):
        info = item["platforms"][platform]
        info["status"] = status
        if url:
            info["url"] = url
        if status == "posted":
            info["error"] = None
        elif error:
            info["error"] = error
        return item

    @staticmethod
    def transition(item, status, event=None):
        item["status"] = status
        item.setdefault("history", []).append({"event": event or status})
        return item


class FakeNotify:
    messages: list[str] = []

    @classmethod
    def send_message(cls, text):
        cls.messages.append(text)


class PostingCoreTest(unittest.TestCase):
    def setUp(self):
        FakeNotify.messages = []

    def test_redacts_telegram_tokens(self):
        raw = "https://api.telegram.org/bot123456789:ABCdef_012345678901234567890/getUpdates"
        self.assertNotIn("ABCdef", redact_secrets(raw))
        self.assertIn("[REDACTED]", redact_secrets(raw))
        relative = "/bot123456789:ABCdef_012345678901234567890/getUpdates"
        self.assertNotIn("ABCdef", redact_secrets(relative))

    def test_partial_failure_stays_retryable(self):
        item = make_item()
        posters = {
            "x": lambda item: "https://x.example/post/1",
            "youtube": lambda item: (_ for _ in ()).throw(RuntimeError("boom 123456789:ABCdef_012345678901234567890")),
        }
        with patch.object(poster, "POSTERS", posters):
            updated = poster.post_item(item, FakeQueue, FakeNotify)
        self.assertEqual(updated["status"], "partial_failed")
        self.assertEqual(updated["platforms"]["x"]["status"], "posted")
        self.assertEqual(updated["platforms"]["youtube"]["status"], "failed")
        self.assertNotIn("ABCdef", updated["platforms"]["youtube"]["error"])
        self.assertNotIn("ABCdef", FakeNotify.messages[-1])

    def test_retry_skips_already_posted_platforms(self):
        item = make_item()
        item["platforms"]["x"]["status"] = "posted"
        item["platforms"]["x"]["url"] = "https://x.example/post/1"
        calls: list[str] = []

        def x_post(_item):
            calls.append("x")
            return "duplicate"

        def yt_post(_item):
            calls.append("youtube")
            return "https://youtube.example/short/1"

        with patch.object(poster, "POSTERS", {"x": x_post, "youtube": yt_post}):
            updated = poster.post_item(item, FakeQueue, FakeNotify)
        self.assertEqual(calls, ["youtube"])
        self.assertEqual(updated["status"], "posted")

    def test_scheduled_difficulty_slots(self):
        from datetime import datetime

        self.assertEqual(scheduled_difficulty(datetime(2026, 6, 16, 9, 0)), "beginner")
        self.assertEqual(scheduled_difficulty(datetime(2026, 6, 16, 14, 0)), "intermediate")
        self.assertEqual(scheduled_difficulty(datetime(2026, 6, 16, 19, 0)), "intermediate")


if __name__ == "__main__":
    unittest.main()
