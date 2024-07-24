import unittest
from fastapi.testclient import TestClient

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

import github_tracker_bot.bot as bot


client = TestClient(bot.app)

class TestIntegration(unittest.TestCase):
    
    def test_run_task_endpoint(self):
        response = client.post("/run-task", json={"since": "2023-01-01T00:00:00+00:00", "until": "2023-01-02T00:00:00+00:00"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Task run successfully with provided times", response.json().get("message"))

    def test_control_scheduler_start_endpoint(self):
        response = client.post("/control-scheduler", json={"action": "start", "interval_minutes": 5})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Scheduler started with interval of 5 minutes", response.json().get("message"))

    def test_control_scheduler_stop_endpoint(self):
        response = client.post("/control-scheduler", json={"action": "stop"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Scheduler stopped", response.json().get("message"))

if __name__ == '__main__':
    unittest.main()
