import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport
from unittest import mock

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

with mock.patch("github_tracker_bot.ai_decide_commits.OpenAI") as mock_openai_client:
    from github_tracker_bot.bot import app


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_app_startup():
    transport = ASGITransport(app=app)
    shared_secret = os.environ.get("SHARED_SECRET")
    headers = {"Authorization": f"Bearer {shared_secret}"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/non-existing-endpoint", headers=headers)
        assert response.status_code == 401


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_app_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}
