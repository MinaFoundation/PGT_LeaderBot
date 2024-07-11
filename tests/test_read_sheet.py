import unittest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from github_tracker_bot.read_sheet import read_sheet


class TestReadSheet(unittest.TestCase):
    def test_read_sheet_with_data(self):
        values = read_sheet()
        self.assertIsInstance(values, list)
        self.assertGreater(
            len(values), 1, "Expected non-empty data from the sheet with column names"
        )
        self.assertEqual(len(values[0]), 3, "Expected column number is ok.")


if __name__ == "__main__":
    unittest.main()
