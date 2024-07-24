import asyncio
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import github_tracker_bot.bot as bot

client = TestClient(bot.app)


class TestGithubTrackerBot(unittest.TestCase):

    @patch("github_tracker_bot.bot.get_dates_for_today")
    @patch("github_tracker_bot.bot.get_all_results_from_sheet_by_date", new_callable=AsyncMock)
    def test_run_scheduled_task(self, mock_get_results, mock_get_dates):
        mock_get_dates.return_value = (
            "2023-01-01T00:00:00+00:00",
            "2023-01-02T00:00:00+00:00",
        )
        mock_get_results.return_value = None

        asyncio.run(bot.run_scheduled_task())
        mock_get_results.assert_awaited_once()

    def test_get_dates_for_today(self):
        since_date, until_date = bot.get_dates_for_today()
        today = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        expected_until_date = today + timedelta(days=1)

        self.assertEqual(since_date, today.isoformat())
        self.assertEqual(until_date, expected_until_date.isoformat())

    @patch("github_tracker_bot.bot.scheduler", new_callable=AsyncMock)
    def test_control_scheduler_start(self, mock_scheduler):
        response = client.post(
            "/control-scheduler", json={"action": "start", "interval_minutes": 5}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Scheduler started with interval of 5 minutes",
            response.json().get("message"),
        )

    @patch("github_tracker_bot.bot.scheduler", new_callable=AsyncMock)
    def test_control_scheduler_stop(self, mock_scheduler):
        response = client.post("/control-scheduler", json={"action": "stop"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Scheduler stopped", response.json().get("message"))

    @patch("github_tracker_bot.bot.get_all_results_from_sheet_by_date", new_callable=AsyncMock)
    def test_run_task(self, mock_get_results):
        mock_get_results.return_value = None
        response = client.post(
            "/run-task",
            json={
                "since": "2023-01-01T00:00:00+00:00",
                "until": "2023-01-02T00:00:00+00:00",
            },
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
            bot.TaskTimeFrame(since="2023-02-29T00:00:00+00:00", until="2023-01-02T00:00:00+00:00")

    def test_scheduler(self):
        with patch("aioschedule.every") as mock_every, patch(
            "github_tracker_bot.bot.run_scheduled_task", new_callable=AsyncMock
        ) as mock_run_task:
            mock_job = MagicMock()
            mock_every.return_value.minutes.do.return_value = mock_job

            async def run_scheduler():
                schedule_task = asyncio.create_task(bot.scheduler(1))
                await asyncio.sleep(0.1)
                schedule_task.cancel()

            asyncio.run(run_scheduler())
            mock_every.return_value.minutes.do.assert_called_once_with(
                bot.run_scheduled_task
            )
            mock_run_task.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
