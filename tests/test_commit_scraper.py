import unittest
from unittest.mock import patch, AsyncMock
import asyncio
import aiohttp
from github.GithubException import GithubException

from github_tracker_bot.commit_scraper import fetch_commits, get_user_commits_in_repo


class TestCommitScraper(unittest.TestCase):
    def setUp(self):
        self.username = "berkingurcan"
        self.repo_link = "https://github.com/UmstadAI/zkAppUmstad"
        self.since = "2024-07-03T00:00:00Z"
        self.until = "2024-07-04T00:00:00Z"

    @patch('github_tracker_bot.commit_scraper.fetch_commits', new_callable=AsyncMock)
    @patch('github_tracker_bot.commit_scraper.g.get_repo')
    async def test_get_user_commits_in_repo(self, mock_get_repo, mock_fetch_commits):
        mock_repo = mock_get_repo.return_value
        mock_repo.get_branches.return_value = [
            AsyncMock(name="branch_main"),
            AsyncMock(name="branch_dev")
        ]

        mock_repo.get_branches.return_value[0].name = "main"
        mock_repo.get_branches.return_value[1].name = "dev"

        mock_fetch_commits.return_value = [
            {
                "sha": "commit_sha_1",
                "commit": {
                    "message": "Initial commit",
                    "committer": {"date": "2024-07-03T12:34:56Z"},
                    "author": {"name": self.username}
                }
            },
            {
                "sha": "commit_sha_2",
                "commit": {
                    "message": "Second commit",
                    "committer": {"date": "2024-07-03T13:34:56Z"},
                    "author": {"name": self.username}
                }
            }
        ]

        result = await get_user_commits_in_repo(self.username, self.repo_link, self.since, self.until)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['message'], "Initial commit")
        self.assertEqual(result[0]['branch'], "main")
        self.assertEqual(result[1]['message'], "Second commit")
        self.assertEqual(result[1]['branch'], "main")

    @patch('github_tracker_bot.commit_scraper.aiohttp.ClientSession.get', new_callable=AsyncMock)
    async def test_fetch_commits(self, mock_get):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = [
            {
                "sha": "commit_sha_1",
                "commit": {
                    "message": "Initial commit",
                    "committer": {"date": "2024-07-03T12:34:56Z"},
                    "author": {"name": self.username}
                }
            }
        ]
        mock_response.headers = {}
        mock_get.return_value.__aenter__.return_value = mock_response

        async with aiohttp.ClientSession() as session:
            result = await fetch_commits(session, "https://api.github.com/repos/UmstadAI/zkAppUmstad/commits")

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['sha'], "commit_sha_1")
        self.assertEqual(result[0]['commit']['message'], "Initial commit")

    @patch('github_tracker_bot.commit_scraper.aiohttp.ClientSession.get', new_callable=AsyncMock)
    async def test_fetch_commits_error(self, mock_get):
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.text.return_value = "Not Found"
        mock_get.return_value.__aenter__.return_value = mock_response

        async with aiohttp.ClientSession() as session:
            result = await fetch_commits(session, "https://api.github.com/repos/UmstadAI/zkAppUmstad/commits")

        self.assertIsNone(result)

def run_async_tests():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(unittest.main())

if __name__ == '__main__':
    run_async_tests()
