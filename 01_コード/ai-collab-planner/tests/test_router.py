import unittest
from pathlib import Path

from ai_planner.config import load_settings
from ai_planner.router import decide_level


SETTINGS = load_settings(Path(__file__).parents[1] / "config.toml")


class RouterTest(unittest.TestCase):
    def test_critical_keyword_has_highest_priority(self):
        result = decide_level("本番の決済機能を変更したい", SETTINGS)
        self.assertEqual(result.level, "critical")
        self.assertIn("決済", result.matched_keywords)

    def test_complex_feature(self):
        result = decide_level("iOSとAndroidで位置情報を記録したい", SETTINGS)
        self.assertEqual(result.level, "complex")

    def test_light_change(self):
        result = decide_level("READMEの誤字を修正したい", SETTINGS)
        self.assertEqual(result.level, "light")

    def test_standard_is_default(self):
        result = decide_level("問い合わせ一覧に絞り込み機能を追加したい", SETTINGS)
        self.assertEqual(result.level, "standard")


if __name__ == "__main__":
    unittest.main()
