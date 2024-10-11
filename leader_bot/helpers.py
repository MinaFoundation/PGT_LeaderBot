import pandas as pd
import github_tracker_bot.mongo_data_handler as rd
from typing import List


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
        if user.user_handle == username:
            if user.qualified_daily_contribution_number_by_month.get(month):
                return user

    return None


def get_monthly_user_data_from_ai_decisions(ai_decisions):
    if not ai_decisions or not ai_decisions[0]:
        raise ValueError("Empty ai_decisions list")

    date_qualified_nonqualified = {}

    for decision_list in ai_decisions:
        for decision in decision_list:
            date = decision.response.date
            if date not in date_qualified_nonqualified:
                date_qualified_nonqualified[date] = [
                    0,
                    0,
                ]  # first element is nonqualified, second is qualified

            if decision.response.is_qualified:
                date_qualified_nonqualified[date][1] += 1
            else:
                date_qualified_nonqualified[date][0] += 1
    return dict(sorted(date_qualified_nonqualified.items()))
