import unittest
from unittest.mock import patch, MagicMock
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
        user = User(
            user_handle="test_user",
            github_name="test_github",
            repositories=["repo1", "repo2"],
        )
        self.mock_redis.set.return_value = True
        result = self.redis_client.create_user(user)
        self.mock_redis.set.assert_called_once_with(
            f"user:{user.user_handle}", user.to_dict()
        )
        self.assertEqual(result, user)

    def test_create_user_invalid(self):
        user = User(
            user_handle="test_user",
            github_name="test_github",
            repositories="not_a_list",
        )
        with self.assertRaises(ValueError):
            self.redis_client.create_user(user)

    # GET CASES
    def test_get_user_exists(self):
        user_data = {
            "user_handle": "test_user",
            "github_name": "test_github",
            "repositories": ["repo1", "repo2"],
        }
        self.mock_redis.get.return_value = user_data
        result = self.redis_client.get_user("test_user")
        self.mock_redis.get.assert_called_once_with("user:test_user")
        self.assertEqual(result.user_handle, "test_user")

    def test_get_user_not_exists(self):
        self.mock_redis.get.return_value = None
        result = self.redis_client.get_user("nonexistent_user")
        self.mock_redis.get.assert_called_once_with("user:nonexistent_user")
        self.assertIsNone(result)

    # UPDATE CASES
    def test_update_user_exists_valid_data(self):
        user = User(
            user_handle="test_user",
            github_name="new_github",
            repositories=["repo1", "repo2"],
        )
        self.mock_redis.exists.return_value = True
        self.mock_redis.set.return_value = True
        result = self.redis_client.update_user(user)
        self.mock_redis.set.assert_called_once_with(
            f"user:{user.user_handle}", user.to_dict()
        )
        self.assertEqual(result, user)

    def test_update_user_exists_invalid_data(self):
        user = User(
            user_handle="test_user", github_name="new_github", repositories="not_a_list"
        )
        with self.assertRaises(ValueError):
            self.redis_client.update_user(user)

    def test_update_user_nonexists(self):
        user = User(
            user_handle="test_user",
            github_name="new_github",
            repositories=["repo1", "repo2"],
        )
        self.mock_redis.exists.return_value = False
        with self.assertRaises(KeyError):
            self.redis_client.update_user(user)

    def test_update_user_handle(self):
        user_handle = "old_handle"
        updated_user_handle = "new_handle"
        user_data = {
            "user_handle": user_handle,
            "github_name": "test_github",
            "repositories": ["repo1", "repo2"],
        }
        self.mock_redis.exists.side_effect = [True, False]
        self.mock_redis.get.return_value = user_data
        self.mock_redis.set.return_value = True
        result = self.redis_client.update_user_handle(user_handle, updated_user_handle)
        self.mock_redis.get.assert_called_once_with(f"user:{user_handle}")
        self.mock_redis.set.assert_called_once_with(
            f"user:{updated_user_handle}", user_data
        )
        self.assertEqual(result.user_handle, updated_user_handle)

    def test_update_github_name(self):
        user_handle = "test_user"
        update_github_name = "new_github"
        user_data = {
            "user_handle": user_handle,
            "github_name": "old_github",
            "repositories": ["repo1", "repo2"],
        }
        self.mock_redis.exists.return_value = True
        self.mock_redis.get.return_value = user_data
        self.mock_redis.set.return_value = True
        result = self.redis_client.update_github_name(user_handle, update_github_name)
        updated_user_data = user_data.copy()
        updated_user_data["github_name"] = update_github_name
        self.mock_redis.set.assert_called_once_with(
            f"user:{user_handle}", updated_user_data
        )
        self.assertEqual(result.github_name, update_github_name)

    def test_update_repositories(self):
        user_handle = "test_user"
        repositories = ["repo1", "repo3"]
        user_data = {
            "user_handle": user_handle,
            "github_name": "test_github",
            "repositories": ["repo1", "repo2"],
        }
        self.mock_redis.exists.return_value = True
        self.mock_redis.get.return_value = user_data
        self.mock_redis.set.return_value = True
        result = self.redis_client.update_repositories(user_handle, repositories)
        updated_user_data = user_data.copy()
        updated_user_data["repositories"] = repositories
        self.mock_redis.set.assert_called_once_with(
            f"user:{user_handle}", updated_user_data
        )
        self.assertEqual(result.repositories, repositories)

    # DELETE CASES
    def test_delete_user(self):
        user_handle = "test_user"
        self.mock_redis.delete.return_value = True
        result = self.redis_client.delete_user(user_handle)
        self.mock_redis.delete.assert_called_once_with(f"user:{user_handle}")
        self.assertTrue(result)

    def test_delete_nonexists_user(self):
        user_handle = "nonexistent_user"
        self.mock_redis.delete.return_value = False
        result = self.redis_client.delete_user(user_handle)
        self.mock_redis.delete.assert_called_once_with(f"user:{user_handle}")
        self.assertFalse(result)

    # AI DECISIONS CASES
    def test_get_ai_decisions_by_user(self):
        user_handle = "test_user"
        ai_decisions = [
            [
                {
                    "username": "berkingurcan",
                    "repository": "https://github.com/UmstadAI/zkAppUmstad/",
                    "date": "2024-05-02",
                    "response": {
                        "username": "berkingurcan",
                        "date": "2024-05-02",
                        "is_qualified": "True",
                        "explanation": "The commits made on this day include significant updates to the Discord API route and the prompts used by the bot. The changes enhance the functionality and user experience of the bot by refining its capabilities and instructions. The updates are well-structured and demonstrate thoughtful consideration of the bot's behavior. Additionally, the change from 'gpt-4-1106-preview' to 'gpt-4-turbo' in the model indicates an improvement in performance. Overall, these contributions are meaningful and impactful, qualifying the day's commits.",
                    },
                },
                {
                    "username": "berkingurcan",
                    "repository": "https://github.com/UmstadAI/zkAppUmstad/",
                    "date": "2024-05-17",
                    "response": {
                        "username": "berkingurcan",
                        "date": "2024-05-17",
                        "is_qualified": "True",
                        "explanation": "The commits made on this day include significant contributions such as adding a demo searcher API and tools, updating prompts with new features, and improving the formatting of search results. The changes are well-structured and demonstrate thoughtful consideration, particularly in the 'feat add format demosearch query results' and 'feat add search tool and update prompt' commits, which enhance functionality and user experience. Despite some minor commits, the overall impact of the contributions is substantial, qualifying the day's work.",
                    },
                },
            ],
            [
                {
                    "username": "berkingurcan",
                    "repository": "https://github.com/UmstadAI/discord-umstad",
                    "date": "2024-05-02",
                    "response": {
                        "username": "berkingurcan",
                        "date": "2024-05-02",
                        "is_qualified": "True",
                        "explanation": "The commit introduces a new variable 'IS_THREAD_PROCESSOR_DONE' and modifies the logic in 'handle_thread_create' to conditionally execute the POST request based on this variable. This change demonstrates significant effort in improving error handling and control flow in the code, which contributes meaningfully to the functionality of the application.",
                    },
                },
                {
                    "username": "berkingurcan",
                    "repository": "https://github.com/UmstadAI/discord-umstad",
                    "date": "2024-05-13",
                    "response": {
                        "username": "berkingurcan",
                        "date": "2024-05-13",
                        "is_qualified": "False",
                        "explanation": "The first commit does not contain any diff, which means it does not contribute any meaningful change. The second commit updates 'bot.py' but only adds comments without any functional changes or significant improvements to the code. Therefore, there are no qualified commits that add value to the codebase.",
                    },
                },
            ],
        ]
        self.mock_redis.get.return_value = ai_decisions
        result = self.redis_client.get_ai_decisions_by_user(user_handle)
        self.mock_redis.get.assert_called_once_with(f"ai_decisions:{user_handle}")
        self.assertEqual(result[0].username, "test_user")

    def test_get_ai_decisions_by_user_and_daterange(self):
        pass

    def test_add_ai_decisions_by_user(self):
        user_handle = "test_user"
        ai_decisions = [
            AIDecision(
                username="test_user",
                repository="repo1",
                date="2023-07-21",
                response=DailyContributionResponse(
                    username="test_user",
                    date="2023-07-21",
                    is_qualified="True",
                    explanation="valid",
                ),
            )
        ]
        self.mock_redis.set.return_value = True
        result = self.redis_client.add_ai_decisions_by_user(user_handle, ai_decisions)
        self.mock_redis.set.assert_called_once_with(
            f"ai_decisions:{user_handle}",
            [decision.to_dict() for decision in ai_decisions],
        )
        self.assertTrue(result)

    # CONTRIBUTION DATA CASES
    def test_get_total_daily_contribution_number(self):
        user_handle = "test_user"
        self.mock_redis.get.return_value = 10
        result = self.redis_client.get_total_daily_contribution_number(user_handle)
        self.mock_redis.get.assert_called_once_with(
            f"total_daily_contribution:{user_handle}"
        )
        self.assertEqual(result, 10)

    def test_set_total_daily_contribution_number(self):
        user_handle = "test_user"
        updated_number = 20
        self.mock_redis.set.return_value = True
        result = self.redis_client.set_total_daily_contribution_number(
            user_handle, updated_number
        )
        self.mock_redis.set.assert_called_once_with(
            f"total_daily_contribution:{user_handle}", updated_number
        )
        self.assertTrue(result)

    def test_get_total_qualified_daily_contribution_number(self):
        user_handle = "test_user"
        self.mock_redis.get.return_value = 15
        result = self.redis_client.get_total_qualified_daily_contribution_number(
            user_handle
        )
        self.mock_redis.get.assert_called_once_with(
            f"total_qualified_daily_contribution:{user_handle}"
        )
        self.assertEqual(result, 15)

    def test_set_total_qualified_daily_contribution_number(self):
        user_handle = "test_user"
        updated_number = 25
        self.mock_redis.set.return_value = True
        result = self.redis_client.set_total_qualified_daily_contribution_number(
            user_handle, updated_number
        )
        self.mock_redis.set.assert_called_once_with(
            f"total_qualified_daily_contribution:{user_handle}", updated_number
        )
        self.assertTrue(result)

    def test_get_qualified_daily_contribution_number_by_month(self):
        user_handle = "test_user"
        self.mock_redis.get.return_value = {"2023-07": 5}
        result = self.redis_client.get_qualified_daily_contribution_number_by_month(
            user_handle
        )
        self.mock_redis.get.assert_called_once_with(
            f"qualified_daily_contribution_by_month:{user_handle}"
        )
        self.assertEqual(result, {"2023-07": 5})

    def test_set_qualified_daily_contribution_number_by_month(self):
        user_handle = "test_user"
        month = "2023-07"
        number = 7
        self.mock_redis.set.return_value = True
        result = self.redis_client.set_qualified_daily_contribution_number_by_month(
            user_handle, month, number
        )
        self.mock_redis.set.assert_called_once_with(
            f"qualified_daily_contribution_by_month:{user_handle}:{month}", number
        )
        self.assertTrue(result)

    def test_get_qualified_daily_contribution_dates(self):
        user_handle = "test_user"
        self.mock_redis.get.return_value = ["2023-07-01", "2023-07-02"]
        result = self.redis_client.get_qualified_daily_contribution_dates(user_handle)
        self.mock_redis.get.assert_called_once_with(
            f"qualified_daily_contribution_dates:{user_handle}"
        )
        self.assertEqual(result, ["2023-07-01", "2023-07-02"])

    def test_set_qualified_daily_contribution_dates(self):
        user_handle = "test_user"
        list_of_dates = ["2023-07-01", "2023-07-02"]
        self.mock_redis.set.return_value = True
        result = self.redis_client.set_qualified_daily_contribution_dates(
            user_handle, list_of_dates
        )
        self.mock_redis.set.assert_called_once_with(
            f"qualified_daily_contribution_dates:{user_handle}", list_of_dates
        )
        self.assertTrue(result)

    def test_get_qualified_daily_contribution_streak(self):
        user_handle = "test_user"
        self.mock_redis.get.return_value = 5
        result = self.redis_client.get_qualified_daily_contribution_streak(user_handle)
        self.mock_redis.get.assert_called_once_with(
            f"qualified_daily_contribution_streak:{user_handle}"
        )
        self.assertEqual(result, 5)

    def test_set_qualified_daily_contribution_streak(self):
        user_handle = "test_user"
        updated_number = 6
        self.mock_redis.set.return_value = True
        result = self.redis_client.set_qualified_daily_contribution_streak(
            user_handle, updated_number
        )
        self.mock_redis.set.assert_called_once_with(
            f"qualified_daily_contribution_streak:{user_handle}", updated_number
        )
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
