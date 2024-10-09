import unittest
from unittest.mock import patch, AsyncMock
import asyncio
import aiohttp
from github.GithubException import GithubException
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from github_tracker_bot.process_commits import fetch_diff

class TestGithubAPI(unittest.TestCase):

    @patch("github_tracker_bot.process_commits.fetch_diff", new_callable=AsyncMock)
    async def test_fetch_diff_success():
        repo = 'test/repo'
        sha = 'testsha'
        url = f'https://api.github.com/repos/{repo}/commits/{sha}'
        diff_content = 'diff --git a/file.txt b/file.txt\n...'

        with aioresponses() as m:
            m.get(
                url,
                status=200,
                body=diff_content,
                headers={'Content-Type': 'application/vnd.github.v3.diff'}
            )

            result = await fetch_diff(repo, sha)
            assert result == diff_content


""" 
    @pytest.mark.asyncio
    async def test_fetch_diff_404_error():
        repo = 'invalid/repo'
        sha = 'invalidsha'
        url = f'https://api.github.com/repos/{repo}/commits/{sha}'

        with aioresponses() as m:
            m.get(
                url,
                status=404,
                body='Not Found'
            )

            result = await fetch_diff(repo, sha)
            assert result is None
        pass

    @pytest.mark.asyncio
    async def test_fetch_diff_rate_limit():
        repo = 'test/repo'
        sha = 'testsha'
        url = f'https://api.github.com/repos/{repo}/commits/{sha}'

        with aioresponses() as m:
            m.get(
                url,
                status=403,
                body='Rate limit exceeded',
                headers={
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': '9999999999'
                }
            )

            result = await fetch_diff(repo, sha)
            assert result is None
        pass

    @pytest.mark.asyncio
    async def test_fetch_diff_server_error():
        repo = 'test/repo'
        sha = 'testsha'
        url = f'https://api.github.com/repos/{repo}/commits/{sha}'

        with aioresponses() as m:
            m.get(
                url,
                status=500,
                body='Internal Server Error'
            )

            result = await fetch_diff(repo, sha)
            assert result is None
        pass

    @pytest.mark.asyncio
    async def test_fetch_diff_client_error():
        repo = 'test/repo'
        sha = 'testsha'

        with patch('aiohttp.ClientSession.get', side_effect=aiohttp.ClientError):
            with pytest.raises(aiohttp.ClientError):
                await fetch_diff(repo, sha)
        pass
    @pytest.mark.asyncio
    async def test_fetch_diff_timeout_error():
        repo = 'test/repo'
        sha = 'testsha'

        with patch('aiohttp.ClientSession.get', side_effect=asyncio.TimeoutError):
            with pytest.raises(asyncio.TimeoutError):
                await fetch_diff(repo, sha)
        pass

    @pytest.mark.asyncio
    async def test_fetch_diff_unauthorized():
        repo = 'test/repo'
        sha = 'testsha'
        url = f'https://api.github.com/repos/{repo}/commits/{sha}'

        with aioresponses() as m:
            m.get(
                url,
                status=401,
                body='Unauthorized'
            )

            result = await fetch_diff(repo, sha)
            assert result is None
        pass

    @pytest.mark.asyncio
    async def test_fetch_diff_malformed_content():
        repo = 'test/repo'
        sha = 'testsha'
        url = f'https://api.github.com/repos/{repo}/commits/{sha}'
        diff_content = 'MALFORMED DIFF CONTENT'

        with aioresponses() as m:
            m.get(
                url,
                status=200,
                body=diff_content,
                headers={'Content-Type': 'application/vnd.github.v3.diff'}
            )

            result = await fetch_diff(repo, sha)
            assert result == diff_content
        pass """

def run_async_tests():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(unittest.main())


if __name__ == "__main__":
    run_async_tests()
