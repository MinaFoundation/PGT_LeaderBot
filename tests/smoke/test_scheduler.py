import pytest
from github_tracker_bot.bot import app

@pytest.mark.smoke
def test_scheduler_exists():
    assert hasattr(app.state, "scheduler_task")