import config
import prompts
from typing import TypedDict, List
from datetime import datetime

import log_config
import prompts

from openai import AuthenticationError, NotFoundError, OpenAI, OpenAIError

logger = log_config.get_logger(__name__)

client = OpenAI(api_key=config.OPENAI_API_KEY)


class CommitData(TypedDict):
    repo: str
    author: str
    date: str
    message: str
    sha: str
    branch: str
    diff: str


async def decide_daily_commits(
    date: str, data_array: List[CommitData], seed: int = None
):
    message = prompts.process_message(date, data_array)

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": prompts.SYSTEM_MESSAGE_DAILY_DECIDE_COMMIT,
                },
                {"role": "user", "content": message},
            ],
            seed=seed,
            temperature=0.1,
        )

        return completion.choices[0].message.content

    except OpenAIError as e:
        logger.error(f"OpenAI API call failed with error: {e}")
