import sys
import os

import pytest
from httpx import AsyncClient, ASGITransport

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config

from github_tracker_bot.bot import app


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_app_startup():
    transport = ASGITransport(app=app)
    headers = {"Authorization": config.SHARED_SECRET}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/non-existing-endpoint", headers=headers)
        assert response.status_code == 404


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_app_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}
