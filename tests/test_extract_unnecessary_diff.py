import unittest
import re
import github_tracker_bot.lib.extract_unnecessary_diff as lib

# Unit tests
class TestNonCodeFileDetection(unittest.TestCase):

    def test_is_non_code_file(self):
        self.assertTrue(lib.is_non_code_file("yarn.lock"))
        self.assertTrue(lib.is_non_code_file("package-lock.json"))
        self.assertTrue(lib.is_non_code_file("node_modules/package"))
        self.assertFalse(lib.is_non_code_file("main.py"))
        self.assertFalse(lib.is_non_code_file("src/main.c"))

    def test_extract_file_path(self):
        diff_data = "diff --git a/src/main.py b/src/main.py\n"
        self.assertEqual(lib.extract_file_path(diff_data), "src/main.py")

        diff_data_no_match = "some random text"
        self.assertIsNone(lib.extract_file_path(diff_data_no_match))

    def test_process_diff(self):
        diff_data_code_file = "diff --git a/src/main.py b/src/main.py\n"
        self.assertFalse(lib.process_diff(diff_data_code_file))

        diff_data_non_code_file = "diff --git a/yarn.lock b/yarn.lock\n"
        self.assertTrue(lib.process_diff(diff_data_non_code_file))

        diff_data_no_path = "some random text"
        self.assertTrue(lib.process_diff(diff_data_no_path))

if __name__ == '__main__':
    unittest.main()
