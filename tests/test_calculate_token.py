import unittest
import tiktoken
import github_tracker_bot.helpers.calculate_token as lib

class TestCalculateTokenNumber(unittest.TestCase):
    def generate_data_with_token_count(self, token_count):
        return "word " * (token_count-1)
    
    def test_token_count_below_limit(self):
        data = self.generate_data_with_token_count(50000)
        result = lib.calculate_token_number(data)
        self.assertEqual(result, True)

    def test_token_count_above_limit(self):
        data = self.generate_data_with_token_count(130000)
        result = lib.calculate_token_number(data)
        self.assertEqual(result, False)

if __name__ == '__main__':
    unittest.main()