import discord
import os
import sys
import json

from datetime import datetime

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
                        f"Cannot found user named {discord_handle}"
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
