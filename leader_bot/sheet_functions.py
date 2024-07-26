import os
import sys
import json
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config

from log_config import get_logger
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from config import GOOGLE_CREDENTIALS, SPREADSHEET_ID

from db_functions import fetch_db_get_users

logger = get_logger(__name__)

SERVICE_ACCOUNT_FILE = GOOGLE_CREDENTIALS

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
RANGE_NAME = "A1:D99999"


def get_google_sheets_service():
    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build("sheets", "v4", credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Failed to create Google Sheets service: {e}")


def get_google_drive_service():
    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build("drive", "v3", credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Failed to create Google Drive service: {e}")
        None


def read_sheet(spreadsheet_id):
    service = get_google_sheets_service()
    try:
        sheet = service.spreadsheets()
        result = (
            sheet.values().get(spreadsheetId=spreadsheet_id, range=RANGE_NAME).execute()
        )
        data = result.get("values", [])
        if not data:
            logger.debug("No data found.")
            return []

        return data

    except Exception as e:
        logger.error(f"Failed to read Google Sheets data: {e}")
        return []


def create_new_spreadsheet(title: str):
    service = get_google_sheets_service()
    try:
        spreadsheet = {"properties": {"title": title}}
        spreadsheet = (
            service.spreadsheets()
            .create(body=spreadsheet, fields="spreadsheetId")
            .execute()
        )
        logger.info(f"Spreadsheet created with ID: {spreadsheet.get('spreadsheetId')}")
        return spreadsheet.get("spreadsheetId")
    except Exception as e:
        logger.error(f"Failed to create new spreadsheet: {e}")
        return None


def create_leaderboard_sheet(
    spreadsheet_id: str, leaderboard: List[List[str]], year: str, month: str
):
    service = get_google_sheets_service()
    sheet_title = f"Leaderboard {year}-{month}"

    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_list = spreadsheet.get("sheets", [])

        sheet_exists = False
        for sheet in sheet_list:
            if sheet["properties"]["title"] == sheet_title:
                sheet_exists = True
                break

        if not sheet_exists:
            create_request = {"addSheet": {"properties": {"title": sheet_title}}}
            create_body = {"requests": [create_request]}
            response = (
                service.spreadsheets()
                .batchUpdate(spreadsheetId=spreadsheet_id, body=create_body)
                .execute()
            )

            new_sheet_id = response["replies"][0]["addSheet"]["properties"]["sheetId"]
            logger.info(f"Leaderboard sheet created with ID: {new_sheet_id}")
        else:
            logger.info(f"Sheet with title {sheet_title} already exists.")

        range_name = sheet_title
        value_range_body = {"range": range_name, "values": leaderboard}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=value_range_body,
        ).execute()

        logger.info("Leaderboard data has been written to the sheet.")

    except Exception as e:
        logger.error(f"Failed to create leaderboard sheet: {e}")


def fill_created_spreadsheet_with_users_except_ai_decisions(spreadsheed_id):
    try:
        column_names = [
            [
                "User Handle",
                "Github Name",
                "Repositories",
                "Total Daily Contribution Number",
                "Total Qualified Daily Contribution Number",
                "Qualified Daily Contribution Number by Month",
                "Qualified Daily Contribution Dates",
                "Best Streak",
            ]
        ]

        column_insert_result = insert_data(spreadsheed_id, "A1", column_names)

        users = fetch_db_get_users()
        data = []

        for user in users:
            data.append(
                [
                    user.user_handle,
                    user.github_name,
                    ", ".join(user.repositories),
                    user.total_daily_contribution_number,
                    user.total_qualified_daily_contribution_number,
                    str(user.qualified_daily_contribution_number_by_month),
                    str(user.qualified_daily_contribution_dates),
                    user.qualified_daily_contribution_streak,
                ]
            )

        result = insert_data(spreadsheed_id, "A1", data)
        return result
    except Exception as e:
        logger.error(f"Failed to fill spreadsheet: {e}")


def update_created_spreadsheet_with_users_except_ai_decisions(spreadsheed_id):
    try:
        users = fetch_db_get_users()
        data = []

        for user in users:
            data.append(
                [
                    user.user_handle,
                    user.github_name,
                    ", ".join(user.repositories),
                    user.total_daily_contribution_number,
                    user.total_qualified_daily_contribution_number,
                    str(user.qualified_daily_contribution_number_by_month),
                    str(user.qualified_daily_contribution_dates),
                    user.qualified_daily_contribution_streak,
                ]
            )

        result = update_data(spreadsheed_id, "A2", data)
        return result
    except Exception as e:
        logger.error(f"Failed to fill spreadsheet: {e}")


def share_spreadsheet(spreadsheet_id: str, email: str):
    drive_service = get_google_drive_service()
    if drive_service is None:
        logger.error("Google Sheets service is not available.")
        return None
    try:
        permissions = [{"type": "user", "role": "writer", "emailAddress": email}]
        for permission in permissions:
            drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission,
                supportsAllDrives=True,
            ).execute()
        logger.info(f"Spreadsheet {spreadsheet_id} shared with {email}")
    except Exception as e:
        logger.error(f"Failed to share spreadsheet: {e}")


# Example usage
# print(format_for_discord(read_sheet(config.SPREADSHEET_ID)))
def format_for_discord(data: List[List[str]]) -> str:
    if not data:
        return "No data found."

    headers = data[0]
    rows = data[1:]

    header_emoji = "🔹"
    row_emoji = "➡️"

    formatted_message = f"{header_emoji} " + " | ".join(headers) + "\n"
    formatted_message += "➖" * (len(headers) * 8) + "\n"

    for row in rows:
        formatted_message += f"{row_emoji} " + " | ".join(row) + "\n"

    return formatted_message


def insert_data(spreadsheet_id, range_name, values):
    service = get_google_sheets_service()
    try:
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )
        logger.info(f"{result.get('updates').get('updatedCells')} cells appended.")
        return result
    except Exception as e:
        logger.error(f"Failed to insert data into Google Sheets: {e}")
        return None


def update_data(spreadsheet_id, range_name, values):
    service = get_google_sheets_service()
    try:
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body=body,
            )
            .execute()
        )
        logger.info(f"{result.get('updatedCells')} cells updated.")
        return result
    except Exception as e:
        logger.error(f"Failed to update data in Google Sheets: {e}")
        return None


def insert_user(discord_handle: str, github_name: str, repositories: List[str]):
    data = [[discord_handle, github_name, ", ".join(repositories).strip()]]
    insert_data(config.SPREADSHEET_ID, "A1", data)


def add_repository_for_user(discord_handle: str, repository_link: str):
    data = read_sheet(config.SPREADSHEET_ID)
    if not data:
        logger.error("No data found in the spreadsheet.")
        return

    updated_data = []
    user_found = False
    for row in data:
        if row[0] == discord_handle:
            user_found = True
            current_repos = row[2].split(", ")
            if repository_link not in current_repos:
                current_repos.append(repository_link)
            row[2] = ", ".join(current_repos)
        updated_data.append(row)

    if not user_found:
        logger.error(f"User with Discord handle {discord_handle} not found.")
        return

    update_data(config.SPREADSHEET_ID, RANGE_NAME, updated_data)


def update_user(
    discord_handle: str, new_github_name: str = None, new_repositories: List[str] = None
):
    data = read_sheet(config.SPREADSHEET_ID)
    if not data:
        logger.error("No data found in the spreadsheet.")
        return

    updated_data = []
    user_found = False
    for row in data:
        if row[0] == discord_handle:
            user_found = True
            if new_github_name is not None:
                row[1] = new_github_name
            if new_repositories is not None:
                row[2] = ", ".join(new_repositories).strip()
        updated_data.append(row)

    if not user_found:
        logger.error(f"User with Discord handle {discord_handle} not found.")
        return

    clear_range = "A1:Z"
    clear_request = {"range": clear_range}
    service = get_google_sheets_service()
    try:
        service.spreadsheets().values().clear(
            spreadsheetId=config.SPREADSHEET_ID, range=clear_range, body=clear_request
        ).execute()
    except Exception as e:
        logger.error(f"Failed to clear Google Sheets data: {e}")

    update_data(config.SPREADSHEET_ID, RANGE_NAME, updated_data)


def delete_user(discord_handle: str):
    data = read_sheet(config.SPREADSHEET_ID)
    if not data:
        logger.error("No data found in the spreadsheet.")
        return

    updated_data = []
    user_found = False
    for row in data:
        if row[0] != discord_handle:
            updated_data.append(row)
        else:
            user_found = True

    if not user_found:
        logger.error(f"User with Discord handle {discord_handle} not found.")
        return

    clear_range = "A1:Z"
    clear_request = {"range": clear_range}
    service = get_google_sheets_service()
    try:
        service.spreadsheets().values().clear(
            spreadsheetId=config.SPREADSHEET_ID, range=clear_range, body=clear_request
        ).execute()
    except Exception as e:
        logger.error(f"Failed to clear Google Sheets data: {e}")

    update_data(config.SPREADSHEET_ID, RANGE_NAME, updated_data)
