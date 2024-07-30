import os
import sys
import json
from typing import List, Optional
from datetime import datetime, timedelta

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
            dates_with_user_handles[user.user_handle] = (
                user.qualified_daily_contribution_number_by_month
            )

        return dates_with_user_handles
    except Exception as e:
        logger.error(f"Could not fetch the data: {e}")


def get_qualified_dates():
    try:
        users = fetch_db_get_users()
        qualified_dates_with_user_handles = {}

        for user in users:
            qualified_dates_with_user_handles[user.user_handle] = (
                user.qualified_daily_contribution_dates
            )

        return qualified_dates_with_user_handles
    except Exception as e:
        logger.error(f"Could not fetch the data: {e}")


def create_leaderboard_by_month(year: str, month: str, commit_filter: int = 0):
    data = get_data_for_year_month()
    qualified_dates = get_qualified_dates()

    target_date = f"{year}-{month.zfill(2)}"
    leaderboard = []

    last_day_of_month = (datetime(int(year), int(month) + 1, 1) - timedelta(days=1)).day

    current_date = datetime.now()

    # Check this later is it working well
    for user_handle, contributions in data.items():
        if target_date in contributions:
            first_date_str = min(
                [
                    date
                    for date in qualified_dates[user_handle]
                    if date.startswith(target_date)
                ],
                default=None,
            )
            if first_date_str:
                first_date = datetime.strptime(first_date_str, "%Y-%m-%d")
                last_date = datetime(int(year), int(month), last_day_of_month)
                days_since_first_contribution = (last_date - first_date).days

                if contributions[target_date] >= commit_filter:
                        leaderboard.append(
                            (
                                user_handle,
                                contributions[target_date],
                                days_since_first_contribution,
                            )
                        )

    leaderboard.sort(key=lambda x: x[1], reverse=True)

    formatted_leaderboard = [
        ["Rank", "User Handle", "Contributions", "Days Since First Contribution"]
    ]
    for rank, (user_handle, contributions, days_since_first_contribution) in enumerate(
        leaderboard, start=1
    ):
        formatted_leaderboard.append(
            [rank, user_handle, contributions, days_since_first_contribution]
        )

    return formatted_leaderboard


def split_message(message, limit=2000):
    """
    Split a message into chunks that each fit within the character limit.
    """
    chunks = []
    while len(message) > limit:
        split_pos = message.rfind("\n", 0, limit)
        if split_pos == -1:
            split_pos = limit
        chunks.append(message[:split_pos])
        message = message[split_pos:].lstrip()
    chunks.append(message)
    return chunks


def format_leaderboard_for_discord(leaderboard):
    trophy_emojis = ["🥇", "🥈", "🥉"]
    current_date = datetime.now().strftime("%B %d, %Y")

    leaderboard_message = f"🏆 **Leaderboard | {current_date}** 🏆\n\n"

    for entry in leaderboard[1:]:
        rank = entry[0]
        user_handle = entry[1]
        contributions = entry[2]
        days_since_first_contribution = entry[3]

        if rank <= len(trophy_emojis):
            rank_str = trophy_emojis[rank - 1]
        else:
            rank_str = f"{rank}. "

        leaderboard_message += f"{rank_str} **{user_handle}** **|** {contributions} contributions **|** 🗓️ in the last {days_since_first_contribution} days\n"

    return split_message(leaderboard_message)
