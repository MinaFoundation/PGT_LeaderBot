import unittest
import config

from openai import OpenAI

class TestOpenAIIntegration(unittest.TestCase):
    def setUp(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def test_chat_completion_ok(self):
        completion = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
        )

        print(completion)
        self.assertIsNotNone(completion)




if __name__ == "__main__":
    unittest.main()