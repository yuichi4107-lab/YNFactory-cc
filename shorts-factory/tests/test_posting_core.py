from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from src.logging_utils import redact_secrets
from src import platform_copy
from src.pipeline import scheduled_difficulty
from src.platforms import poster


def make_item() -> dict:
    return {
        "id": "item-1",
        "title": "title",
        "caption": (
            "AI導入で成果を出すには、ツール名よりも最初に任せる業務を決めることが大事です。"
            "小さく試して、結果を見て、社内に広げる順番を作ります。"
        ),
        "hashtags": ["#AI活用", "#生成AI", "#ChatGPT", "#業務効率化"],
        "video": {"path": "/tmp/final.mp4"},
        "platforms": {
            "x": {"enabled": True, "status": "pending", "url": None, "error": None},
            "youtube": {"enabled": True, "status": "pending", "url": None, "error": None},
            "instagram": {"enabled": False, "status": "pending", "url": None, "error": None},
        },
        "history": [],
    }


class FakeQueue:
    @staticmethod
    def save_item(item):
        return item

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
        with (
            patch.object(poster, "POSTERS", posters),
            patch.object(poster, "_retry_settings", return_value=(0, 0.0)),
        ):
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

        with (
            patch.object(poster, "POSTERS", {"x": x_post, "youtube": yt_post}),
            patch.object(poster, "_retry_settings", return_value=(0, 0.0)),
        ):
            updated = poster.post_item(item, FakeQueue, FakeNotify)
        self.assertEqual(calls, ["youtube"])
        self.assertEqual(updated["status"], "posted")

    def test_auto_retry_only_failed_platforms(self):
        item = make_item()
        calls: list[str] = []
        youtube_attempts = {"count": 0}

        def x_post(_item):
            calls.append("x")
            return "https://x.example/post/1"

        def yt_post(_item):
            calls.append("youtube")
            youtube_attempts["count"] += 1
            if youtube_attempts["count"] == 1:
                raise RuntimeError("temporary upload error")
            return "https://youtube.example/short/1"

        with (
            patch.object(poster, "POSTERS", {"x": x_post, "youtube": yt_post}),
            patch.object(poster, "_retry_settings", return_value=(2, 0.0)),
        ):
            updated = poster.post_item(item, FakeQueue, FakeNotify)

        self.assertEqual(calls, ["x", "youtube", "youtube"])
        self.assertEqual(updated["status"], "posted")
        self.assertEqual(updated["platforms"]["x"]["attempts"], 1)
        self.assertEqual(updated["platforms"]["youtube"]["attempts"], 2)
        self.assertIn("自動再投稿 1/2", FakeNotify.messages[-1])

    def test_platform_copy_is_platform_specific(self):
        item = make_item()
        copies = platform_copy.build_platform_copy_set(item)

        self.assertIn("最初の1業務", copies["x"]["text"])
        self.assertNotIn("utm_source=youtube", copies["x"]["text"])
        self.assertIn("保存して", copies["instagram"]["caption"])
        self.assertIn("プロフィールの無料診断", copies["tiktok"]["caption"])
        self.assertIn("utm_source=youtube", copies["youtube"]["description"])
        self.assertIn("音声・映像はAIで自動生成しています", copies["youtube"]["description"])

    def test_post_x_uses_platform_specific_copy(self):
        item = make_item()

        class FakeProc:
            returncode = 0
            stdout = "Posted: https://x.example/post/1"
            stderr = ""

        with patch.object(poster.subprocess, "run", return_value=FakeProc()) as run:
            url = poster.post_x(item)

        posted_text = run.call_args.args[0][2]
        self.assertEqual(url, "https://x.example/post/1")
        self.assertIn("最初の1業務", posted_text)
        self.assertNotIn("保存して", posted_text)

    def test_scheduled_difficulty_slots(self):
        from datetime import datetime

        self.assertEqual(scheduled_difficulty(datetime(2026, 6, 16, 9, 0)), "beginner")
        self.assertEqual(scheduled_difficulty(datetime(2026, 6, 16, 14, 0)), "intermediate")
        self.assertEqual(scheduled_difficulty(datetime(2026, 6, 16, 19, 0)), "intermediate")


if __name__ == "__main__":
    unittest.main()
