import unittest
from unittest.mock import patch, MagicMock

import json
import pytest
import fakeredis

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

    # CREATE CASES
    def test_create_user_valid(self):
        pass

    def test_create_user_invalid(self):
        pass

    # GET CASES
    def test_get_user_exists(self):
        pass

    def test_get_user_not_exists(self):
        pass

    # UPDATE CASES
    def test_update_user_exists_valid_data(self):
        pass

    def test_update_user_exists_invalid_data(self):
        pass

    def test_update_user_nonexists(self):
        pass

    def test_update_user_handle(self):
        pass

    def test_update_github_name(self):
        pass

    def test_update_repositories(self):
        pass

    # DELETE CASES
    def test_delete_user(self):
        pass

    def test_delete_nonexists_user(self):
        pass

    # AI DECISIONS CASES
    def test_get_ai_decisions_by_user(self):
        pass

    def test_get_ai_decisions_by_user_and_daterange(self):
        pass

    def test_add_ai_decisions_by_user(self):
        pass

    # CONTRIBUTION DATA CASES
    def test_get_total_daily_contribution_number(self):
        pass

    def test_set_total_daily_contribution_number(self):
        pass

    def test_get_total_qualified_daily_contribution_number(self):
        pass

    def test_set_total_qualified_daily_contribution_number(self):
        pass

    def test_get_qualified_daily_contribution_number_by_month(self):
        pass

    def test_set_qualified_daily_contribution_number_by_month(self):
        pass

    def test_get_qualified_daily_contribution_dates(self):
        pass

    def test_set_qualified_daily_contribution_dates(self):
        pass

    def test_get_qualified_daily_contribution_streak(self):
        pass

    def test_set_qualified_daily_contribution_streak(self):
        pass


if __name__ == "__main__":
    unittest.main()
