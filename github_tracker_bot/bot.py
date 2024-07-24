import asyncio
import schedule
import time
from datetime import datetime, timedelta, timezone
from bot_functions import get_all_results_from_sheet_by_date

import config
from log_config import get_logger

logger = get_logger(__name__)


def get_dates_for_today():
    today = datetime.now(timezone.utc)
    since_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    until_date = since_date + timedelta(days=1)
    return since_date.isoformat(), until_date.isoformat()


def run_scheduled_task():
    try:
        since_date, until_date = get_dates_for_today()
        asyncio.run(
            get_all_results_from_sheet_by_date(
                config.SPREADSHEET_ID, since_date, until_date
            )
        )
    except Exception as e:
        logger.error(
            f"An error occurred while running the scheduled task for between {since_date} and {until_date}: {e}"
        )


# Schedule everyday
# schedule.every().day.at("00:01").do(run_scheduled_task)

# Schedule every 1 mins for testing
schedule.every(1).minutes.do(run_scheduled_task)

if __name__ == "__main__":
    print("Scheduler is running. Press Ctrl+C to exit.")
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"An error occurred in the scheduler loop: {e}")
        time.sleep(1)
