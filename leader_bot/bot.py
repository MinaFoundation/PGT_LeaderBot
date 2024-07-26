import os
import sys
import json

from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import discord
from discord import app_commands

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
    create_leaderboard_sheet
)
from leaderboard_functions import create_leaderboard_by_month

logger = get_logger(__name__)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

spread_sheet_id = None

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=config.GUILD_ID))
    logger.info(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return


@tree.command(
    name="commits-db",
    description="It will create a google sheet with the contributions data",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(
    interaction: discord.Interaction, spreadsheet_name: str, email_address: str = None
):
    global spread_sheet_id
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

@tree.command(
    name="commits-db-update",
    description="It will update the google sheet with the updated contributions data",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(
    interaction: discord.Interaction, spreadsheet_id: str
):
    global spread_sheet_id
    await interaction.response.defer()
    channel = interaction.channel

    updated_spreadsheet_id = update_created_spreadsheet_with_users_except_ai_decisions(spreadsheet_id)

    await interaction.followup.send(
        f"Spreadsheet is updated with id: `{updated_spreadsheet_id}`. "
        f"You can see the spreadsheet in this link: https://docs.google.com/spreadsheets/d/{updated_spreadsheet_id}"
    )

    spread_sheet_id = updated_spreadsheet_id

@tree.command(
    name="leaderboard-create",
    description="It will create leaderboard",
    guild=discord.Object(id=config.GUILD_ID),
)
async def on_command(
    interaction: discord.Interaction, spreadsheet_id: str = None, date: str = None
):
    global spread_sheet_id
    await interaction.response.defer()
    channel = interaction.channel

    if date:
        year, month = date.split('-')
    else:
        now = datetime.now()
        formatted_date = now.strftime("%Y-%m")
        year, month = formatted_date.split('-')

    leaderboard = create_leaderboard_by_month(year, month)
    create_leaderboard_sheet(spreadsheet_id or spread_sheet_id, leaderboard, year, month)
    await interaction.followup.send(str(leaderboard))


client.run(config.DISCORD_TOKEN)
