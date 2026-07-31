from __future__ import annotations

import http.client
import importlib.util
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "ebook_setup_ui.py"
SPEC = importlib.util.spec_from_file_location("ebook_setup_ui", MODULE_PATH)
assert SPEC and SPEC.loader
ebook_setup_ui = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ebook_setup_ui
SPEC.loader.exec_module(ebook_setup_ui)


EXPECTED = {
    "theme_handling": [
        "入力内容のテーマで進める (Recommended)",
        "入力内容を少し広げて進める",
        "入力内容を絞り込んで進める",
        "別テーマを指定する",
    ],
    "target_reader": [
        "初心者・これから始める人 (Recommended)",
        "中小企業の経営者・管理職",
        "実務担当者・現場リーダー",
        "専門家・上級者",
    ],
    "book_type": [
        "実践書・手順書 (Recommended)",
        "やさしい入門書",
        "ストーリー・事例中心",
        "考え方・思想を伝える本",
    ],
    "tone": [
        "やさしいです・ます調 (Recommended)",
        "端的でビジネス寄り",
        "親しみやすい会話調",
        "専門家らしい落ち着いた文体",
    ],
    "length": [
        "約100,000字 (Recommended)",
        "約50,000字",
        "約25,000字",
        "自由記述で指定",
    ],
    "image_density": [
        "標準（章ごとに数点） (Recommended)",
        "少なめ",
        "多め",
        "図解中心",
    ],
}


def recommended_payload(theme: str = "どんなテーマでも使える本") -> dict:
    answers = {}
    for question in ebook_setup_ui.QUESTIONS:
        option = question["options"][0]
        answers[question["id"]] = {"value": option["value"], "label": option["label"]}
    return {
        "theme": theme,
        "mode": "theme-to-ebook",
        "answers": answers,
        "free_text": "",
        "safety_policy": "クライアントから送った値は信用しない",
    }


class QuestionDefinitionTests(unittest.TestCase):
    def test_phase_zero_questions_and_options_match_skill(self) -> None:
        self.assertEqual([question["id"] for question in ebook_setup_ui.QUESTIONS], list(EXPECTED))
        for question in ebook_setup_ui.QUESTIONS:
            labels = [option["label"] for option in question["options"]]
            self.assertEqual(labels, EXPECTED[question["id"]])

    def test_recommended_option_is_first_and_only_one(self) -> None:
        for question in ebook_setup_ui.QUESTIONS:
            recommended = [option for option in question["options"] if option.get("recommended")]
            self.assertEqual(len(recommended), 1, question["id"])
            self.assertIs(question["options"][0], recommended[0])
            self.assertTrue(recommended[0]["label"].endswith(" (Recommended)"))

    def test_legacy_health_specific_defaults_are_removed(self) -> None:
        serialized = json.dumps(ebook_setup_ui.QUESTIONS, ensure_ascii=False)
        for legacy_text in ("ソマチッド", "自然療法", "健康関心層", "検証派"):
            self.assertNotIn(legacy_text, serialized)
        self.assertEqual(
            ebook_setup_ui.SAFETY_POLICY,
            "医療・健康・投資・法律などの該当ジャンルでは、断定を避け、根拠を確認して表現する",
        )


class HtmlSafetyTests(unittest.TestCase):
    def test_arbitrary_theme_cannot_break_out_of_html_or_script(self) -> None:
        hostile = '</script><script>alert("theme")</script><img src=x onerror=alert(1)>'
        page = ebook_setup_ui.render_page(hostile, hostile).decode("utf-8")
        self.assertNotIn(hostile, page)
        self.assertNotIn("<img src=x", page)
        self.assertIn("&lt;/script&gt;", page)
        self.assertIn("\\u003c/script\\u003e", page)


class ValidationTests(unittest.TestCase):
    def test_valid_payload_is_normalized_to_value_label_pairs(self) -> None:
        payload = recommended_payload()
        result = ebook_setup_ui.validate_submission(payload, payload["theme"], payload["mode"])
        self.assertEqual(set(result["answers"]), set(EXPECTED))
        self.assertTrue(all(set(answer) == {"value", "label"} for answer in result["answers"].values()))
        self.assertEqual(result["safety_policy"], ebook_setup_ui.SAFETY_POLICY)

    def test_missing_question_is_rejected(self) -> None:
        payload = recommended_payload()
        del payload["answers"]["tone"]
        with self.assertRaisesRegex(ValueError, "未回答"):
            ebook_setup_ui.validate_submission(payload, payload["theme"], payload["mode"])

    def test_unknown_value_is_rejected(self) -> None:
        payload = recommended_payload()
        payload["answers"]["tone"] = {"value": "injected", "label": "<script>"}
        with self.assertRaisesRegex(ValueError, "定義されていない選択肢"):
            ebook_setup_ui.validate_submission(payload, payload["theme"], payload["mode"])

    def test_wrong_label_is_rejected(self) -> None:
        payload = recommended_payload()
        payload["answers"]["tone"]["label"] = "書き換えたラベル"
        with self.assertRaisesRegex(ValueError, "ラベル"):
            ebook_setup_ui.validate_submission(payload, payload["theme"], payload["mode"])

    def test_other_theme_requires_free_text(self) -> None:
        payload = recommended_payload()
        option = ebook_setup_ui.QUESTIONS[0]["options"][-1]
        payload["answers"]["theme_handling"] = {"value": option["value"], "label": option["label"]}
        with self.assertRaisesRegex(ValueError, "テーマを入力"):
            ebook_setup_ui.validate_submission(payload, payload["theme"], payload["mode"])

    def test_custom_length_requires_free_text(self) -> None:
        payload = recommended_payload()
        option = next(item for item in ebook_setup_ui.QUESTIONS[4]["options"] if item["value"] == "custom")
        payload["answers"]["length"] = {"value": option["value"], "label": option["label"]}
        with self.assertRaisesRegex(ValueError, "希望文字量"):
            ebook_setup_ui.validate_submission(payload, payload["theme"], payload["mode"])


class HttpHandlerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.server = ebook_setup_ui.SetupServer(
            ("127.0.0.1", 0),
            theme="一般テーマ",
            mode="theme-to-ebook",
            output_dir=Path(self.temp_dir.name),
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def post(self, body: bytes) -> tuple[int, dict]:
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        connection.request("POST", "/submit", body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        result = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, result

    def test_invalid_json_is_rejected_without_writing_files(self) -> None:
        status, _ = self.post(b"{not-json")
        self.assertEqual(status, 400)
        self.assertFalse((Path(self.temp_dir.name) / "latest.json").exists())

    def test_valid_submission_writes_latest_json(self) -> None:
        payload = recommended_payload(theme="一般テーマ")
        status, result = self.post(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        self.assertEqual(status, 200)
        self.assertTrue(result["ok"])
        latest = json.loads((Path(self.temp_dir.name) / "latest.json").read_text(encoding="utf-8"))
        self.assertEqual(latest["answers"]["length"]["value"], "100000")
        self.assertEqual(latest["answers"]["length"]["label"], "約100,000字 (Recommended)")
        self.assertEqual(latest["source"], "local_ebook_setup_ui")


if __name__ == "__main__":
    unittest.main()
