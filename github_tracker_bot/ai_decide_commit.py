import config
import prompts

from openai import AuthenticationError, NotFoundError, OpenAI, OpenAIError

client = OpenAI(api_key=config.OPENAI_API_KEY)

async def decide_daily_commits(daily_commits):
    