import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import core


class IsAllowed(unittest.TestCase):
    def test_in_list(self):
        self.assertTrue(core.is_allowed(5, [1, 5, 9]))

    def test_not_in_list(self):
        self.assertFalse(core.is_allowed(7, [1, 5, 9]))

    def test_empty_list_rejects(self):
        # empty allowlist == setup mode: accept nothing
        self.assertFalse(core.is_allowed(5, []))


class ExtractImage(unittest.TestCase):
    def test_photo_picks_largest(self):
        msg = {"photo": [
            {"file_id": "small", "width": 90, "height": 90},
            {"file_id": "big", "width": 1280, "height": 960},
        ]}
        self.assertEqual(core.extract_image(msg), ("big", ".jpg"))

    def test_document_png_uses_filename_ext(self):
        msg = {"document": {"file_id": "d1", "mime_type": "image/png",
                            "file_name": "IMG.PNG"}}
        self.assertEqual(core.extract_image(msg), ("d1", ".png"))

    def test_document_uses_mime_when_no_name(self):
        msg = {"document": {"file_id": "d2", "mime_type": "image/jpeg"}}
        self.assertEqual(core.extract_image(msg), ("d2", ".jpg"))

    def test_non_image_document_is_none(self):
        msg = {"document": {"file_id": "d3", "mime_type": "application/pdf",
                            "file_name": "a.pdf"}}
        self.assertIsNone(core.extract_image(msg))

    def test_text_message_is_none(self):
        self.assertIsNone(core.extract_image({"text": "hi"}))

    def test_non_dict_is_none(self):
        self.assertIsNone(core.extract_image(None))


if __name__ == "__main__":
    unittest.main()
