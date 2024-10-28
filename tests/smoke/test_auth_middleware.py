import os
import sys
from fastapi.testclient import TestClient
import pytest
from unittest import mock

from httpx import AsyncClient, ASGITransport

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from github_tracker_bot.bot import app

client = TestClient(app)


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_authentication_required():
    response = await client.post("/run-task")
    assert response.status_code == 401
    assert response.json()["message"] == "Unauthorized"
