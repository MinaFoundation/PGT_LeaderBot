import os
import sys
import json
import time
from typing import List, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config
from log_config import get_logger

logger = get_logger(__name__)

from db_functions import fetch_db_get_users


def get_data_for_year_month():
    try:
        users = fetch_db_get_users()
        dates_with_user_handles = {}

        for user in users:
            dates_with_user_handles[user.user_handle] = user.qualified_daily_contribution_number_by_month

        return dates_with_user_handles
    except Exception as e:
        logger.error(f"Could not fetch the data: {e}")


def create_leaderboard_by_month(year: str, month: str):
    data = get_data_for_year_month()
    target_date = f"{year}-{month.zfill(2)}"
    leaderboard = []

    for user_handle, contributions in data.items():
        if target_date in contributions:
            leaderboard.append((user_handle, contributions[target_date]))

    leaderboard.sort(key=lambda x: x[1], reverse=True)

    formatted_leaderboard = [["Rank", "User Handle", "Contributions"]]
    for rank, (user_handle, contributions) in enumerate(leaderboard, start=1):
        formatted_leaderboard.append([rank, user_handle, contributions])
    
    return formatted_leaderboard