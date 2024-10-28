import os
import sys
import json
import aiohttp
import asyncio
import time
from typing import Optional, List, TypedDict
from datetime import datetime
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

import config
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


retry_conditions = (
    retry_if_exception_type(AuthenticationError)
    | retry_if_exception_type(OpenAIError)
    | retry_if_exception_type(aiohttp.ClientError)
    | retry_if_exception_type(asyncio.TimeoutError)
    | retry_if_exception_type(aiohttp.ClientConnectorError)
)


@retry(
    wait=wait_exponential(multiplier=2, min=5, max=60),
    stop=stop_after_attempt(8),
    retry=retry_conditions,
)
async def decide_daily_commits(
    date: str, data_array: List[CommitData], seed: int = 42
) -> Optional[str]:
    if not validate_date_format(date):
        raise ValueError("Incorrect date format, should be YYYY-MM-DD")

    if not data_array:
        logger.error("Commit data array is empty")
        return None

    message = prompts.process_message(date, data_array)
    if not message:
        logger.error("Message processing failed")
        return None

    try:
        completion = await client.chat.completions.create(
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

    except NotFoundError:
        logger.error("404 Not Found Error.")
        return None

    except aiohttp.ClientResponseError as e:
        if e.status == 403:
            reset_time = e.headers.get("X-RateLimit-Reset")
            try:
                sleep_time = (
                    max(int(reset_time) - int(time.time()) + 1, 1) if reset_time else 60
                )
            except ValueError:
                sleep_time = 60
            logger.warning(f"Rate limit exceeded. Sleeping for {sleep_time} seconds.")
            await asyncio.sleep(sleep_time)
            raise aiohttp.ClientError("Rate limit exceeded, retrying...")

    except OpenAIError as e:
        logger.error(f"OpenAI API Error: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None
