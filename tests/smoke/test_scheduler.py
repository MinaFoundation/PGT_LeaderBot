from fastapi.testclient import TestClient
import pytest
import os
import sys
from unittest import mock

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from github_tracker_bot.bot import app


@pytest.mark.smoke
def test_scheduler_exists():
    assert hasattr(app.state, "scheduler_task")
