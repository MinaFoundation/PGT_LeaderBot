import sys
import os

from fastapi.responses import RedirectResponse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Query, Depends, Request, status
from fastapi.security import (
    OAuth2AuthorizationCodeBearer,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from pydantic import BaseModel, Field, field_validator

import aioschedule as schedule
import httpx

from github_tracker_bot.bot_functions import (
    get_all_results_from_sheet_by_date,
    get_user_results_from_sheet_by_date,
)

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


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

TOKEN_URL = 'https://discord.com/api/oauth2/token'
API_URL = 'https://discord.com/api/users/@me'

class User(BaseModel):
    id: str
    username: str
    discriminator: str

async def get_current_user(token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://discord.com/api/users/@me',
            headers={'Authorization': f'Bearer {token}'}
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_info = response.json()
        return User(**user_info)

@app.get("/login")
def login():
    oauth2_url = config.DISCORD_OAUTH_URL
    return RedirectResponse(url=oauth2_url)


@app.get("/callback")
async def callback(code: str):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            TOKEN_URL,
            data={
                'client_id': config.DISCORD_CLIENT_ID,
                'client_secret': config.DISCORD_CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': config.DISCORD_REDIRECT_URI
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        token_response.raise_for_status()
        tokens = token_response.json()
        access_token = tokens['access_token']

        user_response = await client.get(
            API_URL,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        user_response.raise_for_status()
        user_info = user_response.json()

    return user_info


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
    user: User = Depends(get_current_user),
):
    if user["id"] != config.DISCORD_BOT_USER_ID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

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
