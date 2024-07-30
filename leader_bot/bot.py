import os
import sys
import json

from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import discord
from discord import app_commands

from discord.ext import tasks
from datetime import datetime, timedelta

import config
from log_config import get_logger
from sheet_functions import (
    format_for_discord,
    read_sheet,
    create_new_spreadsheet,
    share_spreadsheet,
    insert_user,
    fill_created_spreadsheet_with_users_except_ai_decisions,
    update_created_spreadsheet_with_users_except_ai_decisions,
    create_leaderboard_sheet,
)
from leaderboard_functions import (
    create_leaderboard_by_month,
    format_leaderboard_for_discord,
)
from modals import UserModal

logger = get_logger(__name__)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

spread_sheet_id = None
auto_post_task = None
auto_post_tasks = {}
task_details = {}


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
            await interaction.followup.send(msg)
    except Exception as e:
        logger.error(f"Error in leaderboard-create command: {e}")
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


@tree.command(
    name="leaderboard-view",
    description="It will show leaderboard in the discord channel",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(interaction: discord.Interaction, date: str = None):
    await interaction.response.defer()
    channel = interaction.channel

    try:
        if date:
            year, month = date.split("-")
        else:
            now = datetime.now()
            formatted_date = now.strftime("%Y-%m")
            year, month = formatted_date.split("-")

        leaderboard = create_leaderboard_by_month(year, month)
        messages = format_leaderboard_for_discord(leaderboard)
        for msg in messages:
            await interaction.followup.send(msg)
    except Exception as e:
        logger.error(f"Error in leaderboard-view command: {e}")
        await interaction.followup.send(f"Please check your input: {e}", ephemeral=True)


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
                f"Spreadsheet id is missing; it will not update the spreadsheet!"
            )

        if task_id not in auto_post_tasks or not auto_post_tasks[task_id].is_running():
            auto_post_tasks[task_id] = tasks.loop(minutes=1)(
                auto_post_leaderboard(task_id)
            )
            auto_post_tasks[task_id].start()

        await interaction.followup.send(
            f"Auto-post leaderboard task started for {date} at {time}."
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
                f"Auto-post leaderboard task stopped for {date}."
            )
        else:
            await interaction.followup.send(
                f"No auto-post leaderboard task is currently running for {date}."
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
                for msg in messages:
                    await channel.send(msg)
        except Exception as e:
            logger.error(f"Error in auto_post_leaderboard task {task_id}: {e}")

    return inner


client.run(config.DISCORD_TOKEN)
