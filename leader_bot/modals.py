import discord
import os
import sys
import json
import aiohttp

from datetime import datetime
from github_tracker_bot.bot_functions import delete_all_data

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from discord.ui import Modal, TextInput
from typing import List
import config

from log_config import get_logger

logger = get_logger(__name__)


from sheet_functions import (
    insert_user,
    update_user,
    delete_user,
    add_repository_for_user,
)


class UserModal(Modal, title="User Information"):
    def __init__(
        self,
        operation: str,
        discord_handle: str = "",
        github_name: str = "",
        repositories: str = "",
    ):
        super().__init__(title="User Information")
        self.operation = operation

        self.discord_handle = TextInput(
            label="Discord Handle",
            placeholder="Enter your Discord handle",
            default=discord_handle,
        )
        self.github_name = TextInput(
            label="GitHub Name",
            placeholder="Enter your GitHub name",
            default=github_name,
        )
        self.repositories = TextInput(
            label="Repositories (comma separated)",
            placeholder="Enter repositories",
            default=repositories,
        )

        self.add_item(self.discord_handle)
        if operation in ["insert", "update"]:
            self.add_item(self.github_name)
            self.add_item(self.repositories)
        elif operation == "add_repo":
            self.add_item(self.repositories)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            discord_handle = self.discord_handle.value
            github_name = self.github_name.value
            repositories = self.repositories.value.split(",")

            if self.operation == "insert":
                insert_user(discord_handle, github_name, repositories)
            elif self.operation == "update":
                updated_user = update_user(discord_handle, github_name, repositories)
                if not updated_user:
                    await interaction.followup.send(
                        f"Cannot found user named {discord_handle}"
                    )
            elif self.operation == "add_repo":
                for repo in repositories:
                    add_repository_for_user(discord_handle, repo)
            elif self.operation == "delete":
                updated_user = delete_user(discord_handle)
                if not updated_user:
                    await interaction.followup.send(
                        f"User with Discord handle {discord_handle} not found."
                    )

            await interaction.followup.send(
                f"{self.operation.capitalize()} operation completed.", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error in on_submit: {e}")
            await interaction.followup.send(
                "Oops! Something went wrong.", ephemeral=True
            )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        logger.error(f"Error in on_error: {error}")
        await interaction.followup.send("Oops! Something went wrong.", ephemeral=True)


class UserDeletionModal(Modal, title="User Deletion"):
    def __init__(self, from_date: str = "", until_date: str = ""):
        super().__init__(title="User Deletion")

        self.initial_from_date = from_date
        self.initial_until_date = until_date

        self.discord_handle = TextInput(  ##TODO: clarify github or discord username
            label="Discord Handle",
            placeholder="Enter your Discord handle",
        )
        self.from_date = TextInput(
            label="From Date (YYYY-MM-DD)",
            placeholder="Enter the start date",
        )
        self.until_date = TextInput(
            label="Until Date (YYYY-MM-DD)",
            placeholder="Enter the end date",
        )

        self.add_item(self.discord_handle)
        self.add_item(self.from_date)
        self.add_item(self.until_date)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            discord_handle = self.discord_handle.value.strip()
            modal_from_date = self.from_date.value.strip()
            modal_until_date = self.until_date.value.strip()

            if (
                self.initial_from_date != modal_from_date
                or self.initial_until_date != modal_until_date
            ):
                await interaction.followup.send(
                    "Dates do not match. Please try again.", ephemeral=True
                )
                return

            elif self.initial_until_date < self.initial_from_date:
                await interaction.followup.send(
                    "Until date shouldn't be fewer than From date. Please try again.",
                    ephemeral=True,
                )
                return

            await delete_all_data(modal_from_date, modal_until_date)

            await interaction.followup.send(
                f"All data between {modal_from_date} and {modal_until_date} has been deleted.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error in on_submit: {e}")
            await interaction.followup.send(
                "Oops! Something went wrong.", ephemeral=True
            )


class SheetCreationModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Create Sheet")
        self.spreadsheet_name = discord.ui.TextInput(
            label="Spreadsheet Name",
            placeholder="Enter spreadsheet name..."
        )
        self.email = discord.ui.TextInput(
            label="Email Address (Optional)",
            required=False,
            placeholder="Enter email address..."
        )
        
    async def on_submit(self, interaction: discord.Interaction):
        # Implementation of sheet creation logic
        pass


class LeaderboardCreateModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Create/Update Leaderboard")
        self.spreadsheet_id = discord.ui.TextInput(
            label="Spreadsheet ID (Optional)",
            required=False,
            placeholder="Enter spreadsheet ID..."
        )
        self.date = discord.ui.TextInput(
            label="Date (YYYY-MM)",
            placeholder="e.g., 2024-03",
            required=False
        )
        
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            date = self.date.value if self.date.value else None
            spreadsheet_id = self.spreadsheet_id.value if self.spreadsheet_id.value else None
            
            if date:
                year, month = date.split("-")
            else:
                now = datetime.now()
                year, month = now.strftime("%Y-%m").split("-")

            leaderboard = create_leaderboard_by_month(year, month)
            create_leaderboard_sheet(spreadsheet_id, leaderboard, year, month)
            messages = format_leaderboard_for_discord(leaderboard)
            
            for msg in messages:
                await interaction.followup.send(msg, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)


class LeaderboardViewModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="View Leaderboard")
        self.thread_id = discord.ui.TextInput(
            label="Thread ID",
            placeholder="Enter thread ID"
        )
        self.date = discord.ui.TextInput(
            label="Date (YYYY-MM)",
            placeholder="e.g., 2024-03",
            required=False
        )
        
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            thread = await interaction.guild.fetch_channel(self.thread_id.value)
            date = self.date.value if self.date.value else None
            
            if date:
                year, month = date.split("-")
            else:
                now = datetime.now()
                year, month = now.strftime("%Y-%m").split("-")

            leaderboard = create_leaderboard_by_month(year, month)
            messages = format_leaderboard_for_discord(leaderboard)
            
            bot_user_id = interaction.client.user.id
            async for message in thread.history(limit=None):
                if message.author.id == bot_user_id:
                    await message.delete()

            for msg in messages:
                await thread.send(msg)

            await interaction.followup.send("Leaderboard posted successfully!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)


class TaskRunModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Run Task")
        self.since = discord.ui.TextInput(
            label="Since (YYYY-MM-DD)",
            placeholder="Enter start date"
        )
        self.until = discord.ui.TextInput(
            label="Until (YYYY-MM-DD)",
            placeholder="Enter end date"
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            since = convert_to_iso8601(self.since.value)
            until = convert_to_iso8601(self.until.value)
            
            url = f"{config.GTP_ENDPOINT}/run-task"
            payload = {"since": since, "until": until}
            headers = {"Authorization": config.SHARED_SECRET}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    response_data = await response.json()

            await interaction.followup.send(response_data["message"], ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)


class SchedulerStartModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Start Scheduler")
        self.interval = discord.ui.TextInput(
            label="Interval (minutes)",
            placeholder="Enter interval in minutes",
            default="1"
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            interval = int(self.interval.value)
            url = f"{config.GTP_ENDPOINT}/control-scheduler"
            payload = {"action": "start", "interval_minutes": interval}
            headers = {"Authorization": config.SHARED_SECRET}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    response_data = await response.json()

            await interaction.followup.send(response_data["message"], ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)
