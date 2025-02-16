import discord
from discord.ui import View, Button
from typing import Optional
from datetime import datetime
import os
import aiohttp
import config

from leader_bot.modals import (
    LeaderboardCreateModal,
    LeaderboardViewModal,
    SheetCreationModal,
    SheetUpdateModal,
    UserModal,
    UserMonthlyDataModal,
    AIDecisionsModal,
    UserDeletionModal,
    TaskRunModal,
    UserTaskRunModal,
    SchedulerStartModal,
    AutopostStartModal,
    AutopostStopModal,
)
from leader_bot.sheet_functions import write_users_to_csv


class MainView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # Organize main menu buttons into two rows
        self.leaderboard_management.row = 0
        self.user_management.row = 0
        self.api_management.row = 1
        self.sheet_management.row = 1

    def create_main_menu_embed(self):
        embed = discord.Embed(
            title="Leaderboard Admin Control Panel",
            description="Select a category to manage:",
            color=discord.Color.blue(),
            timestamp=datetime.now(),
        )
        embed.add_field(
            name="🏆 Leaderboard Management",
            value="Manage leaderboards and rankings",
            inline=True,
        )
        embed.add_field(
            name="👥 User Management", value="Manage user data", inline=True
        )
        embed.add_field(
            name="🔧 API Management",
            value="Control API tasks and settings",
            inline=True,
        )
        embed.add_field(
            name="📊 Sheet Management",
            value="Create, update and manage sheets",
            inline=True,
        )
        embed.set_footer(text="Use the buttons below to navigate")
        return embed

    @discord.ui.button(
        label="🏆 Leaderboard Management", style=discord.ButtonStyle.primary
    )
    async def leaderboard_management(
        self, interaction: discord.Interaction, button: Button
    ):
        embed = discord.Embed(
            title="Leaderboard Management",
            description="Select an operation:",
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(
            embed=embed, view=LeaderboardManagementView(), ephemeral=True
        )

    @discord.ui.button(label="👥 User Management", style=discord.ButtonStyle.primary)
    async def user_management(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="User Management",
            description="Select an operation:",
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(
            embed=embed, view=UserManagementView(), ephemeral=True
        )

    @discord.ui.button(label="🔧 API Management", style=discord.ButtonStyle.primary)
    async def api_management(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="API Management",
            description="Select an operation:",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(
            embed=embed, view=APIManagementView(), ephemeral=True
        )

    @discord.ui.button(label="📊 Sheet Management", style=discord.ButtonStyle.primary)
    async def sheet_management(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="Sheet Management",
            description="Select an operation:",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Create Sheet", value="Create a new spreadsheet", inline=True
        )
        embed.add_field(
            name="Update Sheet", value="Update existing spreadsheet", inline=True
        )
        embed.add_field(name="Edit Sheet", value="Modify sheet contents", inline=True)

        await interaction.response.send_message(
            embed=embed, view=SheetManagementView(), ephemeral=True
        )


class SheetManagementView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # Add buttons to specific rows
        self.create_sheet.row = 0
        self.update_sheet.row = 0
        self.edit_sheet.row = 0
        self.back_to_main.row = 1  # Put back button on new row

    @discord.ui.button(label="Create Sheet", style=discord.ButtonStyle.primary)
    async def create_sheet(self, interaction: discord.Interaction, button: Button):
        modal = SheetCreationModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Update Sheet", style=discord.ButtonStyle.primary)
    async def update_sheet(self, interaction: discord.Interaction, button: Button):
        modal = SheetUpdateModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Edit Sheet", style=discord.ButtonStyle.primary)
    async def edit_sheet(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="Edit Sheet",
            description="Choose edit operation:",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(
            embed=embed, view=SheetEditView(), ephemeral=True
        )

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_to_main(self, interaction: discord.Interaction, button: Button):
        main_view = MainView()
        await interaction.response.edit_message(
            embed=main_view.create_main_menu_embed(), view=main_view
        )


class SheetEditView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # Organize buttons into rows
        self.insert_user.row = 0
        self.update_user.row = 0
        self.add_repo.row = 1
        self.delete_user.row = 1
        self.back_to_sheet_management.row = 2

    @discord.ui.button(label="Insert User", style=discord.ButtonStyle.primary)
    async def insert_user(self, interaction: discord.Interaction, button: Button):
        modal = UserModal(operation="insert")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Update User", style=discord.ButtonStyle.primary)
    async def update_user(self, interaction: discord.Interaction, button: Button):
        modal = UserModal(operation="update")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Add Repository", style=discord.ButtonStyle.primary)
    async def add_repo(self, interaction: discord.Interaction, button: Button):
        modal = UserModal(operation="add_repo")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Delete User", style=discord.ButtonStyle.danger)
    async def delete_user(self, interaction: discord.Interaction, button: Button):
        modal = UserModal(operation="delete")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_to_sheet_management(
        self, interaction: discord.Interaction, button: Button
    ):
        embed = discord.Embed(
            title="Sheet Management",
            description="Select an operation:",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Create Sheet", value="Create a new spreadsheet", inline=True
        )
        embed.add_field(
            name="Update Sheet", value="Update existing spreadsheet", inline=True
        )
        embed.add_field(name="Edit Sheet", value="Modify sheet contents", inline=True)

        await interaction.response.edit_message(embed=embed, view=SheetManagementView())


class LeaderboardManagementView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # Organize buttons into rows
        self.create_update.row = 0
        self.view_leaderboard.row = 0
        self.autopost_controls.row = 0
        self.back_to_main.row = 1

    @discord.ui.button(label="Create", style=discord.ButtonStyle.primary)
    async def create_update(self, interaction: discord.Interaction, button: Button):
        modal = LeaderboardCreateModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="View Leaderboard", style=discord.ButtonStyle.primary)
    async def view_leaderboard(self, interaction: discord.Interaction, button: Button):
        modal = LeaderboardViewModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Auto-post Controls", style=discord.ButtonStyle.primary)
    async def autopost_controls(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="Auto-post Controls",
            description="Manage automatic posting:",
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(
            embed=embed, view=AutopostControlView(), ephemeral=True
        )

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_to_main(self, interaction: discord.Interaction, button: Button):
        main_view = MainView()
        await interaction.response.edit_message(
            embed=main_view.create_main_menu_embed(), view=main_view
        )


class UserManagementView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # Organize buttons into rows
        self.get_monthly_data.row = 0
        self.get_all_data.row = 0
        self.get_ai_decisions.row = 1
        self.delete_data.row = 1
        self.back_to_main.row = 2

    @discord.ui.button(label="Get Monthly Data", style=discord.ButtonStyle.primary)
    async def get_monthly_data(self, interaction: discord.Interaction, button: Button):
        modal = UserMonthlyDataModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Get All Data", style=discord.ButtonStyle.primary)
    async def get_all_data(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="Export Data",
            description="Exporting all user data to CSV...",
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        file_path = "all_data.csv"
        result = write_users_to_csv(file_path)
        if "successfully" in result:
            await interaction.channel.send(file=discord.File(file_path))
            os.remove(file_path)

    @discord.ui.button(label="Get AI Decisions", style=discord.ButtonStyle.primary)
    async def get_ai_decisions(self, interaction: discord.Interaction, button: Button):
        modal = AIDecisionsModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Delete Data", style=discord.ButtonStyle.danger)
    async def delete_data(self, interaction: discord.Interaction, button: Button):
        modal = UserDeletionModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_to_main(self, interaction: discord.Interaction, button: Button):
        main_view = MainView()
        await interaction.response.edit_message(
            embed=main_view.create_main_menu_embed(), view=main_view
        )


class APIManagementView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # Organize buttons into rows
        self.run_task.row = 0
        self.run_user_task.row = 0
        self.scheduler_controls.row = 0
        self.back_to_main.row = 1

    @discord.ui.button(label="Run Task", style=discord.ButtonStyle.primary)
    async def run_task(self, interaction: discord.Interaction, button: Button):
        modal = TaskRunModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Run Task for User", style=discord.ButtonStyle.primary)
    async def run_user_task(self, interaction: discord.Interaction, button: Button):
        modal = UserTaskRunModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Scheduler Controls", style=discord.ButtonStyle.primary)
    async def scheduler_controls(
        self, interaction: discord.Interaction, button: Button
    ):
        embed = discord.Embed(
            title="Scheduler Controls",
            description="Manage scheduler:",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(
            embed=embed, view=SchedulerControlView(), ephemeral=True
        )

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_to_main(self, interaction: discord.Interaction, button: Button):
        main_view = MainView()
        await interaction.response.edit_message(
            embed=main_view.create_main_menu_embed(), view=main_view
        )


class SchedulerControlView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # Organize buttons into rows
        self.start_scheduler.row = 0
        self.stop_scheduler.row = 0
        self.back_to_api.row = 1

    @discord.ui.button(label="Start Scheduler", style=discord.ButtonStyle.success)
    async def start_scheduler(self, interaction: discord.Interaction, button: Button):
        modal = SchedulerStartModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Stop Scheduler", style=discord.ButtonStyle.danger)
    async def stop_scheduler(self, interaction: discord.Interaction, button: Button):
        await self.control_scheduler(interaction, "stop")

    async def control_scheduler(
        self, interaction: discord.Interaction, action: str, interval: int = 1
    ):
        try:
            url = f"{config.GTP_ENDPOINT}/control-scheduler"
            payload = {"action": action, "interval_minutes": interval}
            headers = {"Authorization": config.SHARED_SECRET}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    response_data = await response.json()

            await interaction.response.send_message(
                response_data["message"], ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_to_api(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="API Management",
            description="Select an operation:",
            color=discord.Color.red(),
        )
        await interaction.response.edit_message(embed=embed, view=APIManagementView())


class AutopostControlView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # Organize buttons into rows
        self.start_autopost.row = 0
        self.stop_autopost.row = 0
        self.back_to_leaderboard.row = 1

    @discord.ui.button(label="Start Auto-post", style=discord.ButtonStyle.success)
    async def start_autopost(self, interaction: discord.Interaction, button: Button):
        modal = AutopostStartModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Stop Auto-post", style=discord.ButtonStyle.danger)
    async def stop_autopost(self, interaction: discord.Interaction, button: Button):
        modal = AutopostStopModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def back_to_leaderboard(
        self, interaction: discord.Interaction, button: Button
    ):
        embed = discord.Embed(
            title="Leaderboard Management",
            description="Select an operation:",
            color=discord.Color.gold(),
        )
        await interaction.response.edit_message(
            embed=embed, view=LeaderboardManagementView()
        )
