import unittest
import github_tracker_bot.helpers.extract_unnecessary_diff as lib

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

class TestFilterDiffs(unittest.TestCase):
    def test_filter_out_non_code_diffs(self):
        diff_text = """
        diff --git a/yarn.lock b/yarn.lock
        new file mode 100644
        index 0000000..e69de29

        diff --git a/package-lock.json b/package-lock.json
        new file mode 100644
        index 0000000..e69de29

        diff --git a/src/main.py b/src/main.py
        new file mode 100644
        index 0000000..e69de29
        --- a/src/main.py
        +++ b/src/main.py
        @@ -0,0 +1 @@
        +print("Hello World")
        """
        expected_output = """
        diff --git a/src/main.py b/src/main.py
        new file mode 100644
        index 0000000..e69de29
        --- a/src/main.py
        +++ b/src/main.py
        @@ -0,0 +1 @@
        +print("Hello World")
        """
        self.assertEqual(lib.filter_diffs(diff_text).strip(), expected_output.strip())

    def test_no_diffs_to_filter(self):
        diff_text = """
        diff --git a/src/main.py b/src/main.py
        new file mode 100644
        index 0000000..e69de29
        --- a/src/main.py
        +++ b/src/main.py
        @@ -0,0 +1 @@
        +print("Hello World")

        diff --git a/src/utils.py b/src/utils.py
        new file mode 100644
        index 0000000..e69de29
        --- a/src/utils.py
        +++ b/src/utils.py
        @@ -0,0 +1 @@
        +def util_function():
        +    pass
        """
       
        self.assertEquals(lib.filter_diffs(diff_text).strip(), diff_text.strip())

    def test_all_diffs_filtered(self):
        diff_text = """
        diff --git a/.gitignore b/.gitignore
        new file mode 100644
        index 0000000..e69de29

        diff --git a/Makefile b/Makefile
        new file mode 100644
        index 0000000..e69de29
        """
        expected_output = ""
        self.assertEqual(lib.filter_diffs(diff_text).strip(), expected_output.strip())

    def test_mixed_diffs(self):
        diff_text = """
        diff --git a/.gitignore b/.gitignore
        new file mode 100644
        index 0000000..e69de29

        diff --git a/src/main.py b/src/main.py
        new file mode 100644
        index 0000000..e69de29
        --- a/src/main.py
        +++ b/src/main.py
        @@ -0,0 +1 @@
        +print("Hello World")

        diff --git a/Makefile b/Makefile
        new file mode 100644
        index 0000000..e69de29
        """
        expected_output = """
        diff --git a/src/main.py b/src/main.py
        new file mode 100644
        index 0000000..e69de29
        --- a/src/main.py
        +++ b/src/main.py
        @@ -0,0 +1 @@
        +print("Hello World")
        """
        self.assertEqual(lib.filter_diffs(diff_text).strip(), expected_output.strip())

if __name__ == '__main__':
    unittest.main()
