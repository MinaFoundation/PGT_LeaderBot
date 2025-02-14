"""
This module contains shared state variables used across different modules in the leader_bot package.
"""
from datetime import datetime
from log_config import get_logger
from leader_bot.leaderboard_functions import create_leaderboard_by_month, format_leaderboard_for_discord
from leader_bot.sheet_functions import create_leaderboard_sheet

logger = get_logger(__name__)

# Dictionary to store auto-post task details
task_details = {}

# Dictionary to store auto-post tasks
auto_post_tasks = {}

def auto_post_leaderboard(task_id):
    async def inner():
        try:
            now = datetime.now()
            details = task_details[task_id]
            if now.hour == details["hour"] and now.minute == details["minute"]:
                leaderboard = create_leaderboard_by_month(
                    details["year"], details["month"]
                )
                if details.get("spreadsheet_id"):
                    create_leaderboard_sheet(
                        details["spreadsheet_id"],
                        leaderboard,
                        details["year"],
                        details["month"],
                    )
                messages = format_leaderboard_for_discord(leaderboard)
                channel = details["channel"]
                
                # Get the bot user from the channel's guild
                bot_user = channel.guild.me
                async for message in channel.history(limit=None):
                    if message.author.id == bot_user.id:
                        await message.delete()
                for msg in messages:
                    await channel.send(msg)
        except Exception as e:
            logger.error(f"Error in auto_post_leaderboard task {task_id}: {e}")

    return inner 