from typing import List
import github_tracker_bot.read_sheet as rs
import github_tracker_bot.redis_data_handler as rd

async def get_sheet_data(spreadsheet_id):
    sheet_data: list = await rs.read_sheet(spreadsheet_id)
    return sheet_data


async def spreadsheet_to_list_of_user(sheet_data) -> List[rd.User]:
    ss_users: List[rd.User]

    if not sheet_data:
        return []

    keys = []

    for k in keys[0]:
        keys.append(k)

    for user_data in sheet_data:
        user_handle = user_data[keys[0]]
        github_name = user_data[keys[1]]
        repositories = user_data[keys[2]]

        user = rd.User(user_handle, github_name, repositories)
        ss_users.append(user)

    return ss_users