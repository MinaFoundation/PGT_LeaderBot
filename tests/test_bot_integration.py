import unittest
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from fastapi.testclient import TestClient

import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/../"))

import github_tracker_bot.bot as bot


client = TestClient(bot.app)

@pytest.mark.asyncio
class TestIntegration(unittest.TestCase):

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=bot.app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    @patch("github_tracker_bot.bot_functions.get_all_results_from_sheet_by_date", new_callable=AsyncMock)
    async def test_run_task(mock_get_all_results):
        async with AsyncClient(app=bot.app, base_url="http://test") as client:
            response = await client.post(
                "/run-task",
                json={
                    "since": "2023-10-01T00:00:00Z",
                    "until": "2023-10-02T00:00:00Z"
                },
                headers={"Authorization": "your_auth_token"}
            )
        assert response.status_code == 200
        assert response.json() == {"message": "Task run successfully with provided times"}
        mock_get_all_results.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("github_tracker_bot.bot_functions.get_user_results_from_sheet_by_date", new_callable=AsyncMock)
    async def test_run_task_for_user(mock_get_user_results):
        async with AsyncClient(app=bot.app, base_url="http://test") as client:
            response = await client.post(
                "/run-task-for-user?username=testuser",
                json={
                    "since": "2023-10-01T00:00:00Z",
                    "until": "2023-10-02T00:00:00Z"
                },
                headers={"Authorization": "your_auth_token"}
            )
        assert response.status_code == 200
        assert response.json() == {"message": "Task run successfully with provided times"}
        mock_get_user_results.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        async with AsyncClient(app=bot.app, base_url="http://test") as client:
            response = await client.post(
                "/run-task",
                json={
                    "since": "2023-10-01T00:00:00Z",
                    "until": "2023-10-02T00:00:00Z"
                }
                # No Authorization header
            )
        assert response.status_code == 401
        assert response.json() == {"message": "Unauthorized"}

    @pytest.mark.asyncio
    async def test_rate_limiting():
        async with AsyncClient(app=bot.app, base_url="http://test") as client:
            headers = {"Authorization": "your_auth_token"}
            for _ in range(10):
                response = await client.post(
                    "/run-task",
                    json={
                        "since": "2023-10-01T00:00:00Z",
                        "until": "2023-10-02T00:00:00Z"
                    },
                    headers=headers
                )
                assert response.status_code == 200

            # 11th request should be rate limited
            response = await client.post(
                "/run-task",
                json={
                    "since": "2023-10-01T00:00:00Z",
                    "until": "2023-10-02T00:00:00Z"
                },
                headers=headers
            )
            assert response.status_code == 429





if __name__ == "__main__":
    unittest.main()
