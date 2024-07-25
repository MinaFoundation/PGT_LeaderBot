import os
import sys
import json

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
)

logger = get_logger(__name__)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


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
    await interaction.response.defer()
    channel = interaction.channel

    created_spreadsheet_id = create_new_spreadsheet(spreadsheet_name)

    share_spreadsheet(created_spreadsheet_id, email_address or config.GMAIL_ADDRESS)
    res = fill_created_spreadsheet_with_users_except_ai_decisions(
        created_spreadsheet_id
    )

    print(res)

    await interaction.followup.send(
        f"Spreadsheet is created with id: `{created_spreadsheet_id}` and name `{spreadsheet_name}`. "
        f"You can see the spreadsheet in this link: https://docs.google.com/spreadsheets/d/{created_spreadsheet_id}"
    )


client.run(config.DISCORD_TOKEN)
