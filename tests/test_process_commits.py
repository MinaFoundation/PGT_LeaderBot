import unittest
from unittest.mock import patch, AsyncMock
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
        # Mock a client error for the first attempt, then success on retry
        mock_get.side_effect = [
            aiohttp.ClientError(),
            AsyncMock(status=200, text=AsyncMock(return_value="diff content")),
        ]

        repo = "memreok/PGT_LeaderBot"
        sha = "244a732c324d993d62dcb0017f8fd1b0d39d99e0"
        diff = await fetch_diff(repo, sha)

        # Assert the result after retry
        self.assertEqual(diff, "diff content")
        self.assertEqual(mock_get.call_count, 2)  # Ensure it retried once

    @patch("aiohttp.ClientSession.get")
    async def test_retry_on_timeout_error(self, mock_get):
        # Mock a timeout error for the first attempt, then success on retry
        mock_get.side_effect = [
            asyncio.TimeoutError(),
            AsyncMock(status=200, text=AsyncMock(return_value="diff content")),
        ]

        repo = "memreok/PGT_LeaderBot"
        sha = "244a732c324d993d62dcb0017f8fd1b0d39d99e0"
        diff = await fetch_diff(repo, sha)

        # Assert the result after retry
        self.assertEqual(diff, "diff content")
        self.assertEqual(mock_get.call_count, 2)  # Ensure it retried once

    @patch('asyncio.sleep', return_value=None)  # Mock sleep to skip delay
    @patch('aiohttp.ClientSession.get')
    async def test_handle_403_api_rate_limit(self, mock_sleep, mock_get):
        # Mock a 403 response for rate limit exceeded, then success on retry
        mock_response_403 = AsyncMock()
        mock_response_403.status = 403
        mock_response_403.text = AsyncMock(return_value="API Rate Limit Exceeded")
        
        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.text = AsyncMock(return_value="diff content")

        mock_get.side_effect = [
            mock_response_403,
            mock_response_success
        ]

        repo = "memreok/PGT_LeaderBot"
        sha = "244a732c324d993d62dcb0017f8fd1b0d39d99e0"
        diff = await fetch_diff(repo, sha)

        # Assert the result after retrying due to rate limit
        self.assertEqual(diff, "diff content")
        self.assertEqual(mock_get.call_count, 2)  # Ensure it retried
        mock_sleep.assert_called_once_with(60)  # Ensure it slept for 60 seconds


    @patch('aiohttp.ClientSession.get')
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
