import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from log_config import get_logger

logger = get_logger(__name__)

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import GOOGLE_CREDENTIALS, SPREADSHEET_ID

SERVICE_ACCOUNT_FILE = GOOGLE_CREDENTIALS

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)

RANGE_NAME = "A1:D99999"

def read_sheet():
    sheet = service.spreadsheets()
    result = (
        sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    )
    values = result.get("values", [])
    if not values:
        logger.debug("No data found.")
    else:
        for row in values:
            logger.debug(row)


if __name__ == "__main__":
    read_sheet()
