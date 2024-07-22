import json
import unittest
from unittest.mock import patch, MagicMock
import mongomock

from github_tracker_bot.mongo_data_handler import (
    MongoDBManagement,
    User,
    AIDecision,
    DailyContributionResponse,
)


class TestMongoDBManagement(unittest.TestCase):

    def setUp(self):
        self.client = mongomock.MongoClient()
        self.db = self.client.my_database
        self.collection = self.db.my_collection
        self.mongo_handler = MongoDBManagement(self.db, self.collection)
        self.test_user = User(
            user_handle="test_handle",
            github_name="test_github",
            repositories=["repo1", "repo2"],
        )

        self.test_update_user = User(
            user_handle="updated_handle",
            github_name="test_updated_github",
            repositories=["repo1", "repo3", "repo4"],
        )

    # CREATE CASES
    def test_create_user_valid(self):
        result = self.mongo_handler.create_user(self.test_user)

        self.assertTrue(result)
        self.assertIsNotNone(self.collection.find_one({"user_handle": "test_handle"}))

    def test_create_user_invalid(self):
        invalid_user = User(
            user_handle="", github_name="test_github", repositories="repo not list"
        )
        with self.assertRaises(ValueError):
            self.mongo_handler.create_user(invalid_user)

    # GET CASES
    def test_get_user_exists(self):
        self.mongo_handler.create_user(self.test_user)
        user = self.mongo_handler.get_user("test_handle")

        self.assertIsNotNone(user)
        self.assertEqual(user["user_handle"], "test_handle")

    def test_get_user_not_exists(self):
        user = self.mongo_handler.get_user("nonexistent_handle")
        self.assertIsNone(user)

    # UPDATE CASES
    def test_update_user_exists_valid_data(self):
        self.mongo_handler.create_user(self.test_user)

        result = self.mongo_handler.update_user(self.test_user.user_handle, self.test_update_user)
        self.assertTrue(result)

        updated_user = self.mongo_handler.get_user("updated_handle")
        self.assertEqual(updated_user["github_name"], self.test_update_user.github_name)

    def test_update_user_exists_invalid_data(self):
        self.mongo_handler.create_user(self.test_user)
        self.test_user.repositories = ""
        with self.assertRaises(ValueError):
            self.mongo_handler.update_user(self.test_user.user_handle, self.test_user)

    def test_update_user_nonexists(self):
        non_existing_user = User(
            user_handle="nonexistent_handle",
            github_name="test_github",
            repositories=["repo1", "repo2"]
        )

        result = self.mongo_handler.update_user(non_existing_user.user_handle, non_existing_user)
        self.assertFalse(result)

    def test_update_user_handle(self):
        self.mongo_handler.create_user(self.test_user)
        new_handle = "new_handle"
        result = self.mongo_handler.update_user_handle("test_handle", new_handle)

        self.assertTrue(result)
        updated_user = self.mongo_handler.get_user(new_handle)

        self.assertIsNotNone(updated_user)
        self.assertEqual(updated_user["user_handle"], new_handle)

    def test_update_github_name(self):
        self.mongo_handler.create_user(self.test_user)
        new_github_name = "new_github"

        result = self.mongo_handler.update_github_name("test_handle", new_github_name)
        self.assertTrue(result)
        
        updated_user = self.mongo_handler.get_user("test_handle")
        self.assertEqual(updated_user["github_name"], new_github_name)

    def test_update_repositories(self):
        self.mongo_handler.create_user(self.test_user)
        new_repositories = ["new_repo1", "new_repo2"]
        result = self.mongo_handler.update_repositories("test_handle", new_repositories)
        self.assertTrue(result)
        updated_user = self.mongo_handler.get_user("test_handle")
        self.assertEqual(updated_user["repositories"], new_repositories)

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
