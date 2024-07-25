import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import discord
from discord import app_commands

import config
from log_config import get_logger
from sheet_functions import format_for_discord, read_sheet

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
    await message.channel.send(format_for_discord(read_sheet(config.SPREADSHEET_ID)))


client.run(config.DISCORD_TOKEN)
