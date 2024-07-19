from typing import List, Optional
import github_tracker_bot.read_sheet as rs
import github_tracker_bot.redis_data_handler as rd


async def get_sheet_data(spreadsheet_id: str) -> List[dict]:
    sheet_data: List[dict] = await rs.read_sheet(spreadsheet_id)
    return sheet_data


def spreadsheet_to_list_of_user(sheet_data: List[dict]) -> List[rd.User]:
    if not sheet_data:
        return []

    keys = list(sheet_data[0].keys())

    ss_users: List[rd.User] = []

    for user_data in sheet_data:
        try:
            user_handle = user_data[keys[0]]
            github_name = user_data[keys[1]]
            repositories = user_data[keys[2]]

            user = rd.User(user_handle, github_name, repositories)
            ss_users.append(user)
        except KeyError as e:
            print(f"Key error: {e} - skipping user data: {user_data}")
        except Exception as e:
            print(f"Unexpected error: {e} - skipping user data: {user_data}")

    return ss_users


def find_user(users: List[rd.User], identifier: str) -> Optional[rd.User]:
    for user in users:
        if user.user_handle == identifier or user.github_name == identifier:
            return user
    return None
