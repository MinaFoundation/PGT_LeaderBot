import os
import sys
import json
import time
import asyncio
import random

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


async def decide_daily_commits(date: str, data_array: List[CommitData], seed: int = 42, max_retries: int = None, initial_retry_delay: int = None):
    if not validate_date_format(date):
        raise ValueError("Incorrect date format, should be YYYY-MM-DD")
        
    # Use config values if not explicitly provided
    if max_retries is None:
        max_retries = config.OPENAI_MAX_RETRIES
    if initial_retry_delay is None:
        initial_retry_delay = config.OPENAI_INITIAL_RETRY_DELAY

    retry_count = 0
    had_error = False
    
    while retry_count <= max_retries:
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
            
            # Log successful retry if we previously had an error
            if had_error:
                logger.info(f"Successfully completed OpenAI API call after {retry_count} retries")

            return completion.choices[0].message.content

        except OpenAIError as e:
            error_message = str(e)
            logger.error(f"OpenAI API call failed with error: {e}")
            had_error = True
            
            # Check for errors that should be retried
            should_retry = False
            
            # 403 Forbidden or HTML response (API instability)
            if "403 Forbidden" in error_message or "<!DOCTYPE html>" in error_message:
                should_retry = True
            # Rate limit errors
            elif "rate limit" in error_message.lower() or "too many requests" in error_message.lower():
                should_retry = True
            # Server errors (5xx)
            elif "500" in error_message or "502" in error_message or "503" in error_message or "504" in error_message:
                should_retry = True
            # Timeout errors
            elif "timeout" in error_message.lower() or "timed out" in error_message.lower():
                should_retry = True
                
            if should_retry:
                retry_count += 1
                if retry_count <= max_retries:
                    # Calculate exponential backoff delay with jitter: initial_delay * 2^(retry_count-1) * (0.5 + random(0, 0.5))
                    base_delay = initial_retry_delay * (2 ** (retry_count - 1))
                    jitter = random.uniform(0.5, 1.0)  # Add 50-100% of the base delay as jitter
                    retry_delay = base_delay * jitter
                    logger.info(f"OpenAI API error detected. Retrying in {int(retry_delay)} seconds (Attempt {retry_count}/{max_retries})...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Maximum retry attempts ({max_retries}) reached. Giving up.")
                    return False
            else:
                # For other OpenAI errors, don't retry
                return False

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return False
