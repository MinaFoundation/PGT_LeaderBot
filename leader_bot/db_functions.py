import os
import sys
from typing import List, Dict, Optional
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from log_config import get_logger

logger = get_logger(__name__)

from pymongo import MongoClient
import github_tracker_bot.mongo_data_handler as mongo
from helpers import get_user_data_for_a_month


def connect_db(host, db, collection):
    client = MongoClient(host)
    db = client[db]
    collection = db[collection]

    mongo_manager = mongo.MongoDBManagement(db, collection)
    return mongo_manager


mongo_manager = connect_db(config.MONGO_HOST, config.MONGO_DB, config.MONGO_COLLECTION)

user_id_collection = connect_db(
    config.MONGO_HOST, config.MONGO_DB, "DISCORD_USERS"
).collection


def fetch_db_get_users() -> List[Optional[mongo.User]]:
    users = mongo_manager.get_users()
    return users


def insert_discord_users(data):
    try:
        batch_size = 1000

        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            result = user_id_collection.insert_many(batch)
            logger.debug(f"Inserted batch with IDs: {result.inserted_ids}")
        return True
    except Exception as e:
        logger.error(
            f"An error occured while inserting discord users to {user_id_collection}: {e}"
        )
        return False


def get_discord_user_id(username):
    try:
        user = user_id_collection.find_one({username: {"$exists": True}})
        if user:
            return user.get(username)
        else:
            return None
    except Exception as e:
        logger.error(f"An error occured: {e}")
        return None


def get_ai_decisions_by_user_and_timeframe(username, since, until):
    ai_decisions = mongo_manager.get_ai_decisions_by_user_and_daterange(
        username, since, until
    )

    return ai_decisions


def calculate_monthly_streak(month: str) -> Dict[str, int]:
    try:
        users = fetch_db_get_users()
        user_streaks = {}

        for user in users:
            contributions_in_month = [
                date
                for date in user.qualified_daily_contribution_dates
                if date.startswith(month)
            ]

            if contributions_in_month:
                streak = 0
                max_streak = 0
                previous_date = None

                for date in sorted(contributions_in_month):
                    current_date = datetime.strptime(date, "%Y-%m-%d")
                    if previous_date and (current_date - previous_date).days == 1:
                        streak += 1
                    else:
                        streak = 1
                    max_streak = max(max_streak, streak)
                    previous_date = current_date

                user_streaks[user.user_handle] = max_streak

        return user_streaks

    except Exception as e:
        logger.error(f"Failed to calculate monthly streaks: {e}")
        return {}


def get_user_data_for_a_month_from_db(username: str, month: str):
    try:
        users = fetch_db_get_users()
        return get_user_data_for_a_month(users, username, month)

    except Exception as e:
        logger.error(f"Failed to get user data for a month: {e}")
        return {}
