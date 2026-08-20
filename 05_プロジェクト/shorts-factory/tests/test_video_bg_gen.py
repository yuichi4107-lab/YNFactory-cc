"""Atlas Cloud Seedance 2.0 統合のユニットテスト。

対象:
- コスト計算（estimate_cost）
- 予算判定（is_budget_available: 月次上限・1本あたり上限の両ケース）
- 週5枠判定（is_seedance_slot: 該当5枠 + 非該当ケース）
- 例外メッセージにAPIキーが含まれないこと（ログ・通知への漏洩防止）
- Seedance台本のセリフ注入（inject_tts_line_into_prompt）:
  LLMがvideo_prompt内でセリフを引用符・空白・句読点ごと変形しても、
  後処理でtts_text原文が確実に埋め込まれること
- フォールバック台本が直近動画との重複チェック対象から除外されること

実際のAtlas Cloud API呼び出しは行わない。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from src import pipeline, renderer, script_gen, topview_inventory, video_bg_gen
from src.config import CONFIG


def _fixed_seedance_cue(overrides: dict | None = None) -> dict:
    cue = {
        "video_prompt": (
            "Same 45-year-old Japanese male business professional in a dark navy business suit, "
            "crisp white shirt, dark solid tie, sitting in the same modern Japanese office "
            "meeting room, same bust-up locked-off camera angle, no zoom. "
            "He says in Japanese: {{LINE}}"
        ),
        "tts_text": "実は残業の9割は防げます。",
        "tts_kana": "ジツハザンギョウノキュウワリハフセゲマス。",
        "display": ["残業の9割は", "防げます"],
        "emphasis": True,
    }
    if overrides:
        cue.update(overrides)
    return cue


def _fixed_seedance_data(cue_overrides: dict | None = None) -> dict:
    return {
        "title": "AI活用で残業を減らす3つの技",
        "character_description": script_gen.SEEDANCE_FIXED_CHARACTER_DESCRIPTION,
        "room_description": script_gen.SEEDANCE_FIXED_ROOM_DESCRIPTION,
        "camera_description": script_gen.SEEDANCE_FIXED_CAMERA_DESCRIPTION,
        "cues": [_fixed_seedance_cue(cue_overrides) for _ in range(4)],
        "caption": "A" * 100,
        "hashtags": ["#生成AI", "#AI活用", "#仕事術"],
        "card_keywords": ["見える化", "自動判定", "優先度", "効率化"],
    }


class TopviewInventoryReuseGuardTest(unittest.TestCase):
    """書き出し済み実写素材を最終ショート間で再利用しない。"""

    def test_select_live_clips_returns_only_unused_assets(self):
        clips = [
            {"id": "used", "use_count": 1, "last_used_at": "2026-08-08T01:00:00+09:00"},
            {"id": "new-b", "use_count": 0, "last_used_at": None},
            {"id": "new-a", "use_count": 0, "last_used_at": None},
        ]
        with patch.object(topview_inventory, "validate_inventory", return_value=({}, clips, Path("/tmp/manifest.json"))):
            selected, _ = topview_inventory.select_live_clips({}, count=2)
        self.assertEqual([clip["id"] for clip in selected], ["new-a", "new-b"])

    def test_select_live_clips_uses_today_batch_before_reserve(self):
        clips = [
            {"id": "reserve-a", "use_count": 0, "registered_at": "2026-08-08T04:00:00+09:00"},
            {"id": "today-a", "use_count": 0, "registered_at": "2026-08-09T04:00:00+09:00"},
            {"id": "today-b", "use_count": 0, "registered_at": "2026-08-09T04:00:00+09:00"},
            {"id": "reserve-b", "use_count": 0, "registered_at": "2026-08-08T04:00:00+09:00"},
        ]
        with patch.object(topview_inventory, "validate_inventory", return_value=({}, clips, Path("/tmp/manifest.json"))):
            selected, _ = topview_inventory.select_live_clips({}, count=2)
        self.assertEqual([clip["id"] for clip in selected], ["today-b", "today-a"])

    def test_select_live_clips_stops_when_unused_assets_are_insufficient(self):
        clips = [
            {"id": "used-a", "use_count": 1, "last_used_at": "2026-08-08T01:00:00+09:00"},
            {"id": "unused", "use_count": 0, "last_used_at": None},
            {"id": "used-b", "use_count": 2, "last_used_at": "2026-08-08T02:00:00+09:00"},
        ]
        with patch.object(topview_inventory, "validate_inventory", return_value=({}, clips, Path("/tmp/manifest.json"))):
            with self.assertRaisesRegex(topview_inventory.TopviewInventoryError, "使用済み素材は再利用しません"):
                topview_inventory.select_live_clips({}, count=2)


class TopviewRegisterMergeTest(unittest.TestCase):
    """補充登録で既存クリップの使用履歴を消さない。"""

    class _Config:
        def __init__(self, assets_dir: Path):
            self._assets_dir = assets_dir

        def get(self, *keys, default=None):
            if keys == ("topview", "assets_dir"):
                return str(self._assets_dir)
            if keys == ("topview", "manifest"):
                return str(self._assets_dir / "manifest.json")
            return default

    def _register(self, tmp: Path, names: list[str]) -> dict:
        for name in names:
            (tmp / name).write_bytes(b"stub")
        meta = {"duration_sec": 12.0, "width": 1080, "height": 1920}
        with patch.object(topview_inventory, "_probe_clip", return_value=meta):
            path = topview_inventory.register_files(self._Config(tmp), names)
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def test_replenishment_keeps_use_history_of_existing_clips(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            self._register(tmp, ["old.mp4"])
            manifest_path = tmp / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["clips"][0]["use_count"] = 1
            manifest["clips"][0]["last_used_at"] = "2026-08-08T01:00:00+09:00"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            merged = self._register(tmp, ["new.mp4"])

        by_id = {c["id"]: c for c in merged["clips"]}
        self.assertEqual(set(by_id), {"topview-old", "topview-new"})
        self.assertEqual(by_id["topview-old"]["use_count"], 1)
        self.assertEqual(by_id["topview-old"]["last_used_at"], "2026-08-08T01:00:00+09:00")
        self.assertEqual(by_id["topview-new"]["use_count"], 0)
        self.assertIn("registered_at", by_id["topview-new"])
        self.assertEqual(by_id["topview-new"]["format"], "split_12s_v1")

    def test_reregistering_a_used_clip_does_not_reset_it_to_unused(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            self._register(tmp, ["clip.mp4"])
            manifest_path = tmp / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["clips"][0]["use_count"] = 2
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            merged = self._register(tmp, ["clip.mp4"])

        self.assertEqual(len(merged["clips"]), 1)
        self.assertEqual(merged["clips"][0]["use_count"], 2)


class TopviewTwelveSecondSplitTest(unittest.TestCase):
    """12秒の実写素材1本を、前後の実写区間へ安全に分ける。"""

    def test_offsets_use_start_and_later_part_of_one_twelve_second_clip(self):
        clip = {"id": "split", "duration_sec": 12.0}
        topview = {**CONFIG.cfg["topview"], "second_segment_start_sec": 6.0, "max_live_segment_sec": 5.0}
        with patch.object(CONFIG, "cfg", {**CONFIG.cfg, "topview": topview}):
            self.assertEqual(
                pipeline._topview_split_clip_offsets(clip, [4.0, 3.0, 3.0, 4.0, 3.0, 3.0]),
                [0.0, 6.0],
            )

    def test_offsets_stop_when_two_live_sections_do_not_fit(self):
        clip = {"id": "too-short-for-script", "duration_sec": 12.0}
        with self.assertRaisesRegex(pipeline.TopviewInventoryError, "12秒素材"):
            pipeline._topview_split_clip_offsets(clip, [5.1, 2.0, 2.0, 4.0, 2.0, 2.0])

    def test_renderer_cuts_two_offsets_from_the_same_source(self):
        calls: list[list[str]] = []
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            source = work / "long.mp4"
            cards = [work / "card-a.png", work / "card-b.png"]
            with patch.object(renderer, "_run", side_effect=lambda cmd, *_: calls.append(cmd)):
                renderer.render_hybrid_background(
                    [source, source], cards, [5.0, 4.0, 6.0, 5.0], work,
                    live_start_offsets=[0.0, 12.0],
                )

        live_calls = [cmd for cmd in calls if "-ss" in cmd]
        self.assertEqual(len(live_calls), 2)
        self.assertEqual([cmd[cmd.index("-ss") + 1] for cmd in live_calls], ["0.000", "12.000"])
        self.assertTrue(all("-stream_loop" not in cmd for cmd in live_calls))

    def test_renderer_keeps_four_cards_between_twelve_second_clip_parts(self):
        calls: list[list[str]] = []
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            source = work / "split.mp4"
            cards = [work / f"card-{i}.png" for i in range(4)]
            with patch.object(renderer, "_run", side_effect=lambda cmd, *_: calls.append(cmd)):
                renderer.render_hybrid_background(
                    [source, source], cards, [4.0, 2.0, 2.0, 4.0, 2.0, 2.0], work,
                    live_start_offsets=[0.0, 6.0],
                )

        live_calls = [cmd for cmd in calls if "-ss" in cmd]
        self.assertEqual(len(live_calls), 2)
        self.assertEqual([cmd[cmd.index("-ss") + 1] for cmd in live_calls], ["0.000", "6.000"])


class VideoBgGenCostTest(unittest.TestCase):
    """コスト計算・予算判定・コストログのテスト。"""

    def setUp(self):
        self._runtime_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._runtime_tmp.cleanup)
        logs_patch = patch.object(CONFIG, "logs_dir", Path(self._runtime_tmp.name))
        logs_patch.start()
        self.addCleanup(logs_patch.stop)

    def test_estimate_cost_fast_model(self):
        # fast: $0.09/s
        self.assertAlmostEqual(video_bg_gen.estimate_cost(10, "fast"), 0.9)
        self.assertAlmostEqual(video_bg_gen.estimate_cost(40, "fast"), 3.6)

    def test_estimate_cost_std_model(self):
        # std: $0.112/s
        self.assertAlmostEqual(video_bg_gen.estimate_cost(10, "std"), 1.12)

    def test_estimate_cost_uses_config_default_model(self):
        with patch.object(CONFIG, "cfg", {**CONFIG.cfg, "seedance": {**CONFIG.cfg["seedance"], "model": "fast"}}):
            self.assertAlmostEqual(video_bg_gen.estimate_cost(10), 0.9)

    def test_monthly_cost_total_sums_only_successful_records(self):
        month = video_bg_gen.month_key()
        video_bg_gen.record_cost(
            video_bg_gen.GenerationCostRecord(
                video_id="v1", cut_count=4, total_duration_sec=40, model="fast",
                unit_price_per_sec=0.09, cost_usd=3.6, success=True,
                timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
            )
        )
        video_bg_gen.record_cost(
            video_bg_gen.GenerationCostRecord(
                video_id="v2", cut_count=1, total_duration_sec=0, model="fast",
                unit_price_per_sec=0.09, cost_usd=0.0, success=False,
                timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
                detail="filter_blocked",
            )
        )
        self.assertAlmostEqual(video_bg_gen.monthly_cost_total(month), 3.6)

    def test_budget_available_within_monthly_limit(self):
        # monthly_budget_usd既定130、消費済み$100 → 残$30。1本$3.6は通る
        video_bg_gen.record_cost(
            video_bg_gen.GenerationCostRecord(
                video_id="v1", cut_count=4, total_duration_sec=1111, model="fast",
                unit_price_per_sec=0.09, cost_usd=100.0, success=True,
                timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
            )
        )
        self.assertTrue(video_bg_gen.is_budget_available(3.6))

    def test_budget_unavailable_when_monthly_limit_exceeded(self):
        # 消費済み$100、残り$30に対して$35は超過 → False
        video_bg_gen.record_cost(
            video_bg_gen.GenerationCostRecord(
                video_id="v1", cut_count=4, total_duration_sec=1111, model="fast",
                unit_price_per_sec=0.09, cost_usd=100.0, success=True,
                timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
            )
        )
        self.assertFalse(video_bg_gen.is_budget_available(35))

    def test_budget_unavailable_when_per_video_limit_exceeded(self):
        # max_cost_per_video_usd既定$10を超える単発コストは、月次残高に余裕があってもFalse
        self.assertFalse(video_bg_gen.is_budget_available(15))

    def test_cost_log_is_reconstructable_from_file(self):
        video_bg_gen.record_cost(
            video_bg_gen.GenerationCostRecord(
                video_id="v1", cut_count=4, total_duration_sec=40, model="fast",
                unit_price_per_sec=0.09, cost_usd=3.6, success=True,
                timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
            )
        )
        lines = video_bg_gen.cost_log_path().read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["video_id"], "v1")
        self.assertEqual(record["cost_usd"], 3.6)
        self.assertTrue(record["success"])


class SeedanceSlotTest(unittest.TestCase):
    """毎日3枠の混在形式判定（曜日-時マッチ）のテスト。"""

    def test_all_daily_scheduled_slots_are_hybrid_seedance(self):
        cases = [
            (datetime(2026, 7, 6 + weekday, hour, 0), f"{code}-{hour:02d}")
            for weekday, code in enumerate(("mon", "tue", "wed", "thu", "fri", "sat", "sun"))
            for hour in (9, 14, 19)
        ]
        seedance = {**CONFIG.cfg["seedance"], "enabled": True}
        with patch.object(CONFIG, "cfg", {**CONFIG.cfg, "seedance": seedance}):
            for dt, slot_code in cases:
                with self.subTest(slot_code=slot_code):
                    self.assertTrue(pipeline.is_seedance_slot(dt))
                    self.assertTrue(pipeline.is_hybrid_seedance_slot(dt))

    def test_slot_matches_by_hour_regardless_of_minute(self):
        # 分は見ない: 09:00〜09:59台であれば発火する
        seedance = {**CONFIG.cfg["seedance"], "enabled": True}
        with patch.object(CONFIG, "cfg", {**CONFIG.cfg, "seedance": seedance}):
            self.assertTrue(pipeline.is_seedance_slot(datetime(2026, 7, 6, 9, 59)))
            self.assertTrue(pipeline.is_seedance_slot(datetime(2026, 7, 6, 9, 1)))

    def test_non_configured_hour_does_not_match(self):
        # 定刻外の10時は対象外
        seedance = {**CONFIG.cfg["seedance"], "enabled": True}
        with patch.object(CONFIG, "cfg", {**CONFIG.cfg, "seedance": seedance}):
            self.assertFalse(pipeline.is_seedance_slot(datetime(2026, 7, 6, 10, 0)))
            self.assertFalse(pipeline.is_hybrid_seedance_slot(datetime(2026, 7, 6, 10, 0)))

    def test_disabled_returns_false_even_in_slot(self):
        with patch.object(
            CONFIG, "cfg", {**CONFIG.cfg, "seedance": {**CONFIG.cfg["seedance"], "enabled": False}}
        ):
            self.assertFalse(pipeline.is_seedance_slot(datetime(2026, 7, 6, 9, 0)))

    def test_topview_covers_all_daily_slots_when_enabled(self):
        topview = {**CONFIG.cfg["topview"], "enabled": True}
        with patch.object(CONFIG, "cfg", {**CONFIG.cfg, "topview": topview}):
            for weekday in range(7):
                for hour in (9, 14, 19):
                    with self.subTest(weekday=weekday, hour=hour):
                        self.assertTrue(pipeline.is_topview_slot(datetime(2026, 7, 6 + weekday, hour, 0)))

    def test_hybrid_segment_durations_follow_tts_boundaries(self):
        cues = [{"start": start} for start in (0.0, 5.2, 10.0, 15.6)]
        self.assertEqual(pipeline._hybrid_segment_durations(cues, 21.0), [5.2, 4.8, 5.6, 5.4])

    def test_topview_segment_durations_follow_six_tts_boundaries(self):
        cues = [{"start": start} for start in (0.0, 4.0, 7.0, 10.0, 14.0, 17.0)]
        self.assertEqual(pipeline._topview_segment_durations(cues, 20.0), [4.0, 3.0, 3.0, 4.0, 3.0, 3.0])


class SeedanceSecretRedactionTest(unittest.TestCase):
    """例外・エラーメッセージにAPIキーが平文で残らないことのテスト。"""

    def setUp(self):
        self._saved_env = os.environ.pop("ATLAS_CLOUD_API_KEY", None)
        self._saved_secret = CONFIG.secrets.get("atlas_cloud")

    def tearDown(self):
        if self._saved_env:
            os.environ["ATLAS_CLOUD_API_KEY"] = self._saved_env
        if self._saved_secret is not None:
            CONFIG.secrets["atlas_cloud"] = self._saved_secret

    def test_config_error_message_has_no_key_and_does_not_leak_when_key_missing(self):
        CONFIG.secrets["atlas_cloud"] = {"api_key": ""}
        with self.assertRaises(video_bg_gen.SeedanceConfigError) as ctx:
            video_bg_gen._api_key()
        # メッセージ自体にAPIキーの値が含まれないこと（そもそも未設定なので当然だが、
        # 設定案内の文言だけであることを明示的に確認する）
        self.assertNotIn("apikey-", str(ctx.exception))

    def test_http_error_message_redacts_api_key_from_body(self):
        fake_key = "apikey-secret1234567890"
        os.environ["ATLAS_CLOUD_API_KEY"] = fake_key
        try:
            with patch("urllib.request.urlopen") as mock_urlopen:
                import urllib.error

                mock_urlopen.side_effect = urllib.error.HTTPError(
                    url="https://api.atlascloud.ai/api/v1/model/generateVideo",
                    code=401,
                    msg="Unauthorized",
                    hdrs=None,
                    fp=__import__("io").BytesIO(
                        f"invalid key: {fake_key}".encode("utf-8")
                    ),
                )
                with self.assertRaises(video_bg_gen.SeedanceAPIError) as ctx:
                    video_bg_gen._http_json(
                        "POST", "https://api.atlascloud.ai/api/v1/model/generateVideo", fake_key, {}
                    )
                self.assertNotIn(fake_key, str(ctx.exception))
                self.assertIn("[REDACTED]", str(ctx.exception))
        finally:
            os.environ.pop("ATLAS_CLOUD_API_KEY", None)


class SeedanceLineInjectionTest(unittest.TestCase):
    """video_prompt内のセリフ注入（inject_tts_line_into_prompt）のテスト。

    実E2Eで判明した不具合1: LLMがvideo_prompt内に直接セリフを書くと、
    引用符・空白・句読点をわずかに変形するため tts_text との完全一致検証が
    構造的に通らなかった。修正後は `{{LINE}}` プレースホルダーを機械的に
    置換する方式にし、完全一致検証自体を撤廃した。

    オーナーフィードバック対応: Seedanceにtts_text（漢字仮名交じり）を
    そのまま読ませると音読み/訓読みの誤読が発生するため、注入対象を
    tts_kana（カタカナ読み）に変更した。VOICEVOX版の
    「読み上げはカタカナ読み仮名・テロップは漢字表記」分離方式と同じ発想。
    """

    def test_placeholder_is_replaced_with_tts_kana_verbatim(self):
        kana = "ジツハザンギョウノキュウワリハフセゲマス。"
        prompt = "A woman talks to the camera. She says in Japanese: {{LINE}}"
        result = script_gen.inject_tts_line_into_prompt(prompt, kana)
        self.assertIn(kana, result)
        self.assertNotIn("{{LINE}}", result)

    def test_llm_variant_line_without_placeholder_still_gets_verbatim_kana_appended(self):
        # LLMがプレースホルダーを書き忘れ、独自にセリフっぽい文字列を書いた場合でも、
        # tts_kana原文が確実に（変形されずに）含まれるプロンプトになること。
        kana = "ヒトツメハタスクノミエルカデス。"
        prompt = (
            'A woman talks to the camera. She says in Japanese: "1つ目はタスクの見える化です"'
            "  (without trailing punctuation, slightly reworded)"
        )
        result = script_gen.inject_tts_line_into_prompt(prompt, kana)
        self.assertIn(kana, result)

    def test_injection_is_idempotent_in_shape_for_multiple_cues(self):
        # 複数cueそれぞれで独立して注入されること（他cueのセリフが混入しない）
        prompt1 = "Cut 1 prompt. {{LINE}}"
        prompt2 = "Cut 2 prompt. {{LINE}}"
        r1 = script_gen.inject_tts_line_into_prompt(prompt1, "セリフイチ")
        r2 = script_gen.inject_tts_line_into_prompt(prompt2, "セリフニ")
        self.assertIn("セリフイチ", r1)
        self.assertNotIn("セリフニ", r1)
        self.assertIn("セリフニ", r2)
        self.assertNotIn("セリフイチ", r2)

    def test_apply_line_injection_uses_tts_kana_not_tts_text(self):
        # 注入されるのは漢字のtts_textではなく、カタカナのtts_kanaであること
        # （オーナーフィードバック対応の核心: 誤読防止のため発話はカナ限定にする）。
        data = {
            "cues": [
                {
                    "video_prompt": "Cut A. {{LINE}}",
                    "tts_text": "上手にできました",
                    "tts_kana": "ジョウズニデキマシタ",
                },
                {
                    "video_prompt": "Cut B. {{LINE}}",
                    "tts_text": "一昨日確認しました",
                    "tts_kana": "オトトイカクニンシマシタ",
                },
            ]
        }
        result = script_gen._apply_line_injection(data)
        self.assertIn("ジョウズニデキマシタ", result["cues"][0]["video_prompt"])
        self.assertNotIn("上手にできました", result["cues"][0]["video_prompt"])
        self.assertIn("オトトイカクニンシマシタ", result["cues"][1]["video_prompt"])
        self.assertNotIn("一昨日確認しました", result["cues"][1]["video_prompt"])
        self.assertNotIn("{{LINE}}", result["cues"][0]["video_prompt"])
        self.assertNotIn("{{LINE}}", result["cues"][1]["video_prompt"])

    def test_apply_line_injection_falls_back_to_tts_text_when_kana_missing(self):
        # tts_kanaが異常に欠落しているデータでも、注入自体はスキップせず
        # tts_textにフォールバックする（validate側で別途tts_kana必須エラーを出す）。
        data = {
            "cues": [
                {"video_prompt": "Cut A. {{LINE}}", "tts_text": "台本セリフA", "tts_kana": ""},
            ]
        }
        result = script_gen._apply_line_injection(data)
        self.assertIn("台本セリフA", result["cues"][0]["video_prompt"])

    def test_validate_seedance_script_no_longer_requires_exact_line_match(self):
        # 完全一致検証を撤廃したことの回帰防止: video_prompt内にセリフの
        # 文字列がそのまま含まれていなくても（{{LINE}}未置換の生データでも）
        # バリデーションはvideo_prompt/tts_text/tts_kana自体の妥当性だけを見て合格にする。
        data = _fixed_seedance_data()
        errs = script_gen.validate_seedance_script(data, 4)
        self.assertEqual(errs, [])

    def test_validate_seedance_script_rejects_female_or_non_fixed_identity(self):
        data = _fixed_seedance_data(
            {
                "video_prompt": "A young Japanese woman in a beige sweater talks to the camera. {{LINE}}",
            }
        )
        data["character_description"] = "A cheerful Japanese woman in her mid-20s wearing a beige sweater"
        data["room_description"] = "a bright modern Japanese apartment room"
        data["camera_description"] = "front-facing upper-body framing"
        errs = script_gen.validate_seedance_script(data, 4)
        self.assertTrue(any("女性" in e or "45-year-old male" in e for e in errs))


class SeedanceKanaValidationTest(unittest.TestCase):
    """tts_kana必須化・読み整合検証のテスト（オーナーフィードバック対応）。"""

    def _base_data(self, cue_overrides: dict) -> dict:
        return _fixed_seedance_data(cue_overrides)

    def test_missing_tts_kana_is_rejected(self):
        data = self._base_data({"tts_kana": ""})
        errs = script_gen.validate_seedance_script(data, 4)
        self.assertTrue(any("tts_kana" in e and ("空" in e or "短すぎる" in e) for e in errs))

    def test_tts_kana_key_absent_is_rejected(self):
        data = self._base_data({})
        del data["cues"][0]["tts_kana"]
        errs = script_gen.validate_seedance_script(data, 4)
        self.assertTrue(any("tts_kana" in e for e in errs))

    def test_tts_kana_with_kanji_is_rejected(self):
        # tts_kanaに漢字が混じっている（カタカナのみでない）場合は不合格
        data = self._base_data({"tts_kana": "実はザンギョウノキュウワリハフセゲマス。"})
        errs = script_gen.validate_seedance_script(data, 4)
        self.assertTrue(any("非カタカナ文字" in e for e in errs))

    def test_tts_kana_with_latin_letters_is_rejected(self):
        # 英字混入も非カタカナとして不合格（読み仮名は全てカタカナが原則）
        data = self._base_data({"tts_kana": "ChatGPTヲツカイマス"})
        errs = script_gen.validate_seedance_script(data, 4)
        self.assertTrue(any("非カタカナ文字" in e for e in errs))

    def test_tts_kana_mismatched_reading_is_rejected(self):
        # tts_textと全く関係ない読みのtts_kanaは、音韻CERが大きく不合格になる
        data = self._base_data(
            {
                "tts_text": "実は残業の9割は防げます。",
                "tts_kana": "コンニチハセカイ",
            }
        )
        errs = script_gen.validate_seedance_script(data, 4)
        self.assertTrue(any("読みが一致しない" in e for e in errs))

    def test_tts_kana_matching_reading_passes(self):
        data = self._base_data(
            {
                "tts_text": "ChatGPTに日本語で頼むだけです。",
                "tts_kana": "チャットジーピーティーニニホンゴデタノムダケデス。",
            }
        )
        errs = script_gen.validate_seedance_script(data, 4)
        self.assertEqual(errs, [])

    def test_tts_kana_reading_with_numbers_passes(self):
        # 数字の読み（3分→サンプン等）が一致していれば合格すること
        data = self._base_data(
            {
                "tts_text": "1つ目はタスクの見える化です。",
                "tts_kana": "ヒトツメハタスクノミエルカデス。",
            }
        )
        errs = script_gen.validate_seedance_script(data, 4)
        self.assertEqual(errs, [])


class SeedanceFallbackScriptTest(unittest.TestCase):
    """フォールバック台本のセリフ注入・重複チェック除外・kana整合のテスト。"""

    def test_fallback_script_has_no_unresolved_placeholder(self):
        data = script_gen._fallback_seedance_script("AI導入の始め方", "beginner", ["test error"])
        for cue in data["cues"]:
            self.assertNotIn("{{LINE}}", cue["video_prompt"])
            # 注入されるのはtts_kana（カタカナ読み）であること
            self.assertIn(cue["tts_kana"], cue["video_prompt"])

    def test_fallback_script_passes_validation(self):
        data = script_gen._fallback_seedance_script("AI導入の始め方", "beginner", ["test error"])
        errs = script_gen.validate_seedance_script(data, 4)
        self.assertEqual(errs, [])

    def test_normalize_generated_script_expands_ambiguous_tts_abbreviation(self):
        data = _fixed_seedance_data(
            {
                "tts_text": "コミュ力を面接で見極めます。",
                "tts_kana": "コミュリョクヲメンセツデミキワメマス。",
            }
        )
        normalized = script_gen.normalize_generated_script(data)
        self.assertEqual(normalized["cues"][0]["tts_text"], "コミュニケーション力を面接で見極めます。")
        self.assertEqual(normalized["cues"][0]["tts_kana"], "コミュニケーションリョクヲメンセツデミキワメマス。")

    def test_fallback_script_tts_kana_is_katakana_only(self):
        data = script_gen._fallback_seedance_script("AI導入の始め方", "beginner", ["test error"])
        for cue in data["cues"]:
            self.assertRegex(cue["tts_kana"], r"^[ァ-ヶー、。・\s０-９0-9？?！!]+$")

    def test_fallback_script_tts_kana_matches_tts_text_reading(self):
        # フォールバック台本のtts_kanaが、実際にtts_textの読みとして
        # 音韻的に妥当であること（validate_seedance_scriptの読み整合チェックを
        # 直接通すことで確認する）。
        data = script_gen._fallback_seedance_script("AI導入の始め方", "beginner", ["test error"])
        for cue in data["cues"]:
            mismatch = script_gen.phonetic_cer(cue["tts_text"], cue["tts_kana"])
            self.assertLessEqual(mismatch, script_gen.SEEDANCE_KANA_MISMATCH_CER_MAX)

    def test_six_cue_fallback_shortens_a_long_topic_title(self):
        topic = "Claude・Make・Zapierで提案書の弱点を抽出し、反論対策まで整える方法"
        data = script_gen._fallback_seedance_script(topic, "intermediate", ["test error"], cut_count=6)
        self.assertEqual(len(data["cues"]), 6)
        self.assertEqual(script_gen.validate_seedance_script(data, 6), [])

    def test_six_cue_fallback_keeps_live_sections_within_topview_limit(self):
        data = script_gen._fallback_seedance_script(
            "ChatGPTで音声メモを箇条書きの作業メモにする方法",
            "beginner",
            ["test error"],
            cut_count=6,
        )
        maximum = int(CONFIG.get("topview", "max_live_tts_kana_chars", default=35))
        for cue_index in script_gen.TOPVIEW_LIVE_CUE_INDICES:
            kana = data["cues"][cue_index]["tts_kana"]
            self.assertLessEqual(len(kana.replace(" ", "")), maximum)

    def test_generate_seedance_script_falls_back_without_duplicate_check_blocking_it(self):
        # 実E2Eで発覚した不具合の回帰防止: LLM呼び出しが常に失敗する状況でも、
        # フォールバック台本が「過去動画と同一」判定に引っかかって
        # RuntimeErrorにならず、必ず有効な台本を返すこと。
        # recent_duplicate_errorsがフォールバック台本にも過去動画ヒットを
        # 返すよう強制した上で、それでも例外にならないことを確認する。
        with (
            patch.object(
                script_gen, "_call_claude_cli",
                side_effect=RuntimeError("claude CLI failed rc=1: mocked"),
            ),
            patch.object(
                script_gen, "recent_duplicate_errors",
                return_value=["title「x」は最近使用済み"],
            ),
        ):
            data = script_gen.generate_seedance_script("AI導入の始め方", "beginner", 4)
        self.assertTrue(data.get("is_fallback"))
        for cue in data["cues"]:
            self.assertNotIn("{{LINE}}", cue["video_prompt"])


class SubtitleStyleTest(unittest.TestCase):
    """テロップ色の統一テスト。"""

    def test_emphasis_style_uses_same_white_color_as_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "subs.ass"
            renderer.make_ass(
                [
                    {"start": 0.0, "end": 1.0, "display": ["強調"], "emphasis": True},
                    {"start": 1.0, "end": 2.0, "display": ["通常"], "emphasis": False},
                ],
                2.0,
                out,
            )
            ass = out.read_text(encoding="utf-8")
        self.assertIn("Style: Default", ass)
        self.assertIn("Style: Emphasis", ass)
        emphasis_line = next(line for line in ass.splitlines() if line.startswith("Style: Emphasis"))
        self.assertIn("&H00FFFFFF", emphasis_line)
        self.assertNotIn("&H0000E6FF", emphasis_line)


class SeedanceVoicevoxAudioModeTest(unittest.TestCase):
    """Seedance映像 + VOICEVOX音声差し替えのテスト。"""

    def test_seedance_voicevox_cues_use_tts_kana_as_reading_kana(self):
        script = {
            "cues": [
                {
                    "tts_text": "ChatGPTに日本語で頼むだけです。",
                    "tts_kana": "チャットジーピーティーニニホンゴデタノムダケデス。",
                    "display": ["ChatGPTに頼む"],
                }
            ]
        }
        cues = pipeline._seedance_voicevox_cues(script)
        self.assertEqual(cues[0]["reading_kana"], "チャットジーピーティーニニホンゴデタノムダケデス。")
        self.assertEqual(cues[0]["tts_text"], "ChatGPTに日本語で頼むだけです。")

    def test_seedance_audio_mode_defaults_to_voicevox_for_unknown_values(self):
        with patch.object(CONFIG, "cfg", {**CONFIG.cfg, "seedance": {**CONFIG.cfg["seedance"], "audio_mode": "bad"}}):
            self.assertEqual(pipeline._seedance_audio_mode(), "voicevox")


class ProduceSeedanceIntegrationTest(unittest.TestCase):
    """pipeline.produce()のSeedance分岐が実行時刻・実API呼び出しから

    安全に切り離されていることのテスト。

    実E2Eで判明した不具合: 既存の静止画版フローだけを検証しているつもりの
    テストが、実行環境のconfig.yaml（seedance.slots）次第で実行時刻に
    偶然マッチし、意図せずclaude CLI経由の実LLM呼び出し・Atlas Cloud実API
    呼び出しへ進んでしまうことがあった。is_seedance_slot() を明示的に
    モックしない限り、produce() のテストは現在時刻に依存してはならない。
    """

    def test_is_seedance_slot_false_skips_seedance_path_entirely(self):
        # is_seedance_slotがFalseなら、Seedance関連関数は一切呼ばれないこと。
        from src import pipeline

        called = {"seedance": False}

        def fail_if_called(*a, **kw):
            called["seedance"] = True
            raise AssertionError("Seedance候補生成が呼ばれてはいけない")

        fake_report = {"pass": True, "accuracy": {"avg_cer": 0.01}, "duration": 30, "size_mb": 5, "checks": []}
        fake_candidate = {
            "item_id": "fake-id", "out_dir": Path("/tmp/fake"), "report": fake_report,
            "title": "fake title", "topic": "fake topic",
            "script": {"title": "fake title", "caption": "x" * 70, "hashtags": ["#a", "#b", "#c"], "target_platform": "common"},
        }

        with (
            patch.object(pipeline, "is_seedance_slot", return_value=False),
            patch.object(pipeline, "_generate_passable_seedance_candidate", side_effect=fail_if_called),
            patch.object(pipeline, "_generate_passable_candidate", return_value=(fake_candidate, 0)),
            patch.object(pipeline, "_select_topic_entry", return_value={"topic": "fake topic"}),
            patch.object(pipeline.topic_store, "normalize_difficulty", return_value="beginner"),
        ):
            result = pipeline.produce(topic="fake topic", send_queue=False, target_platform="common")

        self.assertFalse(called["seedance"])
        self.assertEqual(result["id"], "fake-id")


class ProduceTopviewRouteTest(unittest.TestCase):
    """Topview枠はAtlas/旧カード生成へ絶対にフォールバックしない。"""

    @staticmethod
    def _candidate() -> dict:
        report = {"pass": True, "accuracy": {"avg_cer": 0.01}, "duration": 30, "size_mb": 5, "checks": []}
        return {
            "item_id": "topview-id", "out_dir": Path("/tmp/topview"), "report": report,
            "title": "topview title", "topic": "fake topic",
            "script": {"title": "topview title", "caption": "x" * 70, "hashtags": ["#a", "#b", "#c"], "target_platform": "common"},
        }

    def test_topview_preempts_seedance_and_card_fallback(self):
        with (
            patch.object(pipeline, "is_topview_slot", return_value=True),
            patch.object(pipeline.topview_inventory, "validate_inventory"),
            patch.object(pipeline, "is_seedance_slot", side_effect=AssertionError("Atlas判定をしてはいけない")),
            patch.object(pipeline, "_generate_passable_topview_candidate", return_value=(self._candidate(), 0)),
            patch.object(pipeline, "_generate_passable_seedance_candidate", side_effect=AssertionError("Atlasを呼んではいけない")),
            patch.object(pipeline, "_generate_passable_candidate", side_effect=AssertionError("旧カード版を作ってはいけない")),
            patch.object(pipeline, "_select_topic_entry", return_value={"topic": "fake topic"}),
            patch.object(pipeline.topic_store, "normalize_difficulty", return_value="beginner"),
        ):
            result = pipeline.produce(topic="fake topic", send_queue=False, target_platform="common")
        self.assertEqual(result["id"], "topview-id")

    def test_topview_inventory_failure_stops_before_topic_selection(self):
        with (
            patch.object(pipeline, "is_topview_slot", return_value=True),
            patch.object(pipeline.topview_inventory, "validate_inventory", side_effect=pipeline.TopviewInventoryError("stock missing")),
            patch.object(pipeline, "_select_topic_entry", side_effect=AssertionError("ネタを消費してはいけない")),
        ):
            with self.assertRaises(pipeline.TopviewInventoryError):
                pipeline.produce(topic=None, send_queue=False, target_platform="common")

    def test_topview_failure_never_falls_back_to_legacy_card(self):
        with (
            patch.object(pipeline, "is_topview_slot", return_value=True),
            patch.object(pipeline.topview_inventory, "validate_inventory"),
            patch.object(pipeline, "_generate_passable_topview_candidate", side_effect=RuntimeError("stock broken")),
            patch.object(pipeline, "_generate_passable_candidate", side_effect=AssertionError("旧カード版を作ってはいけない")),
            patch.object(pipeline, "_select_topic_entry", return_value={"topic": "fake topic"}),
            patch.object(pipeline.topic_store, "normalize_difficulty", return_value="beginner"),
        ):
            with self.assertRaises(pipeline.HybridGenerationBlocked):
                pipeline.produce(topic="fake topic", send_queue=False, target_platform="common")

    def test_is_seedance_slot_true_uses_seedance_candidate_when_it_passes(self):
        # is_seedance_slotがTrueで、Seedance候補が品質検証を合格した場合は
        # 静止画版へフォールバックしないこと。
        from src import pipeline

        seedance_calls = {"count": 0}
        fallback_calls = {"count": 0}

        def fake_seedance(*a, **kw):
            seedance_calls["count"] += 1
            report = {"pass": True, "accuracy": {"avg_cer": 0.05}, "duration": 40, "size_mb": 6, "checks": []}
            candidate = {
                "item_id": "seedance-id", "out_dir": Path("/tmp/seedance"), "report": report,
                "title": "seedance title", "topic": "fake topic",
                "script": {"title": "seedance title", "caption": "x" * 70, "hashtags": ["#a", "#b", "#c"], "target_platform": "common"},
            }
            return candidate, 0

        def fail_if_called(*a, **kw):
            fallback_calls["count"] += 1
            raise AssertionError("静止画版フォールバックが呼ばれてはいけない")

        with (
            patch.object(pipeline, "is_seedance_slot", return_value=True),
            patch.object(pipeline, "_generate_passable_seedance_candidate", side_effect=fake_seedance),
            patch.object(pipeline, "_generate_passable_candidate", side_effect=fail_if_called),
            patch.object(pipeline, "_select_topic_entry", return_value={"topic": "fake topic"}),
            patch.object(pipeline.topic_store, "normalize_difficulty", return_value="beginner"),
        ):
            result = pipeline.produce(topic="fake topic", send_queue=False, target_platform="common")

        self.assertEqual(seedance_calls["count"], 1)
        self.assertEqual(fallback_calls["count"], 0)
        self.assertEqual(result["id"], "seedance-id")

    def test_hybrid_failure_stops_without_card_fallback(self):
        """混在対象枠は失敗しても従来カード版へ置き換えない。"""
        from src import pipeline

        fallback_calls = {"count": 0}

        def fail_if_called(*a, **kw):
            fallback_calls["count"] += 1
            raise AssertionError("混在失敗時にカード版を作ってはいけない")

        with (
            patch.object(pipeline, "is_seedance_slot", return_value=True),
            patch.object(pipeline, "is_hybrid_seedance_slot", return_value=True),
            patch.object(
                pipeline,
                "_generate_passable_seedance_candidate",
                side_effect=RuntimeError("実写素材を生成できません"),
            ),
            patch.object(pipeline, "_generate_passable_candidate", side_effect=fail_if_called),
            patch.object(pipeline, "_select_topic_entry", return_value={"topic": "fake topic"}),
            patch.object(pipeline.topic_store, "normalize_difficulty", return_value="beginner"),
        ):
            with self.assertRaises(pipeline.HybridGenerationBlocked):
                pipeline.produce(topic="fake topic", send_queue=False, target_platform="common")

        self.assertEqual(fallback_calls["count"], 0)

    def test_non_hybrid_seedance_failure_keeps_card_fallback(self):
        """従来のSeedance枠は、混在対象でなければ従来どおりカードへ退避する。"""
        from src import pipeline

        fake_report = {"pass": True, "accuracy": {"avg_cer": 0.01}, "duration": 30, "size_mb": 5, "checks": []}
        fake_candidate = {
            "item_id": "card-id", "out_dir": Path("/tmp/card"), "report": fake_report,
            "title": "card title", "topic": "fake topic",
            "script": {"title": "card title", "caption": "x" * 70, "hashtags": ["#a", "#b", "#c"], "target_platform": "common"},
        }

        with (
            patch.object(pipeline, "is_seedance_slot", return_value=True),
            patch.object(pipeline, "is_hybrid_seedance_slot", return_value=False),
            patch.object(
                pipeline,
                "_generate_passable_seedance_candidate",
                side_effect=RuntimeError("Seedance障害"),
            ),
            patch.object(pipeline, "_generate_passable_candidate", return_value=(fake_candidate, 0)),
            patch.object(pipeline, "_select_topic_entry", return_value={"topic": "fake topic"}),
            patch.object(pipeline.topic_store, "normalize_difficulty", return_value="beginner"),
        ):
            result = pipeline.produce(topic="fake topic", send_queue=False, target_platform="common")

        self.assertEqual(result["id"], "card-id")

    def test_non_common_target_platform_never_triggers_seedance(self):
        # target_platform が common 以外（x/instagram/tiktok/youtube個別）の場合は
        # is_seedance_slot がTrueでもSeedance分岐に入らないこと
        # （Seedance統合は共通動画モード前提のため）。
        from src import pipeline

        called = {"seedance": False}

        def fail_if_called(*a, **kw):
            called["seedance"] = True
            raise AssertionError("target_platform!=commonでSeedanceが呼ばれてはいけない")

        fake_report = {"pass": True, "accuracy": {"avg_cer": 0.01}, "duration": 30, "size_mb": 5, "checks": []}
        fake_candidate = {
            "item_id": "fake-id", "out_dir": Path("/tmp/fake"), "report": fake_report,
            "title": "fake title", "topic": "fake topic",
            "script": {"title": "fake title", "caption": "x" * 70, "hashtags": ["#a", "#b", "#c"], "target_platform": "x"},
        }

        with (
            patch.object(pipeline, "is_seedance_slot", return_value=True),
            patch.object(pipeline, "_generate_passable_seedance_candidate", side_effect=fail_if_called),
            patch.object(pipeline, "_generate_passable_candidate", return_value=(fake_candidate, 0)),
            patch.object(pipeline, "_select_topic_entry", return_value={"topic": "fake topic"}),
            patch.object(pipeline.topic_store, "normalize_difficulty", return_value="beginner"),
        ):
            result = pipeline.produce(topic="fake topic", send_queue=False, target_platform="x")

        self.assertFalse(called["seedance"])
        self.assertEqual(result["id"], "fake-id")


class TopviewQualityAutoRepairTest(unittest.TestCase):
    def test_quality_failure_is_remade_once_before_safe_stop(self):
        failed = {
            "item_id": "topview-try1",
            "out_dir": Path("/tmp/topview-try1"),
            "report": {"pass": False, "checks": [{"name": "subtitle_accuracy_lines", "pass": False}]},
        }
        repaired = {
            "item_id": "topview-try2",
            "out_dir": Path("/tmp/topview-try2"),
            "report": {"pass": True, "checks": []},
        }
        config = {
            **CONFIG.cfg,
            "verify": {**CONFIG.cfg["verify"], "auto_remake_on_fail": True, "remake_max_attempts": 2},
        }
        with (
            patch.object(CONFIG, "cfg", config),
            patch.object(pipeline, "_build_topview_candidate", side_effect=[failed, repaired]) as build,
            patch.object(pipeline, "_mark_discarded_candidate") as mark_discarded,
        ):
            candidate, discarded = pipeline._generate_passable_topview_candidate("テストテーマ", "beginner")

        self.assertEqual(candidate["item_id"], "topview-try2")
        self.assertEqual(discarded, 1)
        self.assertEqual(build.call_args_list[0].args, ("テストテーマ", "beginner", 1))
        self.assertEqual(build.call_args_list[1].args, ("テストテーマ", "beginner", 2))
        mark_discarded.assert_called_once_with(failed, 2)


class SafeStopNotificationTest(unittest.TestCase):
    """安全停止は投稿を作らないが、通知だけは必ず出す。"""

    def test_topview_stock_stop_notifies_owner_with_stock_counts(self):
        manifest = {
            "clips": [
                {"id": "a", "enabled": True, "use_count": 1},
                {"id": "b", "enabled": True, "use_count": 0},
                {"id": "c", "enabled": False, "use_count": 0},
            ]
        }
        sent: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            def fake_get(*keys, default=None):
                if keys == ("topview", "manifest"):
                    return str(manifest_path)
                if keys == ("topview", "min_enabled_clips"):
                    return 6
                return default

            with (
                patch.object(pipeline.CONFIG, "get", side_effect=fake_get),
                patch.object(pipeline.notify, "send_message", side_effect=lambda t, **kw: sent.append(t)),
            ):
                pipeline.notify_safe_stop(pipeline.TopviewInventoryError("在庫が足りません"))

        self.assertEqual(len(sent), 1)
        text = sent[0]
        self.assertIn("安全停止", text)
        self.assertNotIn("在庫が足りません", text)
        self.assertIn("有効 2 本 / 未使用 1 本 / 必要 6 本", text)
        self.assertIn("従来カード版への自動代替は行いません。", text)

    def test_hybrid_block_notifies_owner(self):
        sent: list[str] = []
        with patch.object(pipeline.notify, "send_message", side_effect=lambda t, **kw: sent.append(t)):
            pipeline.notify_safe_stop(pipeline.HybridGenerationBlocked("external response https://example.invalid"))

        self.assertEqual(len(sent), 1)
        self.assertIn("Topview混在動画の生成処理で停止", sent[0])
        self.assertNotIn("external response", sent[0])
        self.assertNotIn("https://", sent[0])

    def test_notification_failure_does_not_raise(self):
        with (
            patch.object(pipeline.notify, "send_message", side_effect=RuntimeError("telegram down")),
            patch.object(pipeline, "log"),
        ):
            pipeline.notify_safe_stop(pipeline.HybridGenerationBlocked("blocked"))


class TopviewLowStockWarningTest(unittest.TestCase):
    """枯渇して安全停止する前に補充を促す。"""

    def _run(self, use_counts: list[int], threshold: int = 6) -> list[str]:
        manifest = {
            "clips": [
                {"id": f"c{i}", "enabled": True, "use_count": n}
                for i, n in enumerate(use_counts)
            ]
        }
        sent: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            def fake_get(*keys, default=None):
                if keys == ("topview", "manifest"):
                    return str(manifest_path)
                if keys == ("topview", "min_enabled_clips"):
                    return 6
                if keys == ("topview", "low_stock_warn_clips"):
                    return threshold
                return default

            with (
                patch.object(pipeline.CONFIG, "get", side_effect=fake_get),
                patch.object(pipeline.notify, "send_message", side_effect=lambda t, **kw: sent.append(t)),
            ):
                pipeline.warn_topview_stock_running_out()
        return sent

    def test_warns_when_unused_stock_is_low(self):
        sent = self._run([0, 0, 1, 1, 1, 1])
        self.assertEqual(len(sent), 1)
        self.assertIn("未使用 2 本", sent[0])
        self.assertIn("残り約 2 本ぶん", sent[0])

    def test_no_warning_while_stock_is_sufficient(self):
        self.assertEqual(self._run([0] * 10), [])

    def test_warns_when_stock_is_exhausted(self):
        sent = self._run([1, 1, 1, 1])
        self.assertEqual(len(sent), 1)
        self.assertIn("未使用 0 本", sent[0])


if __name__ == "__main__":
    unittest.main()
