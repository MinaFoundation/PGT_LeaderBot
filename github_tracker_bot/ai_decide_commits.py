import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
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


async def decide_daily_commits(date: str, data_array: List[CommitData], seed: int = None):
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

        retries = 0
        max_retries = 2

        while retries < max_retries:
            try:
                # Call the OpenAI API
                completion = client.chat.completions.create(
                    model="gpt-4o",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": prompts.SYSTEM_MESSAGE_DAILY_DECIDE_COMMIT},
                        {"role": "user", "content": message},
                    ],
                    seed=seed,
                    temperature=0.1,
                )
                # If successful, return the completion message
                return completion.choices[0].message.content

            except AuthenticationError as e:
                # Handle 403 Forbidden (Authentication Error) with retries
                retries += 1
                logger.error(f"403 Forbidden Error: {e}. Retrying {retries}/{max_retries} in 1 minute...")
                if retries >= max_retries:
                    logger.error(f"Failed after {max_retries} attempts due to 403 Forbidden Error.")
                    return False
                time.sleep(60)  # Sleep for 1 minute before retrying

            except OpenAIError as e:
                # Handle general OpenAIError (e.g., 500 Internal Server Error) with retries
                retries += 1
                logger.error(f"OpenAI API Error: {e}. Retrying {retries}/{max_retries} in 1 minute...")
                if retries >= max_retries:
                    logger.error(f"Failed after {max_retries} attempts due to OpenAI Error: {e}")
                    return False
                time.sleep(60)  # Sleep for 1 minute before retrying

            except NotFoundError:
                # Handle 404 Not Found
                logger.error("404 Not Found Error.")
                return False

    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred: {e}")
        return False


    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred: {e}")
        return False
