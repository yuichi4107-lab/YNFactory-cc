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


if __name__ == "__main__":
    unittest.main()
