import os
import sys
import json
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

def fetch_db_get_users() -> List[Optional[mongo.User]]:
    users = mongo_manager.get_users()
    return users
