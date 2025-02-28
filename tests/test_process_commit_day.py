import unittest
import asyncio
from unittest import mock
import json

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import github_tracker_bot.bot_functions as bot_functions
from github_tracker_bot.ai_decide_commits import decide_daily_commits
from openai import OpenAIError


class TestProcessCommitDay(unittest.TestCase):
    def setUp(self):
        # Sample data for testing
        self.username = "testuser"
        self.repo_link = "https://github.com/test/repo"
        self.commits_day = "2024-04-29"
        self.commits_data = [
            {
                "repo": "repo/test",
                "author": "author",
                "username": "username",
                "date": "2024-04-29T16:52:07Z",
                "message": "Test commit",
                "sha": "sha1",
                "branch": "main",
                "diff": "diff content",
            }
        ]
        
        # Create a patcher for the decide_daily_commits function
        self.decide_patcher = mock.patch('github_tracker_bot.bot_functions.decide_daily_commits')
        self.mock_decide = self.decide_patcher.start()
        
        # Create a patcher for the logger
        self.logger_patcher = mock.patch('github_tracker_bot.bot_functions.logger')
        self.mock_logger = self.logger_patcher.start()
    
    def tearDown(self):
        # Stop all patchers
        self.decide_patcher.stop()
        self.logger_patcher.stop()
    
    async def test_successful_process(self):
        """Test successful processing of commit data."""
        # Mock a successful response from decide_daily_commits
        valid_json = json.dumps({
            "username": "testuser",
            "date": "2024-04-29",
            "is_qualified": True,
            "explanation": "Valid commit"
        })
        self.mock_decide.return_value = valid_json
        
        # Call the function
        result = await bot_functions.process_commit_day(
            self.username, self.repo_link, self.commits_day, self.commits_data
        )
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result["username"], self.username)
        self.assertEqual(result["repository"], self.repo_link)
        self.assertEqual(result["date"], self.commits_day)
        self.assertEqual(result["response"]["is_qualified"], True)
        self.assertEqual(result["commit_hashes"], ["sha1"])
    
    async def test_invalid_json_response(self):
        """Test handling of invalid JSON response."""
        # Mock an invalid JSON response
        invalid_json = "This is not valid JSON"
        self.mock_decide.return_value = invalid_json
        
        # Call the function
        result = await bot_functions.process_commit_day(
            self.username, self.repo_link, self.commits_day, self.commits_data
        )
        
        # Verify the result is None
        self.assertIsNone(result)
        # Verify error was logged
        self.mock_logger.error.assert_any_call(mock.ANY)  # Any error message containing the invalid JSON
    
    async def test_decide_returns_false(self):
        """Test handling when decide_daily_commits returns False."""
        # Mock decide_daily_commits returning False (e.g., after max retries)
        self.mock_decide.return_value = False
        
        # Call the function
        result = await bot_functions.process_commit_day(
            self.username, self.repo_link, self.commits_day, self.commits_data
        )
        
        # Verify the result is None
        self.assertIsNone(result)
        # Verify error was logged
        self.mock_logger.error.assert_called()
    
    async def test_openai_error(self):
        """Test handling of OpenAI errors."""
        # Mock decide_daily_commits raising an OpenAI error
        self.mock_decide.side_effect = OpenAIError("OpenAI API error")
        
        # Call the function
        result = await bot_functions.process_commit_day(
            self.username, self.repo_link, self.commits_day, self.commits_data
        )
        
        # Verify the result is None
        self.assertIsNone(result)
        # Verify error was logged
        self.mock_logger.error.assert_called_with("OpenAI API call failed with error: OpenAI API error")
    
    async def test_unexpected_error(self):
        """Test handling of unexpected errors."""
        # Mock decide_daily_commits raising an unexpected error
        self.mock_decide.side_effect = Exception("Unexpected error")
        
        # Call the function
        result = await bot_functions.process_commit_day(
            self.username, self.repo_link, self.commits_day, self.commits_data
        )
        
        # Verify the result is None
        self.assertIsNone(result)
        # Verify error was logged
        self.mock_logger.error.assert_called_with("An unexpected error occurred: Unexpected error")


if __name__ == "__main__":
    unittest.main() 