import discord
import os
import sys
import json
import aiohttp

from datetime import datetime
from discord.ext import tasks
from github_tracker_bot.bot_functions import delete_all_data
from leader_bot.utils import convert_to_iso8601
from leader_bot.db_functions import (
    calculate_monthly_streak,
    get_ai_decisions_by_user_and_timeframe,
)
from leader_bot.leaderboard_functions import (
    create_leaderboard_by_month,
    format_leaderboard_for_discord,
    format_streaks_for_discord,
)
from leader_bot.shared_state import task_details, auto_post_tasks, auto_post_leaderboard

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from discord.ui import Modal, TextInput
from typing import List
import config

from log_config import get_logger

logger = get_logger(__name__)


from sheet_functions import (
    create_leaderboard_sheet,
    create_new_spreadsheet,
    fill_created_spreadsheet_with_users_except_ai_decisions,
    insert_user,
    share_spreadsheet,
    update_created_spreadsheet_with_users_except_ai_decisions,
    update_user,
    delete_user,
    add_repository_for_user,
    write_ai_decisions_to_csv,
    write_all_data_of_user_to_csv_by_month,
    write_users_to_csv_monthly,
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
            label="Spreadsheet Name", placeholder="Enter spreadsheet name..."
        )
        self.email = discord.ui.TextInput(
            label="Email Address (Optional)",
            required=False,
            placeholder="Enter email address...",
        )

        # Add the TextInput components to the modal
        self.add_item(self.spreadsheet_name)
        self.add_item(self.email)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            spreadsheet_name = self.spreadsheet_name.value
            email = self.email.value if self.email.value else config.GMAIL_ADDRESS

            created_spreadsheet_id = create_new_spreadsheet(spreadsheet_name)
            share_spreadsheet(created_spreadsheet_id, email)
            res = fill_created_spreadsheet_with_users_except_ai_decisions(
                created_spreadsheet_id
            )

            await interaction.followup.send(
                f"Spreadsheet created successfully!\n"
                f"ID: `{created_spreadsheet_id}`\n"
                f"Name: `{spreadsheet_name}`\n"
                f"View it here: https://docs.google.com/spreadsheets/d/{created_spreadsheet_id}",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(
                f"Error creating spreadsheet: {str(e)}", ephemeral=True
            )


class LeaderboardCreateModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Create/Update Leaderboard")
        self.spreadsheet_id = discord.ui.TextInput(
            label="Spreadsheet ID (Optional)",
            required=False,
            placeholder="Enter spreadsheet ID...",
        )
        self.date = discord.ui.TextInput(
            label="Date (YYYY-MM)", placeholder="e.g., 2024-03", required=False
        )

        # Add the TextInput components to the modal
        self.add_item(self.spreadsheet_id)
        self.add_item(self.date)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            date = self.date.value if self.date.value else None
            spreadsheet_id = (
                self.spreadsheet_id.value if self.spreadsheet_id.value else None
            )

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
            label="Thread ID", placeholder="Enter thread ID"
        )
        self.date = discord.ui.TextInput(
            label="Date (YYYY-MM)", placeholder="e.g., 2024-03", required=False
        )

        # Add the TextInput components to the modal
        self.add_item(self.thread_id)
        self.add_item(self.date)

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

            await interaction.followup.send(
                "Leaderboard posted successfully!", ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)


class TaskRunModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Run Task")
        self.since = discord.ui.TextInput(
            label="Since (YYYY-MM-DD)", placeholder="Enter start date"
        )
        self.until = discord.ui.TextInput(
            label="Until (YYYY-MM-DD)", placeholder="Enter end date"
        )

        # Add the TextInput components to the modal
        self.add_item(self.since)
        self.add_item(self.until)

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
            default="1",
        )

        # Add the TextInput component to the modal
        self.add_item(self.interval)

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


class UserMonthlyDataModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Get User Monthly Data")
        self.username = discord.ui.TextInput(
            label="Username", placeholder="Enter username"
        )
        self.date = discord.ui.TextInput(
            label="Date (YYYY-MM)", placeholder="e.g., 2024-03"
        )

        # Add the TextInput components to the modal
        self.add_item(self.username)
        self.add_item(self.date)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            file_path = "user_monthly_data.csv"
            result = write_all_data_of_user_to_csv_by_month(
                file_path, self.username.value, self.date.value
            )

            if "successfully" in result:
                await interaction.channel.send(file=discord.File(file_path))
                os.remove(file_path)
                await interaction.followup.send(
                    "User monthly data has been exported.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "No data found for this user and month.", ephemeral=True
                )
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)


class AIDecisionsModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Get AI Decisions")
        self.username = discord.ui.TextInput(
            label="Username", placeholder="Enter username"
        )
        self.since = discord.ui.TextInput(
            label="Since (YYYY-MM-DD)", placeholder="Start date"
        )
        self.until = discord.ui.TextInput(
            label="Until (YYYY-MM-DD)", placeholder="End date"
        )

        # Add the TextInput components to the modal
        self.add_item(self.username)
        self.add_item(self.since)
        self.add_item(self.until)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            ai_decisions = get_ai_decisions_by_user_and_timeframe(
                self.username.value, self.since.value, self.until.value
            )

            file_path = f"ai_decisions_by_user_{self.username.value}.csv"
            result = write_ai_decisions_to_csv(file_path, ai_decisions)

            if "successful" in result:
                await interaction.channel.send(file=discord.File(file_path))
                os.remove(file_path)
                await interaction.followup.send(
                    "AI decisions have been exported.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "No AI decisions found for this period.", ephemeral=True
                )
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)


class UserTaskRunModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Run Task for User")
        self.username = discord.ui.TextInput(
            label="Username", placeholder="Enter username"
        )
        self.since = discord.ui.TextInput(
            label="Since (YYYY-MM-DD)", placeholder="Enter start date"
        )
        self.until = discord.ui.TextInput(
            label="Until (YYYY-MM-DD)", placeholder="Enter end date"
        )

        # Add the TextInput components to the modal
        self.add_item(self.username)
        self.add_item(self.since)
        self.add_item(self.until)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            since = convert_to_iso8601(self.since.value)
            until = convert_to_iso8601(self.until.value)

            url = f"{config.GTP_ENDPOINT}/run-task-for-user"
            payload = {"since": since, "until": until}
            params = {"username": self.username.value}
            headers = {"Authorization": config.SHARED_SECRET}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, params=params, headers=headers
                ) as response:
                    response_data = await response.json()

            await interaction.followup.send(response_data["message"], ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)


class SheetUpdateModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Update Sheet")
        self.spreadsheet_id = discord.ui.TextInput(
            label="Spreadsheet ID", placeholder="Enter the spreadsheet ID to update"
        )

        # Add the TextInput component to the modal
        self.add_item(self.spreadsheet_id)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            updated_spreadsheet_id = (
                update_created_spreadsheet_with_users_except_ai_decisions(
                    self.spreadsheet_id.value
                )
            )

            await interaction.followup.send(
                f"Spreadsheet updated successfully!\n"
                f"View it here: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id.value}",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(
                f"Error updating spreadsheet: {str(e)}", ephemeral=True
            )


class AutopostStartModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Start Auto-post")
        self.date = discord.ui.TextInput(
            label="Date (YYYY-MM)", placeholder="e.g., 2024-03"
        )
        self.time = discord.ui.TextInput(
            label="Time (HH:MM)", placeholder="e.g., 09:00"
        )
        self.spreadsheet_id = discord.ui.TextInput(
            label="Spreadsheet ID (Optional)",
            required=False,
            placeholder="Enter spreadsheet ID",
        )
        self.channel_id = discord.ui.TextInput(
            label="Channel/Thread ID (Optional)",
            required=False,
            placeholder="Enter channel/thread ID",
        )

        # Add the TextInput components to the modal
        self.add_item(self.date)
        self.add_item(self.time)
        self.add_item(self.spreadsheet_id)
        self.add_item(self.channel_id)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            year, month = self.date.value.split("-")
            hour, minute = map(int, self.time.value.split(":"))
            spreadsheet_id = (
                self.spreadsheet_id.value if self.spreadsheet_id.value else None
            )
            channel_id = (
                self.channel_id.value.strip() if self.channel_id.value else None
            )

            target_channel = interaction.channel
            if channel_id:
                try:
                    target_channel = await interaction.guild.fetch_channel(
                        int(channel_id)
                    )
                    if not target_channel:
                        raise ValueError("Channel not found")
                except (ValueError, discord.NotFound, discord.Forbidden):
                    await interaction.followup.send(
                        "Invalid channel ID or cannot access the specified channel. Using current channel instead.",
                        ephemeral=True,
                    )
                    target_channel = interaction.channel

            task_id = f"{year}-{month}"

            # Check if there's already a task running for this month
            if task_id in auto_post_tasks and auto_post_tasks[task_id].is_running():
                old_channel = task_details[task_id]["channel"]
                await interaction.followup.send(
                    f"There's already an auto-post task running for {task_id} in channel {old_channel.name}. "
                    f"Please stop it first before starting a new one.",
                    ephemeral=True,
                )
                return

            task_details[task_id] = {
                "year": year,
                "month": month,
                "spreadsheet_id": spreadsheet_id,
                "hour": hour,
                "minute": minute,
                "channel": target_channel,
            }

            if not spreadsheet_id:
                await interaction.followup.send(
                    f"Spreadsheet ID is missing; it will not update the spreadsheet!",
                    ephemeral=True,
                )

            auto_post_tasks[task_id] = tasks.loop(minutes=1)(
                auto_post_leaderboard(task_id)
            )
            auto_post_tasks[task_id].start()

            await interaction.followup.send(
                f"Auto-post leaderboard task started for {self.date.value} at {hour:02d}:{minute:02d} "
                f"in channel #{target_channel.name}",
                ephemeral=True,
            )
        except ValueError as ve:
            await interaction.followup.send(
                f"Invalid input: {str(ve)}. Please check your date and time format.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error in AutopostStartModal: {e}")
            await interaction.followup.send(
                f"An error occurred: {str(e)}", ephemeral=True
            )


class AutopostStopModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Stop Auto-post")
        self.date = discord.ui.TextInput(
            label="Date (YYYY-MM)", placeholder="e.g., 2024-03"
        )
        self.channel_id = discord.ui.TextInput(
            label="Channel/Thread ID (Optional)",
            required=False,
            placeholder="Enter channel/thread ID",
        )

        # Add the TextInput components to the modal
        self.add_item(self.date)
        self.add_item(self.channel_id)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            task_id = self.date.value
            channel_id = (
                self.channel_id.value.strip() if self.channel_id.value else None
            )

            if (
                task_id not in auto_post_tasks
                or not auto_post_tasks[task_id].is_running()
            ):
                await interaction.followup.send(
                    f"No auto-post task running for {task_id}", ephemeral=True
                )
                return

            if channel_id:
                try:
                    target_channel = await interaction.guild.fetch_channel(
                        int(channel_id)
                    )
                    if not target_channel:
                        raise ValueError("Channel not found")

                    if task_details[task_id]["channel"].id != target_channel.id:
                        await interaction.followup.send(
                            f"The auto-post task for {task_id} is running in #{task_details[task_id]['channel'].name}, "
                            f"not in the specified channel #{target_channel.name}",
                            ephemeral=True,
                        )
                        return
                except (ValueError, discord.NotFound, discord.Forbidden):
                    await interaction.followup.send(
                        "Invalid channel ID or cannot access the specified channel.",
                        ephemeral=True,
                    )
                    return

            auto_post_tasks[task_id].cancel()
            channel_name = task_details[task_id]["channel"].name
            await interaction.followup.send(
                f"Auto-post leaderboard task stopped for {task_id} in channel #{channel_name}",
                ephemeral=True,
            )

        except ValueError as ve:
            await interaction.followup.send(
                f"Invalid input: {str(ve)}. Please check your date format.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error in AutopostStopModal: {e}")
            await interaction.followup.send(
                f"An error occurred: {str(e)}", ephemeral=True
            )


class LeaderboardClosureModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Leaderboard Closure")
        self.date = discord.ui.TextInput(
            label="Date (YYYY-MM)", placeholder="e.g., 2024-03", required=False
        )
        self.commit_filter = discord.ui.TextInput(
            label="Commit Filter",
            placeholder="Minimum number of commits (default: 10)",
            required=False,
            default="10",
        )

        # Add the TextInput components to the modal
        self.add_item(self.date)
        self.add_item(self.commit_filter)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            forum_channel_id = int(config.LEADERBOARD_FORUM_CHANNEL_ID)
            forum_channel = interaction.guild.get_channel(forum_channel_id)

            if self.date.value:
                year, month = self.date.value.split("-")
                date_obj = datetime.strptime(f"{year}-{month}", "%Y-%m")
            else:
                now = datetime.now()
                date_obj = now
                formatted_date = now.strftime("%Y-%m")
                year, month = formatted_date.split("-")

            commit_filter = (
                int(self.commit_filter.value) if self.commit_filter.value else 10
            )

            leaderboard = create_leaderboard_by_month(year, month, commit_filter)
            messages = format_leaderboard_for_discord(
                leaderboard, self.date.value, True
            )
            month_name = date_obj.strftime("%B")

            thread_title = f"Leaderboard | {year} {month_name}"
            thread, _ = await forum_channel.create_thread(
                name=thread_title, content=messages[0]
            )

            if len(messages) > 0:
                for msg in messages[1:]:
                    await thread.send(msg)

            file_path = "user_data.csv"
            result = write_users_to_csv_monthly(file_path, self.date.value)

            if "Successfully" in result:
                await thread.send(file=discord.File(file_path))
                os.remove(file_path)

            await interaction.followup.send(
                f"Leaderboard thread created: {thread.jump_url}", ephemeral=True
            )

        except Exception as e:
            logger.error(f"Error in LeaderboardClosureModal: {e}")
            await interaction.followup.send(
                f"An error occurred: {str(e)}", ephemeral=True
            )


class MonthlyStreaksModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Monthly Streaks")
        self.date = discord.ui.TextInput(
            label="Date (YYYY-MM)", placeholder="e.g., 2024-03", required=False
        )

        # Add the TextInput component to the modal
        self.add_item(self.date)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            forum_channel_id = int(config.LEADERBOARD_FORUM_CHANNEL_ID)
            forum_channel = interaction.guild.get_channel(forum_channel_id)

            if self.date.value:
                year, month = self.date.value.split("-")
                date_obj = datetime.strptime(f"{year}-{month}", "%Y-%m")
                date = self.date.value
            else:
                now = datetime.now()
                date_obj = now
                formatted_date = now.strftime("%Y-%m")
                year, month = formatted_date.split("-")
                date = formatted_date

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
            logger.error(f"Error in MonthlyStreaksModal: {e}")
            await interaction.followup.send(
                f"An error occurred: {str(e)}", ephemeral=True
            )
