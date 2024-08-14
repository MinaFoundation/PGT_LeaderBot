import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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

        headers = [header.strip() for header in data[0]]
        formatted_data = []

        for row in data[1:]:
            row_data = [row[i].strip() if i < len(row) else "" for i in range(len(headers))]
            user_data = {headers[i]: row_data[i] for i in range(len(headers))}

            for i in range(len(headers)):
                if i < len(row_data):
                    user_data[headers[i]] = row_data[i]
                else:
                    user_data[headers[i]] = ""

            if "REPOSITORIES" in user_data:
                user_data["REPOSITORIES"] = [
                    repo.strip()
                    for repo in user_data["REPOSITORIES"].split(",")
                    if repo.strip()
                ]

            formatted_data.append(user_data)

        logger.debug(json.dumps(formatted_data, indent=2))
        return formatted_data
    except Exception as e:
        logger.error(f"Failed to read Google Sheets data: {e}")
        return []


if __name__ == "__main__":
    read_sheet(SPREADSHEET_ID)
