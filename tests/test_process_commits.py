import unittest
from unittest.mock import patch, AsyncMock, call
import asyncio
import aiohttp

import time
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from github_tracker_bot.process_commits import fetch_diff


class TestFetchDiff(unittest.IsolatedAsyncioTestCase):

    @patch("aiohttp.ClientSession.get")
    async def test_successful_response(self, mock_get):
        # Mock the response object
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="diff content")
        mock_get.return_value.__aenter__.return_value = mock_response

        # Call the fetch_diff function
        repo = "memreok/PGT_LeaderBot"
        sha = "244a732c324d993d62dcb0017f8fd1b0d39d99e0"
        diff = await fetch_diff(repo, sha)

        # Assert the result
        self.assertEqual(diff, "diff content")

    @patch("aiohttp.ClientSession.get")
    async def test_retry_on_client_error(self, mock_get):
        first_attempt = AsyncMock()
        first_attempt.__aenter__.side_effect = aiohttp.ClientError()

        # Mock a successful response on retry
        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.text = AsyncMock(return_value="diff content")
        second_attempt = AsyncMock()
        second_attempt.__aenter__.return_value = mock_response_success

        # Set side effects for consecutive calls
        mock_get.side_effect = [first_attempt, second_attempt]

        repo = "memreok/PGT_LeaderBot"
        sha = "244a732c324d993d62dcb0017f8fd1b0d39d99e0"
        diff = await fetch_diff(repo, sha)

        # Assert the result after retry
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(diff, "diff content")

    @patch("aiohttp.ClientSession.get")
    async def test_retry_on_timeout_error(self, mock_get):
        first_attempt = AsyncMock()
        first_attempt.__aenter__.side_effect = asyncio.TimeoutError()

        # Mock a successful response on retry
        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.text = AsyncMock(return_value="diff content")
        second_attempt = AsyncMock()
        second_attempt.__aenter__.return_value = mock_response_success

        # Set side effects for consecutive calls
        mock_get.side_effect = [first_attempt, second_attempt]

        repo = "memreok/PGT_LeaderBot"
        sha = "244a732c324d993d62dcb0017f8fd1b0d39d99e0"
        diff = await fetch_diff(repo, sha)

        # Assert the result after retry
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(diff, "diff content")

    @patch("asyncio.sleep", new_callable=AsyncMock)
    @patch("time.time", return_value=1000)
    @patch("aiohttp.ClientSession.get")
    async def test_handle_403_api_rate_limit(self, mock_get, mock_time, mock_sleep):
        # Set a fixed current time
        current_time = 1000
        mock_time.return_value = current_time
        reset_time_in_future = current_time + 120  # 2 minutes in the future

        # Mock a 403 response with rate limit reset header
        mock_response_403 = AsyncMock()
        mock_response_403.status = 403
        mock_response_403.text = AsyncMock(return_value="API Rate Limit Exceeded")
        mock_response_403.headers = {"X-RateLimit-Reset": str(reset_time_in_future)}

        # Mock a successful response on retry
        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.text = AsyncMock(return_value="diff content")

        # Set side effects for consecutive calls
        first_attempt = AsyncMock()
        first_attempt.__aenter__.return_value = mock_response_403
        second_attempt = AsyncMock()
        second_attempt.__aenter__.return_value = mock_response_success
        mock_get.side_effect = [first_attempt, second_attempt]

        repo = "memreok/PGT_LeaderBot"
        sha = "244a732c324d993d62dcb0017f8fd1b0d39d99e0"
        diff = await fetch_diff(repo, sha)

        expected_sleep_time = reset_time_in_future - current_time + 1  # Should be 121

        # Assert that sleep was called twice:
        # 1. Once for the rate limit (expected_sleep_time)
        # 2. Once for the tenacity retry (fixed 2 seconds)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_has_calls([call(expected_sleep_time), call(2.0)])

        # Ensure that the second call to `aiohttp.get` was successful
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(diff, "diff content")

    @patch("aiohttp.ClientSession.get")
    async def test_general_exception_handling(self, mock_get):
        # Mock an unknown exception
        mock_get.side_effect = Exception("Unknown Error")

        repo = "memreok/PGT_LeaderBot"
        sha = "244a732c324d993d62dcb0017f8fd1b0d39d99e0"

        with self.assertRaises(Exception):
            await fetch_diff(repo, sha)


def run_async_tests():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(unittest.main())


if __name__ == "__main__":
    run_async_tests()
