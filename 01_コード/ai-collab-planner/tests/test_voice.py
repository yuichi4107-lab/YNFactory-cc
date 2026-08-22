import unittest
from unittest.mock import patch

from ai_planner.voice import WindowsVoiceIO, parse_yes_no


class VoiceTest(unittest.TestCase):
    def test_yes_words(self):
        self.assertTrue(parse_yes_no("はい、進めてください"))

    def test_no_words(self):
        self.assertFalse(parse_yes_no("いいえ、修正してください"))

    def test_unknown_word(self):
        self.assertIsNone(parse_yes_no("少し考えます"))

    def test_domain_corrections_are_applied(self):
        voice = WindowsVoiceIO(corrections={"コーデックス": "Codex", "クロード": "Claude"})
        self.assertEqual(voice._apply_corrections("コーデックスとクロード"), "CodexとClaude")

    def test_whisper_is_preferred(self):
        voice = WindowsVoiceIO(backend="auto", corrections={"コーデックス": "Codex"})
        with patch.object(voice, "_listen_whisper", return_value="コーデックスで実装"), patch.object(
            voice, "_listen_windows", return_value="Windows結果"
        ) as windows:
            result = voice.listen()
        self.assertEqual(result, "Codexで実装")
        windows.assert_not_called()

    def test_windows_is_used_when_whisper_fails(self):
        voice = WindowsVoiceIO(backend="auto")
        with patch.object(voice, "_listen_whisper", return_value=None), patch.object(
            voice, "_listen_windows", return_value="予備の結果"
        ):
            result = voice.listen()
        self.assertEqual(result, "予備の結果")


if __name__ == "__main__":
    unittest.main()
