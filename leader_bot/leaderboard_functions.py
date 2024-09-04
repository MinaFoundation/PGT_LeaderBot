import os
import sys
from typing import Dict
from datetime import datetime

from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from log_config import get_logger

logger = get_logger(__name__)

from db_functions import fetch_db_get_users, get_discord_user_id


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

    if int(month) == 12:
        next_year = int(year) + 1
        next_month = 1
    else:
        next_year = int(year)
        next_month = int(month) + 1

    last_day_of_month = (datetime(next_year, next_month, 1) - timedelta(days=1)).day

    current_date = datetime.now()

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
                if current_date >= last_date:
                    days_since_first_contribution = (last_date - first_date).days + 1
                else:
                    days_since_first_contribution = (current_date - first_date).days + 1

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


def format_leaderboard_for_discord(leaderboard, req_date=None, is_month_closure=False):
    trophy_emojis = ["🥇", "🥈", "🥉"]
    current_date = datetime.now().strftime("%B %d, %Y")

    if is_month_closure and req_date:
        leaderboard_message = f"🏆 **Leaderboard | {req_date}** 🏆\n\n"
    else:
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

        discord_user_id = get_discord_user_id(user_handle)

        if discord_user_id:
            user_mention = f"<@{discord_user_id}>"
        else:
            user_mention = user_handle

        leaderboard_message += f"{rank_str} **{user_mention}** **|** {contributions} days of contributions **|** 🗓️ in the last {days_since_first_contribution} days\n"

    return split_message(leaderboard_message)


def format_streaks_for_discord(streaks: Dict[str, int], month: str) -> str:
    trophy_emojis = ["🥇", "🥈", "🥉"]
    current_date = datetime.now().strftime("%B %d, %Y")

    streaks_message = f"🏆 **Monthly Streaks | {month}** 🏆\n\n"

    sorted_streaks = sorted(streaks.items(), key=lambda item: item[1], reverse=True)

    for i, (user_handle, streak) in enumerate(sorted_streaks):
        rank = i + 1

        if rank <= len(trophy_emojis):
            rank_str = trophy_emojis[rank - 1]
        else:
            rank_str = f"{rank}. "

        discord_user_id = get_discord_user_id(user_handle)

        if discord_user_id:
            user_mention = f"<@{discord_user_id}>"
        else:
            user_mention = user_handle

        streaks_message += f"{rank_str} **{user_mention}** **|** {streak} day{'s' if streak > 1 else ''} streak\n"

    return split_message(streaks_message)
