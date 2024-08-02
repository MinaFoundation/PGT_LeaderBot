import sys
import os
import utils

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from datetime import datetime, timedelta, timezone

from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException, Query, Depends, Request, status
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from pydantic import BaseModel, Field, field_validator

import aioschedule as schedule

from github_tracker_bot.bot_functions import (
    get_all_results_from_sheet_by_date,
    get_user_results_from_sheet_by_date,
)

import config
from log_config import get_logger

logger = get_logger(__name__)

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

app = FastAPI()

limiter = Limiter(key_func=get_remote_address, default_limits=["5/minute"])

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

scheduler_task = None


class ScheduleControl(BaseModel):
    action: str
    interval_minutes: int = 1


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


@app.middleware("http")
async def check_auth_token(request: Request, call_next):
    discord_token = config.DISCORD_TOKEN
    client_id = config.DISCORD_CLIENT_ID
    client_secret = config.DISCORD_CLIENT_SECRET

    auth_token = utils.hasher(discord_token, client_id, client_secret)

    request_token = request.headers.get("Authorization")
    if request_token != auth_token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Unauthorized"},
        )
    response = await call_next(request)
    return response


@app.middleware("http")
async def ip_whitelist(request: Request, call_next):
    client_ip = request.client.host
    if client_ip not in config.ALLOWED_IPS:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"message": "Forbidden: IP address not allowed"},
        )
    response = await call_next(request)
    return response


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


@app.post("/run-task-for-user")
async def run_task_for_user(
    time_frame: TaskTimeFrame,
    username: str = Query(...),
):
    try:
        await get_user_results_from_sheet_by_date(
            username, config.SPREADSHEET_ID, time_frame.since, time_frame.until
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
