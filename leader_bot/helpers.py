import pandas as pd
import github_tracker_bot.mongo_data_handler as rd
from typing import List
import calendar


def csv_to_structured_string(file_path):
    df = pd.read_csv(file_path)

    structured_string = ""

    columns = df.columns

    structured_string += " | ".join(columns) + "\n"
    structured_string += "-" * (len(structured_string) - 1) + "\n"

    for index, row in df.iterrows():
        row_string = " | ".join([str(item) for item in row])
        structured_string += row_string + "\n"

    return structured_string


def get_user_data_for_a_month(users: List[rd.User], username: str, month: str):

    for user in users:
        if (
            user.user_handle == username
            and user.qualified_daily_contribution_number_by_month.get(month)
        ):

            return user

    return None


def get_monthly_user_data_from_ai_decisions(ai_decisions):
    if not ai_decisions or not ai_decisions[0]:
        raise ValueError("Empty ai_decisions list")

    date_nonqualified_qualified = {}

    for decision_list in ai_decisions:
        for decision in decision_list:
            date = decision.response.date
            if date not in date_nonqualified_qualified:
                date_nonqualified_qualified[date] = [
                    0,
                    0,
                ]  # first element is nonqualified, second is qualified

            if decision.response.is_qualified:
                date_nonqualified_qualified[date][1] += 1
            else:
                date_nonqualified_qualified[date][0] += 1
    return dict(sorted(date_nonqualified_qualified.items()))


def get_since_until_y_m_d(date: str):
    """
    Args:
        date (str): The input date as a string in the format 'YYYY-MM'
                    (e.g., '2024-10' for October 2024).

    Returns:
        tuple: A tuple containing two strings:
               - 'since': The first day of the month in 'YYYY-MM-DD' format (e.g., '2024-04-01').
               - 'until': The last day of the month in 'YYYY-MM-DD' format (e.g., '2024-04-30').

    Example:
        >>> get_since_until_y_m_d('2024-10')
        ('2024-10-01', '2024-10-31')
    """
    year, month = map(int, date.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    since = f"{date}-01"
    until = f"{date}-{last_day}"
    return since, until
