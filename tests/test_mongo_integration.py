import json
import unittest
import config
from unittest.mock import patch, MagicMock

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

#collection.delete_many({})

mongo_manager = MongoDBManagement(db, collection)
x = mongo_manager.get_user("berkingurcan")
print(json.dumps(x.to_dict(), indent=3))
