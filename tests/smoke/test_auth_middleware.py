import os
import sys
import pytest
from unittest import mock

from httpx import AsyncClient, ASGITransport

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

with mock.patch("github_tracker_bot.ai_decide_commits.OpenAI") as mock_openai_client:
    from github_tracker_bot.bot import app


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_authentication_required():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/run-task")
        assert response.status_code == 401
        assert response.json()["message"] == "Unauthorized"
