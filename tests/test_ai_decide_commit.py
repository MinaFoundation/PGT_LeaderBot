import unittest
import config

from openai import AuthenticationError, BadRequestError, NotFoundError, OpenAI, OpenAIError

class TestOpenAIIntegration(unittest.TestCase):
    def setUp(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def test_chat_completion_ok(self):
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"}
                ]
            )

            self.assertIsNotNone(completion)
            self.assertTrue(hasattr(completion, 'choices'))
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
                    {"role": "user", "content": ""}
                ]
            )

            self.assertIsNotNone(completion)
            self.assertTrue(hasattr(completion, 'choices'))
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
                    {"role": "user", "content": "Hello!"}
                ]
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
                    {"role": "user", "content": "And give me a quote."}
                ]
            )

            self.assertIsNotNone(completion)
            self.assertTrue(hasattr(completion, 'choices'))
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
                    {"role": "user", "content": "Hello!"}
                ]
            )
            self.fail("Expected AuthenticationError not raised")
        except AuthenticationError:
            pass
        except OpenAIError as e:
            self.fail(f"Unexpected OpenAIError: {e}")

if __name__ == "__main__":
    unittest.main()