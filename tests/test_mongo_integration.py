import json
from typing import Dict
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


def count_all_contribution_data(full_result):
    """
    Returns all total_daily_contribution_number, total_qualified_daily_contribution_number, qualified_daily_contribution_dates
    """
    total_daily_contribution_days = set()
    qualified_daily_contribution_days = set()

    for decision_list in full_result:
        for decision in decision_list:
            total_daily_contribution_days.add(decision.date)
            if decision.response.is_qualified:
                qualified_daily_contribution_days.add(decision.date)

    sorted_total = sorted(total_daily_contribution_days)
    sorted_qualified = sorted_total(qualified_daily_contribution_days)

    return {
        "total_daily_contribution_number": len(sorted_total),
        "total_qualified_daily_contribution_number": len(sorted_qualified),
        "qualified_daily_contribution_dates": sorted_qualified
    }


def count_qualified_contributions_by_date(full_result, since_date, until_date):
    """Returns qualified and total commit days and numbers in dict format between given dates"""
    since_date = parser.isoparse(since_date).replace(tzinfo=None)
    until_date = parser.isoparse(until_date).replace(tzinfo=None)

    qualified_days = set()
    total_days = set()

    for decision_list in full_result:
        for decision in decision_list:
            decision_date = parser.isoparse(decision.date).replace(tzinfo=None)
            if since_date <= decision_date <= until_date:
                total_days.add(decision_date.date().strftime("%Y-%m-%d"))
                if decision.response.is_qualified:
                    qualified_days.add(decision_date.date().strftime("%Y-%m-%d"))

    sorted_qualified_days = sorted(qualified_days)
    sorted_total_days = sorted(total_days)
    return {
        "qualified_days": sorted_qualified_days,
        "qualified_days_count": len(sorted_qualified_days),
        "total_days": sorted_total_days,
        "total_days_count": len(sorted_total_days),
    }

def get_qualified_daily_contribution_number_by_month(full_result) -> Dict[str, int]:
    pass

def calculate_streak(full_result) -> int:
    pass


client = MongoClient(config.MONGO_HOST)
db = client[config.MONGO_DB]
collection = db[config.MONGO_COLLECTION]

# collection.delete_many({})

since_date = "2024-05-01T00:00:00Z"  # ISO 8601 format
until_date = "2024-05-31T00:00:00Z"

mongo_manager = MongoDBManagement(db, collection)
berkingurcan = mongo_manager.get_user("berkingurcan")
dfst = mongo_manager.get_user("dfst")

berkin_c = count_qualified_contributions_by_date(
    berkingurcan.ai_decisions, since_date, until_date
)
dfst_c = count_qualified_contributions_by_date(
    dfst.ai_decisions, since_date, until_date
)

print(f"{berkingurcan.user_handle} commit count {json.dumps(berkin_c, indent=4)}")
print(f"{dfst.user_handle} commit count {json.dumps(dfst_c, indent=4)}")

# print(json.dumps(x.to_dict(), indent=3))

if __name__ == "__main__":
    unittest.main()
