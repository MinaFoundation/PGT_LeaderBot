import unittest
import asyncio
from unittest import mock
import json

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
import github_tracker_bot.ai_decide_commits as ai
from openai import OpenAIError, APIError, APIConnectionError, RateLimitError


class MockResponse:
    def __init__(self, content):
        self.choices = [mock.MagicMock()]
        self.choices[0].message.content = content


class TestOpenAIRetryMechanism(unittest.TestCase):
    def setUp(self):
        # Sample commit data for testing
        self.commit_data = [
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
        
        # Save original values to restore after tests
        self.original_max_retries = config.OPENAI_MAX_RETRIES
        self.original_initial_retry_delay = config.OPENAI_INITIAL_RETRY_DELAY
        
        # Set shorter values for testing
        config.OPENAI_MAX_RETRIES = 2
        config.OPENAI_INITIAL_RETRY_DELAY = 0.1  # Use very short delay for tests
        
        # Create a patcher for the OpenAI client
        self.client_patcher = mock.patch('github_tracker_bot.ai_decide_commits.client')
        self.mock_client = self.client_patcher.start()
        
        # Create a patcher for asyncio.sleep to avoid actual waiting
        self.sleep_patcher = mock.patch('asyncio.sleep', return_value=None)
        self.mock_sleep = self.sleep_patcher.start()
        
        # Create a patcher for the logger
        self.logger_patcher = mock.patch('github_tracker_bot.ai_decide_commits.logger')
        self.mock_logger = self.logger_patcher.start()
    
    def tearDown(self):
        # Restore original config values
        config.OPENAI_MAX_RETRIES = self.original_max_retries
        config.OPENAI_INITIAL_RETRY_DELAY = self.original_initial_retry_delay
        
        # Stop all patchers
        self.client_patcher.stop()
        self.sleep_patcher.stop()
        self.logger_patcher.stop()
    
    async def test_successful_api_call(self):
        """Test that a successful API call returns the expected result."""
        expected_response = json.dumps({"result": "success"})
        self.mock_client.chat.completions.create.return_value = MockResponse(expected_response)
        
        result = await ai.decide_daily_commits("2024-04-29", self.commit_data)
        
        # Verify the result
        self.assertEqual(result, expected_response)
        # Verify the API was called exactly once
        self.assertEqual(self.mock_client.chat.completions.create.call_count, 1)
        # Verify no retries were attempted
        self.mock_sleep.assert_not_called()
    
    async def test_retry_on_403_forbidden(self):
        """Test that a 403 Forbidden error triggers a retry."""
        # Set up the mock to fail with 403 once, then succeed
        error_message = "403 Forbidden"
        expected_response = json.dumps({"result": "success after retry"})
        
        self.mock_client.chat.completions.create.side_effect = [
            OpenAIError(error_message),
            MockResponse(expected_response)
        ]
        
        result = await ai.decide_daily_commits("2024-04-29", self.commit_data)
        
        # Verify the result
        self.assertEqual(result, expected_response)
        # Verify the API was called twice (initial + 1 retry)
        self.assertEqual(self.mock_client.chat.completions.create.call_count, 2)
        # Verify sleep was called once for the retry
        self.mock_sleep.assert_called_once()
        # Verify appropriate logging
        self.mock_logger.error.assert_called_with(f"OpenAI API call failed with error: {error_message}")
        self.mock_logger.info.assert_called()  # Should log about retrying
    
    async def test_retry_on_html_response(self):
        """Test that an HTML error response triggers a retry."""
        # Set up the mock to fail with HTML once, then succeed
        error_message = "<!DOCTYPE html>"
        expected_response = json.dumps({"result": "success after retry"})
        
        self.mock_client.chat.completions.create.side_effect = [
            OpenAIError(error_message),
            MockResponse(expected_response)
        ]
        
        result = await ai.decide_daily_commits("2024-04-29", self.commit_data)
        
        # Verify the result
        self.assertEqual(result, expected_response)
        # Verify the API was called twice (initial + 1 retry)
        self.assertEqual(self.mock_client.chat.completions.create.call_count, 2)
        # Verify sleep was called once for the retry
        self.mock_sleep.assert_called_once()
    
    async def test_retry_on_rate_limit(self):
        """Test that a rate limit error triggers a retry."""
        # Set up the mock to fail with rate limit once, then succeed
        error_message = "rate limit exceeded"
        expected_response = json.dumps({"result": "success after retry"})
        
        self.mock_client.chat.completions.create.side_effect = [
            RateLimitError(error_message),
            MockResponse(expected_response)
        ]
        
        result = await ai.decide_daily_commits("2024-04-29", self.commit_data)
        
        # Verify the result
        self.assertEqual(result, expected_response)
        # Verify the API was called twice (initial + 1 retry)
        self.assertEqual(self.mock_client.chat.completions.create.call_count, 2)
        # Verify sleep was called once for the retry
        self.mock_sleep.assert_called_once()
    
    async def test_retry_on_server_error(self):
        """Test that a server error triggers a retry."""
        # Set up the mock to fail with 500 once, then succeed
        error_message = "500 Internal Server Error"
        expected_response = json.dumps({"result": "success after retry"})
        
        self.mock_client.chat.completions.create.side_effect = [
            APIError(error_message),
            MockResponse(expected_response)
        ]
        
        result = await ai.decide_daily_commits("2024-04-29", self.commit_data)
        
        # Verify the result
        self.assertEqual(result, expected_response)
        # Verify the API was called twice (initial + 1 retry)
        self.assertEqual(self.mock_client.chat.completions.create.call_count, 2)
        # Verify sleep was called once for the retry
        self.mock_sleep.assert_called_once()
    
    async def test_retry_on_timeout(self):
        """Test that a timeout error triggers a retry."""
        # Set up the mock to fail with timeout once, then succeed
        error_message = "timeout"
        expected_response = json.dumps({"result": "success after retry"})
        
        self.mock_client.chat.completions.create.side_effect = [
            APIConnectionError(error_message),
            MockResponse(expected_response)
        ]
        
        result = await ai.decide_daily_commits("2024-04-29", self.commit_data)
        
        # Verify the result
        self.assertEqual(result, expected_response)
        # Verify the API was called twice (initial + 1 retry)
        self.assertEqual(self.mock_client.chat.completions.create.call_count, 2)
        # Verify sleep was called once for the retry
        self.mock_sleep.assert_called_once()
    
    async def test_max_retries_exceeded(self):
        """Test that the function gives up after max retries."""
        # Set up the mock to always fail with 403
        error_message = "403 Forbidden"
        
        self.mock_client.chat.completions.create.side_effect = OpenAIError(error_message)
        
        result = await ai.decide_daily_commits("2024-04-29", self.commit_data)
        
        # Verify the result is False (failure)
        self.assertFalse(result)
        # Verify the API was called max_retries + 1 times (initial + retries)
        self.assertEqual(self.mock_client.chat.completions.create.call_count, config.OPENAI_MAX_RETRIES + 1)
        # Verify sleep was called max_retries times
        self.assertEqual(self.mock_sleep.call_count, config.OPENAI_MAX_RETRIES)
        # Verify appropriate logging
        self.mock_logger.error.assert_any_call(f"Maximum retry attempts ({config.OPENAI_MAX_RETRIES}) reached. Giving up.")
    
    async def test_no_retry_on_other_openai_errors(self):
        """Test that other OpenAI errors don't trigger retries."""
        # Set up the mock to fail with a non-retryable error
        error_message = "Invalid request"
        
        self.mock_client.chat.completions.create.side_effect = OpenAIError(error_message)
        
        result = await ai.decide_daily_commits("2024-04-29", self.commit_data)
        
        # Verify the result is False (failure)
        self.assertFalse(result)
        # Verify the API was called exactly once (no retries)
        self.assertEqual(self.mock_client.chat.completions.create.call_count, 1)
        # Verify sleep was not called
        self.mock_sleep.assert_not_called()
    
    async def test_exponential_backoff(self):
        """Test that the backoff delay increases exponentially."""
        # Set up the mock to fail multiple times
        error_message = "403 Forbidden"
        
        self.mock_client.chat.completions.create.side_effect = [
            OpenAIError(error_message),
            OpenAIError(error_message),
            OpenAIError(error_message)
        ]
        
        result = await ai.decide_daily_commits("2024-04-29", self.commit_data)
        
        # Verify the sleep calls have increasing delays
        self.assertEqual(self.mock_sleep.call_count, 2)  # We set max_retries to 2
        
        # Get the sleep call arguments
        sleep_calls = self.mock_sleep.call_args_list
        first_delay = sleep_calls[0][0][0]
        second_delay = sleep_calls[1][0][0]
        
        # Verify the second delay is greater than the first
        self.assertGreater(second_delay, first_delay)
    
    async def test_successful_retry_logging(self):
        """Test that successful retries are logged."""
        # Set up the mock to fail once, then succeed
        error_message = "403 Forbidden"
        expected_response = json.dumps({"result": "success after retry"})
        
        self.mock_client.chat.completions.create.side_effect = [
            OpenAIError(error_message),
            MockResponse(expected_response)
        ]
        
        result = await ai.decide_daily_commits("2024-04-29", self.commit_data)
        
        # Verify successful retry was logged
        self.mock_logger.info.assert_any_call("Successfully completed OpenAI API call after 1 retries")


if __name__ == "__main__":
    unittest.main() 