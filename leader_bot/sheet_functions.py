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

logger = get_logger(__name__)

SERVICE_ACCOUNT_FILE = GOOGLE_CREDENTIALS
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
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
