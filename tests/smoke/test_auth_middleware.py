import os
import sys
import pytest

from httpx import AsyncClient, ASGITransport
from github_tracker_bot.bot import app

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
import config
import config

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_authentication_required():
    transport = ASGITransport(app=app)
    headers = {"Authorization": config.SHARED_SECRET}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/run-task")
        assert response.status_code == 401
        assert response.json()["message"] == "Unauthorized"

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_authentication_success():
    headers = {"Authorization": config.SHARED_SECRET}
    payload = {
        "since": "2023-01-01T00:00:00+00:00",
        "until": "2023-01-02T00:00:00+00:00"
    }
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as client:
        response = await client.post("/run-task", json=payload)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Task run successfully with provided times"
