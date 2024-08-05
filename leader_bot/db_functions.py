import os
import sys
from typing import List, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from log_config import get_logger

logger = get_logger(__name__)

from pymongo import MongoClient
import github_tracker_bot.mongo_data_handler as mongo


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
