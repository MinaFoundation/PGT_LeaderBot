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
        pass

    def test_save_user_invalid(self):
        pass

    def test_get_user_exists(self):
        pass

    def test_get_user_not_exists(self):
        pass

    def test_delete_user(self, mock_get_user):
        pass

    def test_delete_nonexists_user(self, mock_get_user):
        pass

    def test_get_ai_decisions_by_user(self):
        pass

    def test_get_ai_decisions_by_user_and_daterange(self):
        pass


if __name__ == "__main__":
    unittest.main()
