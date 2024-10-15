import os
import sys
import time
import asyncio
import aiohttp
from datetime import datetime
from dateutil import parser
from github import Github
from typing import List, Optional, Dict, Any
from tenacity import (
    retry,
    wait_fixed,
    stop_after_attempt,
    retry_if_exception_type,
    RetryError,
)
from asyncio import Semaphore

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
import github_tracker_bot.helpers.extract_unnecessary_diff as lib
import github_tracker_bot.helpers.handle_daily_commits_exceed_data as exceed_handler

from log_config import get_logger

logger = get_logger(__name__)

GITHUB_TOKEN = config.GITHUB_TOKEN
g = Github(GITHUB_TOKEN)


CONCURRENT_REQUESTS = 5
semaphore = Semaphore(CONCURRENT_REQUESTS)

retry_conditions = (
    retry_if_exception_type(
        aiohttp.ClientError,
    )
    | retry_if_exception_type(asyncio.TimeoutError)
    | retry_if_exception_type(aiohttp.ClientConnectorError)
)


@retry(wait=wait_fixed(5), stop=stop_after_attempt(8), retry=retry_conditions)
async def fetch_diff(repo: str, sha: str) -> Optional[str]:
    url = f"https://api.github.com/repos/{repo}/commits/{sha}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff",
    }

    async with semaphore:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        diff = await response.text()
                        return diff
                    elif response.status == 403:
                        reset_time = response.headers.get("X-RateLimit-Reset")
                        sleep_time = (
                            int(reset_time) - int(time.time()) + 1 if reset_time else 60
                        )
                        logger.warning(
                            f"Rate limit exceeded. Sleeping for {sleep_time} seconds."
                        )
                        await asyncio.sleep(sleep_time)
                        raise aiohttp.ClientError("Rate limit exceeded, retrying...")
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Failed to fetch diff: {response.status}, {error_text}"
                        )
                        return None
        except Exception as e:
            logger.error(f"Error while fetching diff for repo {repo}: {e}")
            raise


def concatenate_diff_to_commit_info(
    commit_info: Dict[str, Any], diff: Optional[str]
) -> Dict[str, Any]:
    result = {
        "repo": commit_info["repo"],
        "author": commit_info["author"],
        "username": commit_info["username"],
        "date": commit_info["date"],
        "message": commit_info["message"],
        "sha": commit_info["sha"],
        "branch": commit_info["branch"],
    }

    if diff is not None:
        result["diff"] = lib.filter_diffs(diff)
    else:
        result["diff"] = ""

    return result


def group_and_sort_commits(
    processed_commits: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    grouped_commits = {}

    for commit in processed_commits:
        date = commit["date"][:10]
        if date not in grouped_commits:
            grouped_commits[date] = []
        grouped_commits[date].append(commit)

    for date in sorted(grouped_commits.keys()):
        grouped_commits[date].sort(key=lambda x: parser.isoparse(x["date"]))

    return grouped_commits


async def process_commits(commit_infos: List[Dict[str, Any]]):
    tasks = [
        fetch_diff(commit_info["repo"], commit_info["sha"])
        for commit_info in commit_infos
    ]

    diffs = await asyncio.gather(*tasks, return_exceptions=True)

    processed_commits = []
    for commit_info, diff in zip(commit_infos, diffs):
        if isinstance(diff, Exception):
            logger.error(f"Failed to fetch diff for {commit_info['sha']}: {diff}")
            diff = None
        processed_commit = concatenate_diff_to_commit_info(commit_info, diff)
        processed_commits.append(processed_commit)

    grouped_commits = group_and_sort_commits(processed_commits)
    for daily_commit in grouped_commits.values():
        exceed_handler.handle_daily_exceed_data(daily_commit)

    return grouped_commits


if __name__ == "__main__":
    repo_name = "UmstadAI/zkAppUmstad"
    sha = "092c20a73859e0b4a4591f815efbdcab08df4df8"
    try:
        diff = asyncio.run(fetch_diff(repo_name, sha))
        if diff:
            logger.info(f"Fetched diff successfully.")
        else:
            logger.error("Failed to fetch diff")
    except RetryError as e:
        logger.error(f"Failed after retries: {e}")
