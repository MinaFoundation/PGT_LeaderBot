import unittest
from unittest.mock import patch, MagicMock
from openai import OpenAIError, AuthenticationError, NotFoundError
import time
import asyncio

# Ensure the project root is in the path for imports
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the function you're testing
from github_tracker_bot.ai_decide_commits import decide_daily_commits

class TestDecideDailyCommits(unittest.TestCase):


    @patch('time.sleep', return_value=None)  # Mock time.sleep to avoid any waiting
    @patch('github_tracker_bot.ai_decide_commits.client.chat.completions.create')  # Patch the OpenAI API call
    @patch('github_tracker_bot.prompts.process_message')  # Patch the prompts module
    def test_decide_daily_commits_success(self, mock_process_message, mock_openai_create, mock_sleep):
        # Prepare test data
        test_date = "2024-10-15"
        test_data_array = [
            {
                "repo": "test_repo",
                "author": "test_author",
                "username": "test_user",
                "date": "2024-10-14",
                "message": "test commit",
                "sha": "abc123",
                "branch": "main",
                "diff": "some_diff"
            }
        ]
        seed = 42

        # Mock process_message to return a dummy message
        mock_process_message.return_value = "dummy_message"

        # Mock successful OpenAI API response on the first call
        mock_openai_create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="success"))])

        # Run the function
        result = asyncio.run(decide_daily_commits(test_date, test_data_array, seed))

        # Assert that the result is the success message returned by the OpenAI API
        self.assertEqual(result, "success")

        # Assert that the OpenAI API call was attempted only once (no retries)
        self.assertEqual(mock_openai_create.call_count, 1)

        # Assert that time.sleep was never called (since there was no retry needed)
        mock_sleep.assert_not_called()

    @patch('time.sleep', return_value=None)  # Mock time.sleep to avoid any waiting
    @patch('github_tracker_bot.ai_decide_commits.client.chat.completions.create')  # Patch the OpenAI API call
    @patch('github_tracker_bot.prompts.process_message')  # Patch the prompts module
    def test_decide_daily_commits_retry_403(self, mock_process_message, mock_openai_create, mock_sleep):
        # Prepare test data
        test_date = "2024-10-15"
        test_data_array = [
            {
                "repo": "test_repo",
                "author": "test_author",
                "username": "test_user",
                "date": "2024-10-14",
                "message": "test commit",
                "sha": "abc123",
                "branch": "main",
                "diff": "some_diff"
            }
        ]
        seed = 42

        # Mock process_message to return a dummy message
        mock_process_message.return_value = "dummy_message"

        # Create mock response and body for the exceptions
        mock_response = MagicMock()
        mock_body = "403 Forbidden"
        mock_message = "Authentication failed"

        # Mock 403 AuthenticationError for 5 retries and succeed on the 6th try
        mock_openai_create.side_effect = [AuthenticationError(mock_message, response=mock_response, body=mock_body)] * 5 + \
                                        [MagicMock(choices=[MagicMock(message=MagicMock(content="success"))])]

        # Run the function
        result = asyncio.run(decide_daily_commits(test_date, test_data_array, seed))

        # Assert that the result is successful after 5 retries
        self.assertEqual(result, "success")

        # Assert that the OpenAI API call was attempted 6 times (5 retries + 1 success)
        self.assertEqual(mock_openai_create.call_count, 6)

        # Assert that time.sleep was called 5 times (for 403 retries)
        self.assertEqual(mock_sleep.call_count, 5)


    @patch('github_tracker_bot.ai_decide_commits.client.chat.completions.create')  # Patch the OpenAI API call
    @patch('github_tracker_bot.prompts.process_message')  # Patch the prompts module
    def test_decide_daily_commits_404(self, mock_process_message, mock_openai_create):
        # Prepare test data
        test_date = "2024-10-15"
        test_data_array = [
            {
                "repo": "test_repo",
                "author": "test_author",
                "username": "test_user",
                "date": "2024-10-14",
                "message": "test commit",
                "sha": "abc123",
                "branch": "main",
                "diff": "some_diff"
            }
        ]
        seed = 42

        # Mock process_message to return a dummy message
        mock_process_message.return_value = "dummy_message"

        # Create mock response and body for the 404 error
        mock_response = MagicMock()
        mock_body = "404 Not Found"
        mock_message = "Resource not found"

        # Mock 404 NotFoundError
        mock_openai_create.side_effect = NotFoundError(mock_message, response=mock_response, body=mock_body)

        # Run the function
        result = asyncio.run(decide_daily_commits(test_date, test_data_array, seed))

        # Assert that the function returns False when a 404 error occurs
        self.assertFalse(result)

        # Assert that the OpenAI API call was only attempted once (no retries for 404)
        self.assertEqual(mock_openai_create.call_count, 1)

    @patch('github_tracker_bot.ai_decide_commits.client.chat.completions.create')  # Patch the OpenAI API call
    @patch('github_tracker_bot.prompts.process_message')  # Patch the prompts module
    def test_decide_daily_commits_500(self, mock_process_message, mock_openai_create):
        # Prepare test data
        test_date = "2024-10-15"
        test_data_array = [
            {
                "repo": "test_repo",
                "author": "test_author",
                "username": "test_user",
                "date": "2024-10-14",
                "message": "test commit",
                "sha": "abc123",
                "branch": "main",
                "diff": "some_diff"
            }
        ]
        seed = 42

        # Mock process_message to return a dummy message
        mock_process_message.return_value = "dummy_message"

        # Create mock response and body for the 500 error
        mock_message = "Server error"

        # Mock 500 Internal Server Error
        mock_openai_create.side_effect = OpenAIError(mock_message)

        # Run the function
        result = asyncio.run(decide_daily_commits(test_date, test_data_array, seed))

        # Assert that the function retries 5 times and then returns False
        self.assertFalse(result)

        # Assert that the OpenAI API call was attempted 5 times (maximum retries)
        self.assertEqual(mock_openai_create.call_count, 5)


if __name__ == '__main__':
    unittest.main()
