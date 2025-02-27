from datetime import datetime
from dateutil import parser

import sys
import os
import json
import asyncio

from dataclasses import asdict
from collections import OrderedDict, defaultdict
from typing import List

from openai import OpenAIError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from log_config import get_logger

logger = get_logger(__name__)

from github_tracker_bot.commit_scraper import get_user_commits_in_repo
from github_tracker_bot.process_commits import process_commits
from github_tracker_bot.ai_decide_commits import decide_daily_commits
from github_tracker_bot.helpers.spreadsheet_handlers import (
    spreadsheet_to_list_of_user,
    get_sheet_data,
    find_user,
)
import github_tracker_bot.mongo_data_handler as rd
from pymongo import MongoClient


def count_qualified_contributions_by_date(full_result, since_date, until_date):
    since_date = parser.isoparse(since_date).replace(tzinfo=None)
    until_date = parser.isoparse(until_date).replace(tzinfo=None)

    qualified_days = set()

    for decision_list in full_result:
        for decision in decision_list:
            decision_date = parser.isoparse(decision.date).replace(tzinfo=None)
            if since_date <= decision_date <= until_date:
                if decision.response.is_qualified:
                    qualified_days.add(decision_date.date().strftime("%Y-%m-%d"))

    sorted_qualified_days = sorted(qualified_days)
    return {
        "qualified_days": sorted_qualified_days,
        "count": len(sorted_qualified_days),
    }


async def get_all_results_from_sheet_by_date(spreadsheet_id, since_date, until_date):
    try:
        sheet_data = await get_sheet_data(spreadsheet_id)
        if not sheet_data:
            logger.error(
                f"Failed to retrieve data from spreadsheet ID: {spreadsheet_id}"
            )
            return None

        results = {}

        users = spreadsheet_to_list_of_user(sheet_data)

        for user in users:
            user_results, qualified_contribution_count = (
                await get_user_results_from_sheet_by_date(
                    user.github_name, spreadsheet_id, since_date, until_date, sheet_data
                )
            )

            if user_results:
                results[user.user_handle] = {
                    "results": user_results,
                    "qualified_contribution_count": qualified_contribution_count,
                }

        write_full_to_json(results, "all_results.json")
        logger.debug(results)
        return results

    except Exception as e:
        logger.error(f"An error occurred while fetching results from sheet: {e}")


def connect_db(host, db, collection):
    client = MongoClient(host)
    db = client[db]
    collection = db[collection]

    mongo_manager = rd.MongoDBManagement(db, collection)
    return mongo_manager


mongo_manager = connect_db(config.MONGO_HOST, config.MONGO_DB, config.MONGO_COLLECTION)


async def get_user_results_from_sheet_by_date(
    username, spreadsheet_id, since_date, until_date, sheet_data_from=None
):
    try:
        full_results = []

        if not sheet_data_from:
            sheet_data = await get_sheet_data(spreadsheet_id)
        else:
            sheet_data = sheet_data_from
        if not sheet_data:
            logger.error(
                f"Failed to retrieve data from spreadsheet ID: {spreadsheet_id}"
            )
            return None

        users = spreadsheet_to_list_of_user(sheet_data)
        user = find_user(users, username)

        if not user:
            logger.error(f"User not found: {username}")
            return None

        db_user = mongo_manager.get_user(user.user_handle)
        if not db_user:
            logger.info(f"Creating new user in the database: {user.user_handle}")
            db_user = rd.User(
                user_handle=user.user_handle,
                github_name=user.github_name,
                repositories=user.repositories,
            )
            try:
                db_user = mongo_manager.create_user(db_user)
            except Exception as e:
                logger.error(e)
                return None
        else:
            logger.info(f"User already exists in the database: {user.user_handle}")

        tasks = [
            get_result(user.github_name, repository, since_date, until_date)
            for repository in user.repositories
        ]

        results = await asyncio.gather(*tasks)
        results = [result for result in results if result is not None and result != []]
        for ai_decisions in results:
            if ai_decisions:
                ai_decisions_class = create_ai_decisions_class(ai_decisions)
                if db_user:
                    logger.info(
                        f"Updating AI Decisions for existing user in the database: {user.user_handle}"
                    )
                    try:
                        u = mongo_manager.add_ai_decisions_by_user(
                            db_user.user_handle, ai_decisions_class
                        )
                        if u:
                            logger.info(
                                f"Updated succesfully AI Decision for existing user in the database: {user.user_handle}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Error encountered while updating AI Decision: {e}"
                        )

                full_results.append(ai_decisions_class)

        logger.debug(f"Full results: {full_results}")
        write_full_to_json(full_results, "full_res.json")

        qualified_contribution_count = count_qualified_contributions_by_date(
            full_results, since_date, until_date
        )

        if db_user:
            logger.info(f"Updating contribution values for user: {db_user.user_handle}")
            try:
                updated = mongo_manager.update_all_contribution_datas_from_ai_decisions(
                    db_user.user_handle
                )
                if updated:
                    logger.info(
                        f"All user contribution fields are updated for user: {updated.user_handle}"
                    )

            except Exception as e:
                logger.error(
                    f"Error encountered while updating contribution fields for user: {db_user.user_handle}: {e}"
                )

        logger.debug(qualified_contribution_count)
        return full_results, qualified_contribution_count

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

        if not commit_infos:
            return None

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

        get_repo_name = lambda url: url.rstrip("/").split("/")[-1]
        repo_name = get_repo_name(repo_link)

        return ai_decisions

    except Exception as e:
        logger.error(f"An error occurred while getting result: {e}")
        return None


async def process_commit_day(username, repo_link, commits_day, commits_data):
    try:
        response = await decide_daily_commits(commits_day, commits_data)
        
        # If the response is False, it means all retries failed
        if response is False:
            logger.error(f"Failed to get response from OpenAI API after retries for {username}, {repo_link}, {commits_day}")
            return None
        
        try:
            parsed_response = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from OpenAI API: {e}. Response: {response}")
            return None
            
        commit_hashes = [commit["sha"] for commit in commits_data]
        data_entry = {
            "username": username,
            "repository": repo_link,
            "date": commits_day,
            "response": parsed_response,
            "commit_hashes": commit_hashes,
        }
        logger.debug(
            f"AI Response for daily commits:\n"
            f"Username: {username},\n"
            f"Repository: {repo_link},\n"
            f"Date: {commits_day},\n"
            f"Response: {response},\n"
            f"Commit Hashes: {commit_hashes}"
        )
        return data_entry
    except OpenAIError as e:
        logger.error(f"OpenAI API call failed with error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return None


async def delete_all_data(since_date, until_date):
    try:
        deleted_users, updated_users = (
            mongo_manager.delete_ai_decisions_and_clean_users(since_date, until_date)
        )
        if deleted_users is None:
            deleted_users = []
        if updated_users is None:
            updated_users = []
        logger.info(f"deleted_users: {str(deleted_users)}")
        logger.info(f"updated_users: {str(updated_users)}")
        all_users_to_be_updated = list(set(deleted_users + updated_users))
        logger.info(f"all_users_to_be_updated: {str(all_users_to_be_updated)}")
        for user in all_users_to_be_updated:
            try:
                mongo_manager.update_all_contribution_datas_from_ai_decisions(
                    user_handle=user
                )
            except Exception as e:
                logger.error(
                    f"An error occurred while updating contribution fields for user: {user}: {e}"
                )
    except Exception as e:
        logger.error(f"An error occurred while deleting data: {e}")


def convert_to_dict(data):
    if isinstance(data, list):
        return [convert_to_dict(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_to_dict(value) for key, value in data.items()}
    elif hasattr(data, "__dataclass_fields__"):
        return {key: convert_to_dict(value) for key, value in asdict(data).items()}
    elif isinstance(data, set):
        return list(data)
    elif isinstance(data, (rd.AIDecision, rd.DailyContributionResponse)):
        return asdict(data)
    else:
        return data


def create_ai_decisions_class(data):
    """Creates a list of AIDecisions instances from a list of dictionaries."""
    decisions = []
    for entry in data:
        response_data = entry["response"]
        response = rd.DailyContributionResponse(
            username=response_data["username"],
            date=response_data["date"],
            is_qualified=response_data["is_qualified"],
            explanation=response_data["explanation"],
        )
        decision = rd.AIDecision(
            username=entry["username"],
            repository=entry["repository"],
            date=entry["date"],
            response=response,
            commit_hashes=entry.get("commit_hashes", []),
        )
        decisions.append(decision)
    return decisions


def write_to_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=5)
        logger.info(f"Processed commits have been written to {filename}")


def write_full_to_json(data, filename):
    dict_data = convert_to_dict(data)

    with open(filename, "w") as json_file:
        json.dump(dict_data, json_file, indent=4)


if __name__ == "__main__":
    username = "berkingurcan"
    repo_link = "https://github.com/UmstadAI/zkappumstad"
    since_date = "2024-03-01T00:00:00Z"  # ISO 8601 format
    until_date = "2024-06-30T00:00:00Z"

    asyncio.run(
        get_all_results_from_sheet_by_date(
            config.SPREADSHEET_ID, since_date, until_date
        )
    )
