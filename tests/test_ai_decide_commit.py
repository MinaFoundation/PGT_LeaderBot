import unittest
import config

import github_tracker_bot.ai_decide_commits as ai
from openai import AuthenticationError, NotFoundError, OpenAI, OpenAIError


class TestOpenAIIntegration(unittest.TestCase):
    def setUp(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def test_chat_completion_ok(self):
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"},
                ],
            )

            self.assertIsNotNone(completion)
            self.assertTrue(hasattr(completion, "choices"))
            self.assertGreater(len(completion.choices), 0)

            message_content = completion.choices[0].message.content
            self.assertIsInstance(message_content, str)
            self.assertGreater(len(message_content), 0)

        except OpenAIError as e:
            self.fail(f"OpenAI API call failed with error: {e}")

    def test_empty_user_input(self):
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": ""},
                ],
            )

            self.assertIsNotNone(completion)
            self.assertTrue(hasattr(completion, "choices"))
            self.assertGreater(len(completion.choices), 0)

            message_content = completion.choices[0].message.content
            self.assertIsInstance(message_content, str)

        except OpenAIError as e:
            self.fail(f"OpenAI API call failed with error: {e}")

    def test_invalid_model_name(self):
        try:
            self.client.chat.completions.create(
                model="invalid-model-name",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"},
                ],
            )
            self.fail("Expected BadRequestError not raised")
        except NotFoundError:
            pass
        except OpenAIError as e:
            self.fail(f"Unexpected OpenAIError: {e}")

    def test_multiple_messages(self):
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Tell me a joke."},
                    {"role": "user", "content": "And give me a quote."},
                ],
            )

            self.assertIsNotNone(completion)
            self.assertTrue(hasattr(completion, "choices"))
            self.assertGreater(len(completion.choices), 0)

            message_content = completion.choices[0].message.content
            self.assertIsInstance(message_content, str)
            self.assertGreater(len(message_content), 0)

        except OpenAIError as e:
            self.fail(f"OpenAI API call failed with error: {e}")

    def test_handling_authentication_error(self):
        invalid_api_client = OpenAI(api_key="invalid_api_key")
        try:
            invalid_api_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"},
                ],
            )
            self.fail("Expected AuthenticationError not raised")
        except AuthenticationError:
            pass
        except OpenAIError as e:
            self.fail(f"Unexpected OpenAIError: {e}")


class TestDecideDailyCommitsFunction(unittest.TestCase):
    def setUp(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    async def test_commit_without_diff(self):
        commit_without_diff = {
            "2024-04-29": [
                {
                    "repo": "repo/test",
                    "author": "author",
                    "username": "username",
                    "date": "2024-04-29T16:52:07Z",
                    "message": "Commit without diff",
                    "sha": "sha1",
                    "branch": "main",
                    "diff": "",
                }
            ]
        }

        result = await ai.decide_daily_commits(
            "2024-04-29", commit_without_diff["2024-04-29"]
        )
        self.assertEqual(result, False)

    async def test_empty_message(self):
        empty_commit_data = []
        result = await ai.decide_daily_commits("2024-04-29", empty_commit_data)

        self.assertEqual(result, False)

    async def test_incorrect_date_format(self):
        incorrect_date = "29-04-2024"
        with self.assertRaises(ValueError):
            result = await ai.decide_daily_commits(incorrect_date, self.commit_data)

    async def test_valid_commit(self):
        result = await ai.decide_daily_commits("2024-04-29", self.commit_data)
        self.assertNotEqual(result, False)


if __name__ == "__main__":
    unittest.main()
