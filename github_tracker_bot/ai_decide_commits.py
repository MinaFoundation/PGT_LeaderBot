import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from typing import TypedDict, List
from datetime import datetime

import log_config
import github_tracker_bot.prompts as prompts

from openai import AuthenticationError, NotFoundError, OpenAI, OpenAIError

logger = log_config.get_logger(__name__)

client = OpenAI(api_key=config.OPENAI_API_KEY)


class CommitData(TypedDict):
    repo: str
    author: str
    username: str
    date: str
    message: str
    sha: str
    branch: str
    diff: str


def validate_date_format(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


async def decide_daily_commits(
    date: str, data_array: List[CommitData], seed: int = None
):
    if not validate_date_format(date):
        raise ValueError("Incorrect date format, should be YYYY-MM-DD")

    try:
        commit_data = next((data for data in data_array), None)
        if not commit_data:
            logger.error("Commit data or diff file is empty")
            return False

        message = prompts.process_message(date, data_array)
        if not message:
            logger.error("After processing commit")
            return False

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

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False
