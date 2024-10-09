import unittest
from unittest.mock import patch, AsyncMock
import asyncio
import aiohttp
from github.GithubException import GithubException
import time
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from github_tracker_bot.process_commits import fetch_diff

class TestGithubAPI(unittest.IsolatedAsyncioTestCase):

    @patch("aiohttp.ClientSession")
    async def test_fetch_diff_success(self, mock_client_session):
        repo = "test/repo"
        sha = "testsha"
        diff_content = "diff --git a/file.txt b/file.txt\n..."

        # Mock the commit data response
        mock_response_commit = AsyncMock()
        mock_response_commit.status = 200
        mock_response_commit.json.return_value = {"html_url": f"https://github.com/{repo}/commit/{sha}"}

        # Mock the diff data response
        mock_response_diff = AsyncMock()
        mock_response_diff.status = 200
        mock_response_diff.text.return_value = diff_content

        # Set up the mock session to handle both the commit and diff requests
        mock_session = AsyncMock()
        mock_session.get.side_effect = [mock_response_commit, mock_response_diff]

        # Ensure session behaves as an async context manager
        mock_client_session.return_value.__aenter__.return_value = mock_session
        mock_client_session.return_value.__aexit__.return_value = AsyncMock()

        # Call the fetch_diff function
        result = await fetch_diff(repo, sha)

        # Assert that the diff content is returned correctly
        self.assertEqual(result, diff_content)



    @patch("aiohttp.ClientSession")
    @patch("asyncio.sleep", return_value=None)  # Mock sleep to avoid actual waiting
    async def test_fetch_diff_rate_limit(self, mock_sleep, mock_client_session):
        repo = 'test/repo'
        sha = 'testsha'

        # Mock the 403 response with rate limit headers
        reset_time = int(time.sleep()) + 60  # 60 seconds in the future
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.headers = {'X-RateLimit-Reset': str(reset_time)}
        mock_response.text.return_value = "Rate limit exceeded"

        # Mock session.get to return the rate-limited response
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response
        mock_client_session.return_value.__aenter__.return_value = mock_session
        mock_client_session.return_value.__aexit__.return_value = AsyncMock()

        # Call the function
        result = await fetch_diff(repo, sha)

        # Calculate the expected sleep time
        expected_sleep_time = reset_time - int(time.sleep())

        # Assert that asyncio.sleep was called with the correct duration
        mock_sleep.assert_called_once_with(expected_sleep_time)

        # Assert that the result is None (since rate limit was hit)
        self.assertIsNone(result)


    @patch("aiohttp.ClientSession")
    async def test_fetch_diff_commit_not_found(self, mock_client_session):
        repo = "test/repo"
        sha = "invalidsha"
        url = f"https://api.github.com/repos/{repo}/commits/{sha}"

        # Mock session.get to return a 404 response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.text.return_value = "Not Found"

        # Set up mock session
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response
        mock_client_session.return_value.__aenter__.return_value = mock_session
        mock_client_session.return_value.__aexit__.return_value = AsyncMock()

        # Call the function
        result = await fetch_diff(repo, sha)

        # Assert that None is returned when commit data is not found
        self.assertIsNone(result)

    @patch("aiohttp.ClientSession")
    async def test_fetch_diff_diff_not_found(self, mock_client_session):
        repo = "test/repo"
        sha = "testsha"
        url = f"https://api.github.com/repos/{repo}/commits/{sha}"
        commit_data = {"html_url": f"https://github.com/{repo}/commit/{sha}"}

        # Mock session.get to return successful commit data response
        mock_response_commit = AsyncMock()
        mock_response_commit.status = 200
        mock_response_commit.json.return_value = commit_data

        # Mock session.get for diff request, returning 404 for diff
        mock_response_diff = AsyncMock()
        mock_response_diff.status = 404
        mock_response_diff.text.return_value = "Diff Not Found"

        # Set up mock session
        mock_session = AsyncMock()
        mock_session.get.side_effect = [mock_response_commit, mock_response_diff]
        mock_client_session.return_value.__aenter__.return_value = mock_session
        mock_client_session.return_value.__aexit__.return_value = AsyncMock()

        # Call the function
        result = await fetch_diff(repo, sha)

        # Assert that None is returned when the diff is not found
        self.assertIsNone(result)

    @patch("aiohttp.ClientSession")
    async def test_fetch_diff_client_error(self, mock_client_session):
        repo = "test/repo"
        sha = "testsha"

        # Mock session.get to raise aiohttp.ClientError
        mock_session = AsyncMock()
        mock_session.get.side_effect = aiohttp.ClientError
        mock_client_session.return_value.__aenter__.return_value = mock_session
        mock_client_session.return_value.__aexit__.return_value = AsyncMock()

        # Call the function and assert that it raises the error
        with self.assertRaises(aiohttp.ClientError):
            await fetch_diff(repo, sha)

    @patch("aiohttp.ClientSession")
    async def test_fetch_diff_timeout_error(self, mock_client_session):
        repo = "test/repo"
        sha = "testsha"

        # Mock session.get to raise asyncio.TimeoutError
        mock_session = AsyncMock()
        mock_session.get.side_effect = asyncio.TimeoutError
        mock_client_session.return_value.__aenter__.return_value = mock_session
        mock_client_session.return_value.__aexit__.return_value = AsyncMock()

        # Mock the context manager for session.get() so that it correctly handles 'async with'
        mock_response = AsyncMock()
        mock_response.__aenter__.side_effect = asyncio.TimeoutError  # Simulate the timeout when entering the context
        mock_session.get.return_value = mock_response

        # Call the function and assert that it raises asyncio.TimeoutError
        with self.assertRaises(asyncio.TimeoutError):
            await fetch_diff(repo, sha)



def run_async_tests():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(unittest.main())


if __name__ == "__main__":
    run_async_tests()
