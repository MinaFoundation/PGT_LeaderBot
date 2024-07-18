import unittest
from unittest.mock import patch, MagicMock

import json

from github_tracker_bot.redis_data_handler import (
    RedisClient,
    User,
    AIDecision,
    DailyContributionResponse,
)


class TestRedisClient(unittest.TestCase):

    @patch("github_tracker_bot.redis_data_handler.redis.Redis")
    def setUp(self, MockRedis):
        self.mock_redis = MockRedis.return_value
        self.redis_client = RedisClient()

    def test_save_user_valid(self):
        user = User(
            user_handle="test_user",
            github_name="test_github",
            repositories=["repo1", "repo2"],
        )
        self.redis_client.save_user(user)
        self.mock_redis.hset.assert_called_once_with(
            f"user:{user.user_handle}", user.__dict__
        )

    def test_save_user_invalid(self):
        user = User(
            user_handle="test_user",
            github_name="test_github",
            repositories="invalid_repos",
        )
        res = self.redis_client.save_user(user)
        self.assertEqual(res, None)

    def test_get_user_exists(self):
        user_handle = "test_user"
        user_data = {
            "user_handle": "test_user",
            "github_name": "test_github",
            "repositories": json.dumps(["repo1", "repo2"]),
            "total_daily_contribution_number": "0",
            "total_qualified_daily_contribution_number": "0",
            "qualified_daily_contribution_number_by_month": json.dumps({}),
            "qualified_daily_contribution_streak": "0",
        }
        self.mock_redis.hgetall.return_value = {
            k.encode(): v.encode() for k, v in user_data.items()
        }
        user = self.redis_client.get_user(user_handle)
        self.assertEqual(user.user_handle, user_handle)
        self.assertEqual(json.loads(user.repositories), ["repo1", "repo2"])

    def test_get_user_not_exists(self):
        self.mock_redis.hgetall.return_value = {}
        user = self.redis_client.get_user("nonexistent_user")
        self.assertIsNone(user)

    def test_save_decision(self):
        decision = AIDecision(
            username="test_user",
            repository="repo1",
            date="2024-01-01",
            response=DailyContributionResponse(
                username="test_user",
                date="2024-01-01",
                is_qualified=True,
                explanation="Good job",
            ),
        )
        self.redis_client.save_decision(decision)
        self.mock_redis.set.assert_called_once_with(
            f"decision:{decision.username}:{decision.date}",
            json.dumps(decision.to_dict()),
        )

    def test_get_decision_exists(self):
        decision_data = {
            "username": "test_user",
            "repository": "repo1",
            "date": "2024-01-01",
            "response": {
                "username": "test_user",
                "date": "2024-01-01",
                "is_qualified": True,
                "explanation": "Good job",
            },
        }
        self.mock_redis.get.return_value = json.dumps(decision_data)
        decision = self.redis_client.get_decision("test_user", "2024-01-01")
        self.assertEqual(decision.username, "test_user")
        self.assertEqual(decision.response.explanation, "Good job")

    def test_get_decision_not_exists(self):
        self.mock_redis.get.return_value = None
        decision = self.redis_client.get_decision("test_user", "2024-01-01")
        self.assertIsNone(decision)


if __name__ == "__main__":
    unittest.main()
