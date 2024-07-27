from collections import defaultdict
import json
from typing import Dict, List
import unittest
import config
from unittest.mock import patch, MagicMock

from dateutil import parser
from datetime import datetime, timedelta

from pymongo import MongoClient
from pymongo.collection import Collection

from github_tracker_bot.mongo_data_handler import (
    MongoDBManagement,
    User,
    AIDecision,
    DailyContributionResponse,
)


client = MongoClient(config.MONGO_HOST)
db = client[config.MONGO_DB]
collection = db[config.MONGO_COLLECTION]

# collection.delete_many({})

since_date = "2024-05-01T00:00:00Z"  # ISO 8601 format
until_date = "2024-05-31T00:00:00Z"

mongo_manager = MongoDBManagement(db, collection)
berkingurcan = mongo_manager.get_user("berkingurcan")
dfst = mongo_manager.get_user("dfst")
mario_zito = mongo_manager.get_user("mario_zito")

# print(berkingurcan)

# print(json.dumps(x.to_dict(), indent=3))

if __name__ == "__main__":
    unittest.main()
