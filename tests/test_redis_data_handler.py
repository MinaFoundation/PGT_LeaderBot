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

    @patch.object(RedisClient, 'get_user')
    def test_delete_user(self, mock_get_user):
        user_handle = "test_user"
        user_data = User(
            user_handle=user_handle,
            github_name="test_github",
            repositories=["repo1", "repo2"]
        )
        mock_get_user.return_value = user_data

        self.mock_redis.delete.return_value = user_data

        removed_data = self.redis_client.delete_user(user_handle)

        self.mock_redis.delete.assert_called_once_with(f"user:{user_handle}")
        self.assertEqual(removed_data, user_data)

    @patch.object(RedisClient, 'get_user')
    def test_delete_nonexists_user(self, mock_get_user):
        user_handle = "nonexistent_user"
        mock_get_user.return_value = None

        self.mock_redis.delete.return_value = None

        removed_data = self.redis_client.delete_user(user_handle)

        self.mock_redis.delete.assert_called_once_with(f"user:{user_handle}")
        self.assertIsNone(removed_data)



if __name__ == "__main__":
    unittest.main()
