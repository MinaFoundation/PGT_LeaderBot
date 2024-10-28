from fastapi.testclient import TestClient
import pytest
import os
import sys
from unittest import mock

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

mock_env_vars = {
    "OPENAI_API_KEY": "mock_value",
    "MONGO_HOST": "mongodb://localhost:27017/",
    "MONGO_DB": "test_db",
    "MONGO_COLLECTION": "my_collection",
}

with mock.patch.dict(os.environ, mock_env_vars, clear=True):
    from github_tracker_bot.bot import app

    @pytest.mark.smoke
    def test_scheduler_exists():
        assert hasattr(app.state, "scheduler_task")
