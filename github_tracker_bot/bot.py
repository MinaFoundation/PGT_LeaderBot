import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, field_validator

import aioschedule as schedule

from github_tracker_bot.bot_functions import get_all_results_from_sheet_by_date

import config
from log_config import get_logger

logger = get_logger(__name__)

app = FastAPI()
scheduler_task = None


class ScheduleControl(BaseModel):
    action: str
    interval_minutes: int = None


class TaskTimeFrame(BaseModel):
    since: str = Field(...)
    until: str = Field(...)

    @field_validator("since", "until")
    def validate_datetime(cls, value):
        try:
            parsed_date = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed_date.day != int(value[8:10]):
                raise ValueError
            return value
        except ValueError as e:
            raise ValueError("Datetime must be in ISO 8601 format") from e


def get_dates_for_today():
    today = datetime.now(timezone.utc)
    since_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    until_date = since_date + timedelta(days=1)
    return since_date.isoformat(), until_date.isoformat()


async def run_scheduled_task():
    try:
        since_date, until_date = get_dates_for_today()
        logger.info(f"Getting results between {since_date} and {until_date}")
        await get_all_results_from_sheet_by_date(
            config.SPREADSHEET_ID, since_date, until_date
        )
    except Exception as e:
        logger.error(f"An error occurred while running the scheduled task: {e}")
        raise


async def scheduler(interval_minutes):
    schedule.every(interval_minutes).minutes.do(run_scheduled_task)
    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)


@app.post("/run-task")
async def run_task(time_frame: TaskTimeFrame):
    try:
        await get_all_results_from_sheet_by_date(
            config.SPREADSHEET_ID, time_frame.since, time_frame.until
        )
        return {"message": "Task run successfully with provided times"}
    except Exception as e:
        logger.error(f"An error occurred while running the task: {e}")
        return {"message": f"An error occurred: {e}"}


@app.post("/control-scheduler")
async def control_scheduler(control: ScheduleControl):
    global scheduler_task

    if control.action == "start":
        if scheduler_task is None or scheduler_task.cancelled():
            interval_minutes = (
                control.interval_minutes or 1
            )  # Default to 1 minute if not specified
            scheduler_task = asyncio.create_task(scheduler(interval_minutes))
            return {
                "message": "Scheduler started with interval of {} minutes".format(
                    interval_minutes
                )
            }
        else:
            return {"message": "Scheduler is already running"}

    elif control.action == "stop":
        if scheduler_task and not scheduler_task.cancelled():
            scheduler_task.cancel()
            scheduler_task = None
            return {"message": "Scheduler stopped"}
        return {"message": "Scheduler is not running"}

    else:
        raise HTTPException(status_code=400, detail="Invalid action specified")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
