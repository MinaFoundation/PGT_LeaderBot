import asyncio
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import config
import github_tracker_bot.bot as bot

client = TestClient(bot.app)


class TestGithubTrackerBot(unittest.TestCase):

    @patch("github_tracker_bot.bot.get_dates_for_today")
    @patch(
        "github_tracker_bot.bot.get_all_results_from_sheet_by_date",
        new_callable=AsyncMock,
    )
    def test_run_scheduled_task(self, mock_get_results, mock_get_dates):
        mock_get_dates.return_value = (
            "2023-01-01T00:00:00+00:00",
            "2023-01-02T00:00:00+00:00",
        )
        mock_get_results.return_value = None

        asyncio.run(bot.run_scheduled_task())
        mock_get_results.assert_awaited_once()

    @patch("github_tracker_bot.bot.scheduler", new_callable=AsyncMock)
    def test_control_scheduler_start(self, mock_scheduler):
        headers = {"Authorization": config.SHARED_SECRET}

        response = client.post(
            "/control-scheduler", json={"action": "start"}, headers=headers
        )
        self.assertEqual(response.status_code, 200)

    @patch("github_tracker_bot.bot.scheduler", new_callable=AsyncMock)
    def test_control_scheduler_stop(self, mock_scheduler):
        headers = {"Authorization": config.SHARED_SECRET}

        response = client.post(
            "/control-scheduler", json={"action": "stop"}, headers=headers
        )
        self.assertEqual(response.status_code, 200)

    @patch(
        "github_tracker_bot.bot.get_all_results_from_sheet_by_date",
        new_callable=AsyncMock,
    )
    def test_run_task(self, mock_get_results):
        mock_get_results.return_value = None
        # Add the correct authorization token
        headers = {"Authorization": config.SHARED_SECRET}
        response = client.post(
            "/run-task",
            json={
                "since": "2023-01-01T00:00:00+00:00",
                "until": "2023-01-02T00:00:00+00:00",
            },
            headers=headers,  # Pass the headers with the token
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Task run successfully with provided times", response.json().get("message")
        )
        mock_get_results.assert_awaited_once()

    def test_validate_datetime(self):
        with self.assertRaises(ValueError):
            bot.TaskTimeFrame(since="invalid-date", until="2023-01-02T00:00:00+00:00")
        with self.assertRaises(ValueError):
            bot.TaskTimeFrame(since="2023-01-01T00:00:00+00:00", until="invalid-date")
        with self.assertRaises(ValueError):
            bot.TaskTimeFrame(
                since="2023-02-29T00:00:00+00:00", until="2023-01-02T00:00:00+00:00"
            )


if __name__ == "__main__":
    unittest.main()
