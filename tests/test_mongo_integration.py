import json
import unittest
import config
from unittest.mock import patch, MagicMock

from datetime import datetime
from dateutil import parser

from pymongo import MongoClient
from pymongo.collection import Collection

from github_tracker_bot.mongo_data_handler import (
    MongoDBManagement,
    User,
    AIDecision,
    DailyContributionResponse,
)

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

client = MongoClient(config.MONGO_HOST)
db = client[config.MONGO_DB]
collection = db[config.MONGO_COLLECTION]

# collection.delete_many({})

since_date = "2024-05-01T00:00:00Z"  # ISO 8601 format
until_date = "2024-05-30T00:00:00Z"


mongo_manager = MongoDBManagement(db, collection)
berkingurcan = mongo_manager.get_user("berkingurcan")
dfst = mongo_manager.get_user("dfst")

berkin_c = count_qualified_contributions_by_date(berkingurcan.ai_decisions, since_date, until_date)
dfst_c = count_qualified_contributions_by_date(dfst.ai_decisions, since_date, until_date)

print(f"{berkingurcan.user_handle} commit count {berkin_c}")
print(f"{dfst.user_handle} commit count {dfst_c}")

# print(json.dumps(x.to_dict(), indent=3))

if __name__ == "__main__":
    unittest.main()

