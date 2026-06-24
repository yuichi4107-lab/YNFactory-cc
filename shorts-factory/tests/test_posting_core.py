from __future__ import annotations

import errno
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from src.logging_utils import redact_secrets
from src.fs_retry import retry_io
from src import approval_bot, platform_copy, queue_lib, script_gen
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
            "tiktok": {"enabled": False, "status": "pending", "url": None, "error": None},
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

    def test_retry_override_disables_inner_retries(self):
        item = make_item()
        item["platforms"]["x"]["enabled"] = False
        calls: list[str] = []

        def yt_post(_item):
            calls.append("youtube")
            raise RuntimeError("temporary upload error")

        with patch.object(poster, "POSTERS", {"youtube": yt_post}):
            updated = poster.post_item(
                item,
                FakeQueue,
                FakeNotify,
                retry_attempts=0,
                retry_delay_sec=0,
            )

        self.assertEqual(calls, ["youtube"])
        self.assertEqual(updated["status"], "failed")

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

    def test_instagram_reuses_recent_matching_post(self):
        item = make_item()
        calls = {"post": 0}

        class FakeMeta:
            @staticmethod
            def load_env(_path):
                return {"META_IG_USER_ID": "ig-1", "META_ACCESS_TOKEN": "token"}

            @staticmethod
            def graph_get(_path, _token, _params):
                return {
                    "data": [
                        {
                            "id": "media-1",
                            "permalink": "https://instagram.example/reel/existing",
                            "caption": platform_copy.copy_for_platform(item, "instagram")["caption"],
                            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        }
                    ]
                }

            @staticmethod
            def post_instagram_reels(*_args):
                calls["post"] += 1
                return {"status": "posted", "permalink": "https://instagram.example/reel/new"}

        with patch.object(poster, "_meta_module", return_value=FakeMeta):
            self.assertEqual(
                poster.post_instagram(item),
                "https://instagram.example/reel/existing",
            )
        self.assertEqual(calls["post"], 0)

    def test_instagram_posts_through_direct_meta_api(self):
        item = make_item()
        calls = {"post": 0}

        class FakeMeta:
            @staticmethod
            def load_env(_path):
                return {"META_IG_USER_ID": "ig-1", "META_ACCESS_TOKEN": "token"}

            @staticmethod
            def post_instagram_reels(_caption, _video_path, _env):
                calls["post"] += 1
                return {"status": "posted", "permalink": "https://instagram.example/reel/1"}

        with (
            patch.object(poster, "_find_recent_instagram_post", return_value=None),
            patch.object(poster, "_meta_module", return_value=FakeMeta),
        ):
            self.assertEqual(poster.post_instagram(item), "https://instagram.example/reel/1")
        self.assertEqual(calls["post"], 1)

    def test_tiktok_session_expired_is_not_retried(self):
        item = make_item()
        for platform in item["platforms"].values():
            platform["enabled"] = False
        item["platforms"]["tiktok"]["enabled"] = True
        calls = []

        def tiktok_post(_item):
            calls.append("tiktok")
            raise RuntimeError("TikTokセッション失効。scripts/login_tiktok.sh で専用Chromeに再ログインしてください")

        with (
            patch.object(poster, "POSTERS", {"tiktok": tiktok_post}),
            patch.object(poster, "_retry_settings", return_value=(2, 0.0)),
        ):
            updated = poster.post_item(item, FakeQueue, FakeNotify)

        self.assertEqual(calls, ["tiktok"])
        self.assertEqual(updated["platforms"]["tiktok"]["attempts"], 1)
        self.assertTrue(updated["platforms"]["tiktok"]["non_retryable"])
        self.assertEqual(updated["status"], "failed")

    def test_scheduled_difficulty_slots(self):
        from datetime import datetime

        self.assertEqual(scheduled_difficulty(datetime(2026, 6, 16, 9, 0)), "beginner")
        self.assertEqual(scheduled_difficulty(datetime(2026, 6, 16, 14, 0)), "intermediate")
        self.assertEqual(scheduled_difficulty(datetime(2026, 6, 16, 19, 0)), "intermediate")

    def test_retry_io_retries_resource_deadlock(self):
        calls = []

        def flaky():
            calls.append(1)
            if len(calls) == 1:
                raise OSError(errno.EDEADLK, "Resource deadlock avoided")
            return "ok"

        self.assertEqual(retry_io(flaky, attempts=2, delay_sec=0), "ok")
        self.assertEqual(len(calls), 2)

    def test_script_generation_normalizes_unstable_terms(self):
        data = {
            "cues": [
                {
                    "display": ["PDFをAPIで", "AI確認する"],
                    "tts_text": "PDFをAPIでAI確認します。",
                    "reading_kana": "PDFヲAPIデAIカクニンシマス。",
                }
            ]
        }

        script_gen.normalize_generated_script(data)

        joined = json.dumps(data, ensure_ascii=False)
        self.assertNotIn("PDF", joined)
        self.assertNotIn("API", joined)
        self.assertNotIn("AI確認", joined)
        self.assertIn("ピーディーエフ", joined)
        self.assertIn("エーピーアイ", joined)
        self.assertIn("エーアイ確認", joined)

    def test_generic_fallback_script_is_valid(self):
        data = script_gen._fallback_script("ChatGPTで資料を要約する方法", "beginner", ["err"])
        errs = script_gen.validate_script(data, image_count=4)

        self.assertEqual(errs, [])
        self.assertIn("二案を並べます", data["cues"][4]["display"])

    def test_find_due_scheduled_draft(self):
        now = datetime(2026, 6, 25, 9, 0, tzinfo=timezone(timedelta(hours=9)))
        items = [
            {
                "id": "future",
                "status": "draft",
                "difficulty": "beginner",
                "scheduled_for": "2026-06-25T14:00:00+09:00",
            },
            {
                "id": "due",
                "status": "draft",
                "difficulty": "beginner",
                "scheduled_for": "2026-06-25T09:00:00+09:00",
            },
            {
                "id": "intermediate-due",
                "status": "draft",
                "difficulty": "intermediate",
                "scheduled_for": "2026-06-25T09:00:00+09:00",
            },
        ]

        with patch.object(queue_lib, "list_items", return_value=items):
            self.assertEqual(queue_lib.find_due_scheduled_draft(now, "beginner")["id"], "due")
            self.assertEqual(
                queue_lib.find_due_scheduled_draft(now, "intermediate")["id"],
                "intermediate-due",
            )
            self.assertIsNone(
                queue_lib.find_due_scheduled_draft(now + timedelta(hours=3), "beginner")
            )

    def test_deferred_retry_requires_approval_and_cooldown(self):
        now = datetime(2026, 6, 24, 20, 0, tzinfo=timezone(timedelta(hours=9)))
        item = make_item()
        item["status"] = "partial_failed"
        item["created_at"] = "2026-06-24T19:00:00+09:00"
        item["review"] = {"owner_approved": True}
        item["platforms"]["x"]["status"] = "posted"
        item["platforms"]["instagram"]["enabled"] = True
        item["platforms"]["instagram"]["status"] = "failed"
        item["platforms"]["instagram"]["last_attempt_at"] = "2026-06-24T19:40:00+09:00"

        with patch.object(
            approval_bot,
            "_deferred_retry_settings",
            return_value=(True, 3, 900.0, timedelta(hours=6)),
        ):
            allowed, _reason, platforms = approval_bot._deferred_retry_allowed(item, now)
            self.assertTrue(allowed)
            self.assertEqual(platforms, ["instagram"])

            item["review"]["owner_approved"] = False
            allowed, reason, _platforms = approval_bot._deferred_retry_allowed(item, now)
            self.assertFalse(allowed)
            self.assertEqual(reason, "not_approved")

            item["review"]["owner_approved"] = True
            item["platforms"]["instagram"]["last_attempt_at"] = "2026-06-24T19:50:00+09:00"
            allowed, reason, _platforms = approval_bot._deferred_retry_allowed(item, now)
            self.assertFalse(allowed)
            self.assertEqual(reason, "cooldown")

            item["platforms"]["instagram"]["last_attempt_at"] = "2026-06-24T19:40:00+09:00"
            item["created_at"] = "2026-06-17T09:00:00+09:00"
            allowed, reason, _platforms = approval_bot._deferred_retry_allowed(item, now)
            self.assertFalse(allowed)
            self.assertEqual(reason, "expired")

            item["created_at"] = "2026-06-24T19:00:00+09:00"
            item["platforms"]["instagram"]["last_attempt_at"] = None
            item.pop("deferred_retry", None)
            allowed, reason, _platforms = approval_bot._deferred_retry_allowed(item, now)
            self.assertFalse(allowed)
            self.assertEqual(reason, "missing_attempt_at")


if __name__ == "__main__":
    unittest.main()
