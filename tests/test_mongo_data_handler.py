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
        self.assertEqual(user.user_handle, "test_handle")

    def test_get_user_not_exists(self):
        user = self.mongo_handler.get_user("nonexistent_handle")
        self.assertIsNone(user)

    # UPDATE CASES
    def test_update_user_exists_valid_data(self):
        self.mongo_handler.create_user(self.test_user)

        result = self.mongo_handler.update_user(
            self.test_user.user_handle, self.test_update_user
        )
        self.assertTrue(result)

        updated_user = self.mongo_handler.get_user("updated_handle")
        self.assertEqual(updated_user.github_name, self.test_update_user.github_name)

    def test_update_user_exists_invalid_data(self):
        self.mongo_handler.create_user(self.test_user)
        self.test_user.repositories = ""
        with self.assertRaises(ValueError):
            self.mongo_handler.update_user(self.test_user.user_handle, self.test_user)

    def test_update_user_nonexists(self):
        non_existing_user = User(
            user_handle="nonexistent_handle",
            github_name="test_github",
            repositories=["repo1", "repo2"],
        )

        result = self.mongo_handler.update_user(
            non_existing_user.user_handle, non_existing_user
        )
        self.assertFalse(result)

    def test_update_user_handle(self):
        self.mongo_handler.create_user(self.test_user)
        new_handle = "new_handle"
        result = self.mongo_handler.update_field(
            "test_handle", "user_handle", new_handle
        )

        self.assertTrue(result)
        updated_user = self.mongo_handler.get_user(new_handle)

        self.assertIsNotNone(updated_user)
        self.assertEqual(updated_user.user_handle, new_handle)

    def test_update_github_name(self):
        self.mongo_handler.create_user(self.test_user)
        new_github_name = "new_github"

        result = self.mongo_handler.update_field(
            "test_handle", "github_name", new_github_name
        )
        self.assertTrue(result)

        updated_user = self.mongo_handler.get_user("test_handle")
        self.assertEqual(updated_user.github_name, new_github_name)

    def test_update_repositories(self):
        self.mongo_handler.create_user(self.test_user)
        new_repositories = ["new_repo1", "new_repo2"]
        result = self.mongo_handler.update_field(
            "test_handle", "repositories", new_repositories
        )
        self.assertTrue(result)
        updated_user = self.mongo_handler.get_user("test_handle")
        self.assertEqual(updated_user.repositories, new_repositories)

    # DELETE CASES
    def test_delete_user(self):
        self.mongo_handler.create_user(self.test_user)
        result = self.mongo_handler.delete_user("test_handle")

        self.assertTrue(result)
        self.assertIsNone(self.collection.find_one({"user_handle": "test_handle"}))

    def test_delete_nonexists_user(self):
        result = self.mongo_handler.delete_user("nonexistent_handle")
        self.assertFalse(result)

    # AI DECISIONS CASES
    def test_get_ai_decisions_by_user(self):
        self.mongo_handler.create_user(self.test_user)
        ai_decisions = [
            AIDecision(
                username="test_handle",
                repository="repo1",
                date="2023-07-21",
                response=DailyContributionResponse(
                    username="test_handle",
                    date="2023-07-21",
                    is_qualified=True,
                    explanation="Valid contribution",
                ),
            ),
            AIDecision(
                username="test_handle",
                repository="repo1",
                date="2023-07-22",
                response=DailyContributionResponse(
                    username="test_handle",
                    date="2023-07-22",
                    is_qualified=False,
                    explanation="InValid contribution",
                ),
            ),
        ]
        self.mongo_handler.add_ai_decisions_by_user("test_handle", ai_decisions)
        decisions = self.mongo_handler.get_ai_decisions_by_user("test_handle")
        self.assertEqual(len(decisions[0]), 2)
        self.assertEqual(decisions[0][0].response.is_qualified, True)

        user = self.mongo_handler.get_user("test_handle")
        self.assertIsInstance(user, User)

    def test_get_ai_decisions_by_user_and_daterange(self):
        self.mongo_handler.create_user(self.test_user)

        ai_decisions_1 = [
            AIDecision(
                username="test_handle",
                repository="repo1",
                date="2023-07-20",
                response=DailyContributionResponse(
                    username="test_handle",
                    date="2023-07-20",
                    is_qualified=True,
                    explanation="Valid contribution",
                ),
            ),
            AIDecision(
                username="test_handle",
                repository="repo1",
                date="2023-07-23",
                response=DailyContributionResponse(
                    username="test_handle",
                    date="2023-07-23",
                    is_qualified=True,
                    explanation="Valid contribution",
                ),
            ),
        ]
        ai_decisions_2 = [
            AIDecision(
                username="test_handle",
                repository="repo1",
                date="2023-07-21",
                response=DailyContributionResponse(
                    username="test_handle",
                    date="2023-07-21",
                    is_qualified=True,
                    explanation="Valid contribution",
                ),
            ),
            AIDecision(
                username="test_handle",
                repository="repo2",
                date="2023-07-22",
                response=DailyContributionResponse(
                    username="test_handle",
                    date="2023-07-22",
                    is_qualified=True,
                    explanation="Valid contribution",
                ),
            ),
        ]
        self.mongo_handler.add_ai_decisions_by_user("test_handle", ai_decisions_1)
        self.mongo_handler.add_ai_decisions_by_user("test_handle", ai_decisions_2)

        decisions_frame_1 = self.mongo_handler.get_ai_decisions_by_user_and_daterange(
            "test_handle", "2023-07-19", "2023-07-21"
        )
        length_of_decision_frame_1 = sum(len(sublist) for sublist in decisions_frame_1)
        self.assertEqual(length_of_decision_frame_1, 2)

        decisions_frame_2 = self.mongo_handler.get_ai_decisions_by_user_and_daterange(
            "test_handle", "2023-07-19", "2024-07-21"
        )
        length_of_decision_frame_2 = sum(len(sublist) for sublist in decisions_frame_2)
        self.assertEqual(length_of_decision_frame_2, 4)

    def test_add_ai_decisions_by_user(self):
        self.mongo_handler.create_user(self.test_user)
        ai_decisions = [
            AIDecision(
                username="test_handle",
                repository="repo1",
                date="2023-07-21",
                response=DailyContributionResponse(
                    username="test_handle",
                    date="2023-07-21",
                    is_qualified=True,
                    explanation="Valid contribution",
                ),
            )
        ]
        result = self.mongo_handler.add_ai_decisions_by_user(
            "test_handle", ai_decisions
        )
        self.assertTrue(result)

        user = self.mongo_handler.get_user("test_handle")

        self.assertEqual(len(user.ai_decisions), 1)
        self.assertEqual(user, result)

    # CONTRIBUTION DATA CASES
    def test_update_all_contribution_datas_from_ai_decisions(self):
        self.mongo_handler.create_user(self.test_user)

        ai_decisions_1 = [
            AIDecision(
                username="test_handle",
                repository="repo1",
                date="2023-07-20",
                response=DailyContributionResponse(
                    username="test_handle",
                    date="2023-07-20",
                    is_qualified=True,
                    explanation="Valid contribution",
                ),
            ),
            AIDecision(
                username="test_handle",
                repository="repo1",
                date="2023-07-23",
                response=DailyContributionResponse(
                    username="test_handle",
                    date="2023-07-23",
                    is_qualified=False,
                    explanation="Valid contribution",
                ),
            ),
        ]
        ai_decisions_2 = [
            AIDecision(
                username="test_handle",
                repository="repo1",
                date="2023-07-21",
                response=DailyContributionResponse(
                    username="test_handle",
                    date="2023-07-21",
                    is_qualified=True,
                    explanation="Valid contribution",
                ),
            ),
            AIDecision(
                username="test_handle",
                repository="repo2",
                date="2023-07-22",
                response=DailyContributionResponse(
                    username="test_handle",
                    date="2023-07-22",
                    is_qualified=True,
                    explanation="Valid contribution",
                ),
            ),
        ]
        self.mongo_handler.add_ai_decisions_by_user("test_handle", ai_decisions_1)
        self.mongo_handler.add_ai_decisions_by_user("test_handle", ai_decisions_2)

        with patch(
            "leader_bot.sheet_functions.get_repositories_from_user"
        ) as mock_get_repos:
            mock_get_repos.return_value = []
            self.mongo_handler.update_all_contribution_datas_from_ai_decisions(
                "test_handle"
            )

        user = self.mongo_handler.get_user("test_handle")

        self.assertEqual(user.total_daily_contribution_number, 4)
        self.assertEqual(user.total_qualified_daily_contribution_number, 3)

    def test_update_case_1(self):
        user = User(
            user_handle="mario_zito",
            github_name="mazito",
            repositories=[
                "https://github.com/zkcloudworker/zkcloudworker-aws",
                "https://github.com/Identicon-Dao/socialcap",
            ],
            ai_decisions=[
                [
                    AIDecision(
                        username="mazito",
                        repository="https://github.com/Identicon-Dao/socialcap",
                        date="2024-05-13",
                        response=DailyContributionResponse(
                            username="mazito",
                            date="2024-05-13",
                            is_qualified=True,
                            explanation="The commit adds a new feature by introducing a 'payedBy' field to the Masterplan, which enhances the functionality of the application. This change is meaningful and contributes to the overall user experience. The code is well-structured and follows coding standards, making it a qualified commit.",
                        ),
                    ),
                    AIDecision(
                        username="mazito",
                        repository="https://github.com/Identicon-Dao/socialcap",
                        date="2024-05-16",
                        response=DailyContributionResponse(
                            username="mazito",
                            date="2024-05-16",
                            is_qualified=True,
                            explanation="The first commit introduces a significant change by adding authentication checks in the load function, which enhances the security and functionality of the application. The code is well-structured and follows coding standards. Although the subsequent commits are merge commits, they do not detract from the overall impact of the first commit. Therefore, the total contributions for the day are qualified.",
                        ),
                    ),
                ]
            ],
            total_daily_contribution_number=2,
            total_qualified_daily_contribution_number=2,
            qualified_daily_contribution_number_by_month={"2024-05": 2},
            qualified_daily_contribution_dates={"2024-05-13", "2024-05-16"},
            qualified_daily_contribution_streak=1,
        )
        self.mongo_handler.create_user(user)
        r = self.mongo_handler.update_all_contribution_datas_from_ai_decisions(
            "mario_zito"
        )

        pass

    def test_get_total_daily_contribution_number(self):
        self.mongo_handler.create_user(self.test_user)
        self.mongo_handler.update_field(
            self.test_user.user_handle, "total_daily_contribution_number", 5
        )

        total = self.mongo_handler.get_total_daily_contribution_number("test_handle")
        self.assertEqual(total, 5)

    def test_set_total_daily_contribution_number(self):
        self.mongo_handler.create_user(self.test_user)

        result = self.mongo_handler.set_total_daily_contribution_number(
            "test_handle", 10
        )
        self.assertTrue(result)

        user = self.mongo_handler.get_user("test_handle")
        self.assertEqual(user.total_daily_contribution_number, 10)

    def test_get_total_qualified_daily_contribution_number(self):
        self.mongo_handler.create_user(self.test_user)
        self.mongo_handler.update_field(
            self.test_user.user_handle, "total_qualified_daily_contribution_number", 3
        )

        total = self.mongo_handler.get_total_qualified_daily_contribution_number(
            "test_handle"
        )
        self.assertEqual(total, 3)

    def test_set_total_qualified_daily_contribution_number(self):
        self.mongo_handler.create_user(self.test_user)

        result = self.mongo_handler.set_total_qualified_daily_contribution_number(
            "test_handle", 10
        )
        self.assertTrue(result)

        user = self.mongo_handler.get_user("test_handle")
        self.assertEqual(user.total_qualified_daily_contribution_number, 10)

    def test_get_qualified_daily_contribution_number_by_month(self):
        self.mongo_handler.create_user(self.test_user)
        contributions_by_month = {
            "2023-07": 5,
            "2023-08": 7,
        }
        self.mongo_handler.update_field(
            self.test_user.user_handle,
            "qualified_daily_contribution_number_by_month",
            contributions_by_month,
        )

        result = self.mongo_handler.get_qualified_daily_contribution_number_by_month(
            "test_handle"
        )
        self.assertEqual(result, contributions_by_month)

    def test_set_qualified_daily_contribution_number_by_month(self):
        self.mongo_handler.create_user(self.test_user)
        contributions_by_month = {
            "2023-07": 5,
            "2023-08": 7,
        }

        result = self.mongo_handler.set_qualified_daily_contribution_number_by_month(
            "test_handle", contributions_by_month
        )
        self.assertTrue(result)

        user = self.mongo_handler.get_user("test_handle")
        self.assertEqual(
            user.qualified_daily_contribution_number_by_month, contributions_by_month
        )

    def test_add_qualified_daily_contribution_number_by_month(self):
        self.mongo_handler.create_user(self.test_user)
        contributions_by_month = {
            "2023-07": 5,
            "2023-08": 7,
        }
        self.mongo_handler.update_field(
            self.test_user.user_handle,
            "qualified_daily_contribution_number_by_month",
            contributions_by_month,
        )

        self.mongo_handler.add_qualified_daily_contribution_number_by_month(
            "test_handle", "2023", "09", 10
        )

        user = self.mongo_handler.get_user("test_handle")
        expected_contributions_by_month = {
            "2023-07": 5,
            "2023-08": 7,
            "2023-09": 10,
        }
        self.assertEqual(
            user.qualified_daily_contribution_number_by_month,
            expected_contributions_by_month,
        )

        self.mongo_handler.add_qualified_daily_contribution_number_by_month(
            "test_handle", "2023", "08", 15
        )

        expected_contributions_by_month["2023-08"] = 15
        user = self.mongo_handler.get_user("test_handle")
        self.assertEqual(
            user.qualified_daily_contribution_number_by_month,
            expected_contributions_by_month,
        )

    def test_get_qualified_daily_contribution_dates(self):
        self.mongo_handler.create_user(self.test_user)
        self.test_user.qualified_daily_contribution_dates = {
            "2023-07-21": 1,
            "2024-07-11": 1,
        }
        self.mongo_handler.update_field(
            self.test_user.user_handle,
            "qualified_daily_contribution_dates",
            self.test_user.qualified_daily_contribution_dates,
        )

        dates = self.mongo_handler.get_qualified_daily_contribution_dates("test_handle")
        self.assertEqual(set(dates), {"2023-07-21", "2024-07-11"})

    def test_set_qualified_daily_contribution_dates(self):
        self.mongo_handler.create_user(self.test_user)
        contribution_dates = ["2023-07-01", "2023-07-02", "2023-07-03"]

        result = self.mongo_handler.set_qualified_daily_contribution_dates(
            "test_handle", contribution_dates
        )
        self.assertTrue(result)

        user = self.mongo_handler.get_user("test_handle")
        self.assertEqual(
            user.qualified_daily_contribution_dates, set(contribution_dates)
        )

    def test_add_qualified_daily_contribution_dates(self):
        self.mongo_handler.create_user(self.test_user)

        initial_dates = ["2023-07-01", "2023-07-02"]
        self.mongo_handler.set_qualified_daily_contribution_dates(
            self.test_user.user_handle, initial_dates
        )

        new_dates = ["2023-07-03", "2023-07-04"]
        result = self.mongo_handler.add_qualified_daily_contribution_dates(
            self.test_user.user_handle, new_dates
        )
        self.assertTrue(result)

        expected_dates = set(initial_dates + new_dates)
        user = self.mongo_handler.get_user(self.test_user.user_handle)
        self.assertEqual(set(user.qualified_daily_contribution_dates), expected_dates)

    def test_add_qualified_daily_contribution_dates_from_zero(self):
        self.mongo_handler.create_user(self.test_user)

        new_dates = ["2023-07-03", "2023-07-04"]
        result = self.mongo_handler.add_qualified_daily_contribution_dates(
            self.test_user.user_handle, new_dates
        )
        self.assertTrue(result)

        expected_dates = set(new_dates)
        user = self.mongo_handler.get_user(self.test_user.user_handle)
        self.assertEqual(set(user.qualified_daily_contribution_dates), expected_dates)

    def test_get_qualified_daily_contribution_streak(self):
        self.mongo_handler.create_user(self.test_user)
        self.mongo_handler.update_field(
            self.test_user.user_handle, "qualified_daily_contribution_streak", 22
        )

        total = self.mongo_handler.get_qualified_daily_contribution_streak(
            "test_handle"
        )
        self.assertEqual(total, 22)

    def test_set_qualified_daily_contribution_streak(self):
        self.mongo_handler.create_user(self.test_user)

        result = self.mongo_handler.set_qualified_daily_contribution_streak(
            "test_handle", 24
        )
        self.assertTrue(result)

        user = self.mongo_handler.get_user("test_handle")
        self.assertEqual(user.qualified_daily_contribution_streak, 24)


if __name__ == "__main__":
    unittest.main()
