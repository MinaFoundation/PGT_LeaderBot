import json
import os
import sys

from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import aiohttp
import discord
from discord import app_commands

from discord.ext import tasks
from datetime import datetime

import config
from log_config import get_logger
from sheet_functions import (
    create_new_spreadsheet,
    share_spreadsheet,
    fill_created_spreadsheet_with_users_except_ai_decisions,
    update_created_spreadsheet_with_users_except_ai_decisions,
    create_leaderboard_sheet,
    write_users_to_csv,
    write_ai_decisions_to_csv,
    write_users_to_csv_monthly,
)
from leaderboard_functions import (
    create_leaderboard_by_month,
    format_leaderboard_for_discord,
    format_streaks_for_discord,
)
from db_functions import (
    insert_discord_users,
    get_ai_decisions_by_user_and_timeframe,
    calculate_monthly_streak,
)
from modals import UserModal
from helpers import csv_to_structured_string
import utils

logger = get_logger(__name__)

intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

spread_sheet_id = None
auto_post_task = None
auto_post_tasks = {}
task_details = {}

AUTH_TOKEN = utils.hasher(
    config.DISCORD_TOKEN, config.DISCORD_CLIENT_ID, config.DISCORD_CLIENT_SECRET
)


@client.event
async def on_ready():
    try:
        await tree.sync(guild=discord.Object(id=config.GUILD_ID))
        logger.info(f"We have logged in as {client.user}")
    except Exception as e:
        logger.error(f"Error during on_ready: {e}")


@client.event
async def on_message(message):
    try:
        if message.author == client.user:
            return
    except Exception as e:
        logger.error(f"Error processing message: {e}")


@tree.command(
    name="commits-sheet-create",
    description="It will create a google sheet with the contributions data",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(
    interaction: discord.Interaction, spreadsheet_name: str, email_address: str = None
):
    global spread_sheet_id
    try:
        await interaction.response.defer()
        channel = interaction.channel

        created_spreadsheet_id = create_new_spreadsheet(spreadsheet_name)

        share_spreadsheet(created_spreadsheet_id, email_address or config.GMAIL_ADDRESS)
        res = fill_created_spreadsheet_with_users_except_ai_decisions(
            created_spreadsheet_id
        )

        await interaction.followup.send(
            f"Spreadsheet is created with id: `{created_spreadsheet_id}` and name `{spreadsheet_name}`. "
            f"You can see the spreadsheet in this link: https://docs.google.com/spreadsheets/d/{created_spreadsheet_id}"
        )
        spread_sheet_id = created_spreadsheet_id
    except Exception as e:
        logger.error(f"Error in commits-sheet-create command: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


@tree.command(
    name="commits-sheet-update",
    description="It will update the google sheet with the updated contributions data",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(interaction: discord.Interaction, spreadsheet_id: str):
    global spread_sheet_id
    try:
        await interaction.response.defer()
        channel = interaction.channel

        updated_spreadsheet_id = (
            update_created_spreadsheet_with_users_except_ai_decisions(spreadsheet_id)
        )

        await interaction.followup.send(
            f"Spreadsheet is updated with id: `{spread_sheet_id}`. "
            f"You can see the spreadsheet in this link: https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        )

        spread_sheet_id = updated_spreadsheet_id
    except Exception as e:
        logger.error(f"Error in commits-sheet-update command: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


@tree.command(
    name="main-sheet-edit",
    description="Edit Google Sheets from Discord",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(interaction: discord.Interaction, operation: str):
    try:
        if operation not in ["insert", "update", "add_repo", "delete"]:
            await interaction.followup.send(
                "Invalid operation. Please choose one of: insert, update, add_repo, delete.",
                ephemeral=True,
            )
            return

        modal = UserModal(operation=operation)
        await interaction.response.send_modal(modal)
    except Exception as e:
        logger.error(f"Error in main-sheet-edit command: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


@tree.command(
    name="leaderboard-create",
    description="It will create or update leaderboard",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(
    interaction: discord.Interaction, spreadsheet_id: str = None, date: str = None
):
    global spread_sheet_id
    try:
        await interaction.response.defer()
        channel = interaction.channel

        if date:
            year, month = date.split("-")
        else:
            now = datetime.now()
            formatted_date = now.strftime("%Y-%m")
            year, month = formatted_date.split("-")

        leaderboard = create_leaderboard_by_month(year, month)
        create_leaderboard_sheet(
            spreadsheet_id or spread_sheet_id, leaderboard, year, month
        )
        messages = format_leaderboard_for_discord(leaderboard)
        for msg in messages:
            await interaction.followup.send(msg, ephemeral=True)
    except Exception as e:
        logger.error(f"Error in leaderboard-create command: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


@tree.command(
    name="leaderboard-view",
    description="It will show leaderboard in the discord channel",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(
    interaction: discord.Interaction, thread_id: str, date: str = None
):
    await interaction.response.defer()
    channel = interaction.channel

    try:
        thread = await interaction.guild.fetch_channel(thread_id)
        if not isinstance(thread, discord.Thread):
            raise ValueError("The provided ID does not belong to a thread.")

        if date:
            year, month = date.split("-")
        else:
            now = datetime.now()
            formatted_date = now.strftime("%Y-%m")
            year, month = formatted_date.split("-")

        leaderboard = create_leaderboard_by_month(year, month)
        messages = format_leaderboard_for_discord(leaderboard)

        bot_user_id = interaction.client.user.id
        async for message in thread.history(limit=None):
            if message.author.id == bot_user_id:
                await message.delete()

        for msg in messages:
            await thread.send(msg)

        await interaction.followup.send(
            f"Posted to {thread_id} successfully.", ephemeral=True
        )

    except Exception as e:
        logger.error(f"Error in leaderboard-view command: {e}")
        await interaction.followup.send(f"Please check your input: {e}", ephemeral=True)


@tree.command(
    name="leaderboard-start-auto-post",
    description="It will automatically post the leaderboard every day at a specified time",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(
    interaction: discord.Interaction, date: str, time: str, spreadsheet_id: str = None
):
    global auto_post_task, task_details
    try:
        await interaction.response.defer()
        channel = interaction.channel

        year, month = date.split("-")
        hour, minute = map(int, time.split(":"))

        task_id = f"{year}-{month}"

        task_details[task_id] = {
            "year": year,
            "month": month,
            "spreadsheet_id": spreadsheet_id or spread_sheet_id,
            "hour": hour,
            "minute": minute,
            "channel": channel,
        }

        if not task_details[task_id]["spreadsheet_id"]:
            await interaction.followup.send(
                f"Spreadsheet id is missing; it will not update the spreadsheet!",
                ephemeral=True,
            )

        if task_id not in auto_post_tasks or not auto_post_tasks[task_id].is_running():
            auto_post_tasks[task_id] = tasks.loop(minutes=1)(
                auto_post_leaderboard(task_id)
            )
            auto_post_tasks[task_id].start()

        await interaction.followup.send(
            f"Auto-post leaderboard task started for {date} at {time}.", ephemeral=True
        )
    except Exception as e:
        logger.error(f"Error in leaderboard-start-auto-post command: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


@tree.command(
    name="leaderboard-stop-auto-post",
    description="It will stop the auto-post leaderboard task for a specific date (YYYY-MM)",
    guild=discord.Object(id=config.GUILD_ID),
)
async def leaderboard_stop_auto_post(interaction: discord.Interaction, date: str):
    try:
        await interaction.response.defer()

        if date in auto_post_tasks and auto_post_tasks[date].is_running():
            auto_post_tasks[date].cancel()
            await interaction.followup.send(
                f"Auto-post leaderboard task stopped for {date}.", ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"No auto-post leaderboard task is currently running for {date}.",
                ephemeral=True,
            )
    except Exception as e:
        logger.error(f"Error in leaderboard-stop-auto-post command: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


def auto_post_leaderboard(task_id):
    async def inner():
        try:
            now = datetime.now()
            details = task_details[task_id]
            if now.hour == details["hour"] and now.minute == details["minute"]:
                leaderboard = create_leaderboard_by_month(
                    details["year"], details["month"]
                )
                create_leaderboard_sheet(
                    details["spreadsheet_id"],
                    leaderboard,
                    details["year"],
                    details["month"],
                )
                messages = format_leaderboard_for_discord(leaderboard)
                channel = details["channel"]
                bot_user_id = client.user.id
                async for message in channel.history(limit=None):
                    if message.author.id == bot_user_id:
                        await message.delete()
                for msg in messages:
                    await channel.send(msg)
        except Exception as e:
            logger.error(f"Error in auto_post_leaderboard task {task_id}: {e}")

    return inner


@tree.command(
    name="leaderboard-closure-month",
    description="It will create forum thread for leaderboard in the discord forum channel",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(
    interaction: discord.Interaction, date: str = None, commit_filter: int = 10
):
    await interaction.response.defer()
    channel = interaction.channel

    try:
        forum_channel_id = int(config.LEADERBOARD_FORUM_CHANNEL_ID)
        forum_channel = interaction.guild.get_channel(forum_channel_id)
        if date:
            year, month = date.split("-")
            date_obj = datetime.strptime(f"{year}-{month}", "%Y-%m")
        else:
            now = datetime.now()
            date_obj = now
            formatted_date = now.strftime("%Y-%m")
            year, month = formatted_date.split("-")

        leaderboard = create_leaderboard_by_month(year, month, commit_filter)
        messages = format_leaderboard_for_discord(leaderboard, date, True)
        month_name = date_obj.strftime("%B")

        thread_title = f"Leaderboard | {year} {month_name}"
        thread, _ = await forum_channel.create_thread(
            name=thread_title, content=messages[0]
        )

        if len(messages) > 0:
            for msg in messages[1:]:
                await thread.send(msg)

        file_path = "user_data.csv"
        result = write_users_to_csv_monthly(file_path, date)

        if "Successfully" in result:
            await thread.send(file=discord.File(file_path))
            os.remove(file_path)

        await interaction.followup.send(
            f"Leaderboard thread created: {thread.jump_url}", ephemeral=True
        )

    except Exception as e:
        logger.error(f"Error in leaderboard-closure-month: {e}")
        await interaction.followup.send(f"Please check your input: {e}", ephemeral=True)


@tree.command(
    name="get-monthly-streaks",
    description="Gets monthly streaks of users and sends it to channel.",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(interaction: discord.Integration, date: str = None):
    try:
        await interaction.response.defer()

        forum_channel_id = int(config.LEADERBOARD_FORUM_CHANNEL_ID)
        forum_channel = interaction.guild.get_channel(forum_channel_id)
        if date:
            year, month = date.split("-")
            date_obj = datetime.strptime(f"{year}-{month}", "%Y-%m")
        else:
            now = datetime.now()
            date_obj = now
            formatted_date = now.strftime("%Y-%m")
            year, month = formatted_date.split("-")
            date = f"{year}-{month}"

        month_name = date_obj.strftime("%B")
        streaks = calculate_monthly_streak(date)

        messages = format_streaks_for_discord(streaks, month_name)
        thread_title = f"Streaks | {year} {month_name}"
        thread, _ = await forum_channel.create_thread(
            name=thread_title, content=messages[0]
        )

        if len(messages) > 0:
            for msg in messages[1:]:
                await thread.send(msg)

        await interaction.followup.send(
            f"Streaks thread created: {thread.jump_url}", ephemeral=True
        )

    except Exception as e:
        logger.error(f"Error in get monthly streaks command: {e}")
        await interaction.followup.send(f"Please check your input: {e}", ephemeral=True)


@tree.command(
    name="get-members-and-insert-to-db",
    description="Get and insert all members of the guild to the db in new collection",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(interaction: discord.Interaction):
    await interaction.response.defer()
    channel = interaction.channel

    try:
        members = interaction.guild.members
        member_list = [{member.name: member.id} for member in members]
        logger.info(member_list)
        result = insert_discord_users(member_list)
        if result:
            await interaction.followup.send(f"Users successfully inserted")
    except Exception as e:
        logger.error(f"An error occured: {e}")
        await interaction.followup.send(f"An error occured: {e}", ephemeral=True)


def convert_to_iso8601(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    iso8601_str = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

    return iso8601_str


async def fetch(session, url, method="GET", data=None, params=None):
    async with session.request(method, url, json=data, params=params) as response:
        return await response.json()


@tree.command(
    name="run-task",
    description="Run the task for a specific timeframe.",
    guild=discord.Object(id=config.GUILD_ID),
)
async def run_task_for_user(interaction: discord.Interaction, since: str, until: str):
    try:
        since = convert_to_iso8601(since)
        until = convert_to_iso8601(until)

        await interaction.response.defer()
        url = f"{config.GTP_ENDPOINT}/run-task"
        payload = {"since": since, "until": until}
        headers = {"Authorization": AUTH_TOKEN}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response_data = await response.json()

        await interaction.followup.send(response_data["message"])
    except Exception as e:
        logger.error(f"Error in run-task-for-user command: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


@tree.command(
    name="run-task-for-user",
    description="Run the task for a specific user with the specified time frame",
    guild=discord.Object(id=config.GUILD_ID),
)
async def run_task_for_user(
    interaction: discord.Interaction, username: str, since: str, until: str
):
    try:
        since = convert_to_iso8601(since)
        until = convert_to_iso8601(until)

        await interaction.response.defer()
        url = f"{config.GTP_ENDPOINT}/run-task-for-user"
        payload = {"since": since, "until": until}
        params = {"username": username}
        headers = {"Authorization": AUTH_TOKEN}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, params=params, headers=headers
            ) as response:
                response_data = await response.json()

        await interaction.followup.send(response_data["message"])
    except Exception as e:
        logger.error(f"Error in run-task-for-user command: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


@tree.command(
    name="control-scheduler",
    description="Control the scheduler (start/stop) with an optional interval",
    guild=discord.Object(id=config.GUILD_ID),
)
async def control_scheduler(
    interaction: discord.Interaction, action: str, interval: int = 1
):
    try:
        await interaction.response.defer()
        url = f"{config.GTP_ENDPOINT}/control-scheduler"
        payload = {"action": action, "interval_minutes": interval}
        headers = {"Authorization": AUTH_TOKEN}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, params=None, headers=headers
            ) as response:
                response_data = await response.json()

        await interaction.followup.send(response_data["message"])
    except Exception as e:
        logger.error(f"Error in control-scheduler command: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


@tree.command(
    name="get-ai-decisions-by-user",
    description="Gets AI decisions as csv file for specific user between given dates.",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(
    interaction: discord.Interaction, username: str, since: str, until: str
):
    try:
        await interaction.response.defer()
        ai_decisions = get_ai_decisions_by_user_and_timeframe(username, since, until)

        file_path = f"ai_decisions_by_user_{username}.csv"
        result = write_ai_decisions_to_csv(file_path, ai_decisions)
        if "successful" in result:
            await interaction.channel.send(file=discord.File(file_path))
            os.remove(file_path)

        await interaction.followup.send("AI decisions here: ", ephemeral=True)
    except Exception as e:
        logger.error(f"Error in get-ai-decisions-by-user command: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


@tree.command(
    name="get-all-data-to-csv",
    description="Gets all db data and export it to csv.",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(interaction: discord.Interaction):
    try:
        await interaction.response.defer()

        file_path = "all_data.csv"
        result = write_users_to_csv(file_path)
        if "successfully" in result:
            await interaction.channel.send(file=discord.File(file_path))
            os.remove(file_path)

        await interaction.followup.send("All data is here: ", ephemeral=True)
    except Exception as e:
        logger.error(f"Error in get-all-data-to-csv command: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


@tree.command(
    name="get-blockchain-summary",
    description="Gets MINA Blockchain summary",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(interaction: discord.Interaction):
    try:
        await interaction.response.defer()

        url = "https://api.minaexplorer.com/summary"
        headers = {}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response_data = await response.json()

        res = json.dumps(response_data, indent=4)
        discord_message = f"```\n{res}\n```"

        await interaction.followup.send(discord_message)
    except Exception as e:
        logger.error(f"Error in get-blockchain-summary command: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


client.run(config.DISCORD_TOKEN)
