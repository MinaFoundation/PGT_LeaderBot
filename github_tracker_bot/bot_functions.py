import sys
import os
import json
import asyncio
from collections import OrderedDict
from typing import List

from openai import OpenAIError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from log_config import get_logger

logger = get_logger(__name__)

from commit_scraper import get_user_commits_in_repo
from process_commits import process_commits
from ai_decide_commits import decide_daily_commits
from helpers.spreadsheet_handlers import (
    spreadsheet_to_list_of_user,
    get_sheet_data,
    find_user,
)
import redis_data_handler as rd


async def get_all_results_from_sheet_by_date(spreadsheet_id, since_date, until_date):
    # Implement this function if needed
    pass


async def get_user_results_from_sheet_by_date(username, spreadsheet_id, since_date, until_date):
    try:
        full_results = []

        sheet_data = await get_sheet_data(spreadsheet_id)
        if not sheet_data:
            logger.error(f"Failed to retrieve data from spreadsheet ID: {spreadsheet_id}")
            return None

        users = spreadsheet_to_list_of_user(sheet_data)
        user = find_user(users, username)
        if not user:
            logger.error(f"User not found: {username}")
            return None

        tasks = [
            get_result(user.github_name, repository, since_date, until_date)
            for repository in user.repositories
        ]

        results = await asyncio.gather(*tasks)

        for ai_decisions in results:
            if ai_decisions:
                ai_decisions_class = rd.create_ai_decisions_class(ai_decisions)
                full_results.append(ai_decisions_class)

        logger.debug(f"Full results: {full_results}")
        return full_results

    except Exception as e:
        logger.error(f"An error occurred while retrieving user results: {e}")
        return None


async def get_result(username, repo_link, since_date, until_date):
    try:
        commit_infos = await get_user_commits_in_repo(
            username,
            repo_link,
            since_date,
            until_date,
        )

        ai_decisions = []

        if commit_infos:
            processed_commits = await process_commits(commit_infos)
            processed_commits = OrderedDict(sorted(processed_commits.items()))

            for commit_info in processed_commits:
                logger.debug(json.dumps(commit_info, indent=5))

            logger.debug(f"Total commit number: {len(processed_commits)}")
            write_to_json(processed_commits, "processed_commits.json")

            tasks = [
                process_commit_day(username, repo_link, commits_day, commits_data)
                for commits_day, commits_data in processed_commits.items()
            ]

            ai_decisions_results = await asyncio.gather(*tasks)

            for decision in ai_decisions_results:
                if decision:
                    ai_decisions.append(decision)

        return ai_decisions

    except Exception as e:
        logger.error(f"An error occurred while getting result: {e}")
        return None


async def process_commit_day(username, repo_link, commits_day, commits_data):
    try:
        response = await decide_daily_commits(commits_day, commits_data)
        data_entry = {
            "username": username,
            "repository": repo_link,
            "date": commits_day,
            "response": json.loads(response),
        }
        logger.debug(
            f"AI Response for daily commits:\n"
            f"Username: {username},\n"
            f"Repository: {repo_link},\n"
            f"Date: {commits_day},\n"
            f"Response: {response}"
        )
        return data_entry
    except OpenAIError as e:
        logger.error(f"OpenAI API call failed with error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return None


def write_to_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=5)
        logger.info(f"Processed commits have been written to {filename}")


if __name__ == "__main__":
    username = "berkingurcan"
    repo_link = "https://github.com/UmstadAI/zkappumstad"
    since_date = "2023-11-01T00:00:00Z"  # ISO 8601 format
    until_date = "2023-11-30T00:00:00Z"

    asyncio.run(get_user_results_from_sheet_by_date(username, config.SPREADSHEET_ID, since_date, until_date))
