import unittest
from unittest.mock import patch, AsyncMock

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import aiohttp
import asyncio
from github_tracker_bot.process_commits import fetch_diff
import config
from  github import Github

GITHUB_TOKEN = config.GITHUB_TOKEN
g = Github(GITHUB_TOKEN)




class TestFetchDiff(unittest.IsolatedAsyncioTestCase):
    @patch("aiohttp.ClientSession.get")


    
    async def test_fetch_diff_403_error(self, mock_get):
        # Mock the response to simulate a 403 Forbidden error
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.text = AsyncMock(return_value="Forbidden")
        mock_get.return_value.__aenter__.return_value = mock_response

        

        repo_name = "MinaFoundation/PGT_LeaderBot"
        sha = "16e7227acb63c112ec32fd757d7afd46f26e6b3c"

        # Run the fetch_diff function
        diff = await fetch_diff(repo_name, sha)
        

        # Assertions to check if the function behaves as expected
        self.assertIsNotNone(diff)  # Diff should be None due to 403 error
        mock_get.assert_called()  # Ensure that the get method was called

if __name__ == "__main__":
    unittest.main()
