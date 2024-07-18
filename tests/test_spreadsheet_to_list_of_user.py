import sys
import os

from typing import List
import unittest
from unittest.mock import patch, Mock

import config
from github_tracker_bot.redis_data_handler import User
import github_tracker_bot.helpers.spreadsheet_handlers as handlers


class TestSpreadsheetToList(unittest.TestCase):
    def setUp(self):
        self.data_version_1 = [
            {
                "USER HANDLE": "berkingurcan",
                "GITHUB NAME": "berkingurcan",
                "REPOSITORIES": [
                    "https://github.com/UmstadAI/zkAppUmstad",
                    "https://github.com/UmstadAI/discord-umstad",
                    "https://github.com/zkcloudworker/zkcloudworker-lib",
                ],
            },
            {
                "USER HANDLE": "dfst",
                "GITHUB NAME": "dfstio",
                "REPOSITORIES": [
                    "https://github.com/dfstio/minanft-rollup",
                    "https://github.com/zkcloudworker/zkcloudworker-lib",
                    "https://github.com/zkcloudworker/zkcloudworker-aws",
                ],
            },
            {
                "USER HANDLE": "mario_zito",
                "GITHUB NAME": "mazito",
                "REPOSITORIES": [
                    "https://github.com/zkcloudworker/zkcloudworker-aws",
                    "https://github.com/Identicon-Dao/socialcap",
                ],
            },
            {"USER HANDLE": "deneme", "GITHUB NAME": "denene", "REPOSITORIES": []},
        ]

        self.data_version_2 = [
            {
                "user": "berkingurcan",
                "github": "berkingurcan",
                "REPOSITORIES": [
                    "https://github.com/UmstadAI/zkAppUmstad",
                    "https://github.com/UmstadAI/discord-umstad",
                    "https://github.com/zkcloudworker/zkcloudworker-lib",
                ],
            },
            {
                "user": "dfst",
                "github": "dfstio",
                "REPOSITORIES": [
                    "https://github.com/dfstio/minanft-rollup",
                    "https://github.com/zkcloudworker/zkcloudworker-lib",
                    "https://github.com/zkcloudworker/zkcloudworker-aws",
                ],
            },
            {
                "user": "mario_zito",
                "github": "mazito",
                "REPOSITORIES": [
                    "https://github.com/zkcloudworker/zkcloudworker-aws",
                    "https://github.com/Identicon-Dao/socialcap",
                ],
            },
            {"user": "deneme", "github": "denene", "REPOSITORIES": []},
        ]

    async def test_spreadsheet_to_user_version1(self):
        list_of_users = await handlers.spreadsheet_to_list_of_user(self.data_version_1)

        self.assertIsNotNone(list_of_users)
        self.assertIsInstance(list_of_users, List[User])

    async def test_spreadsheet_to_user_version2(self):
        list_of_users = await handlers.spreadsheet_to_list_of_user(self.data_version_2)

        self.assertIsNotNone(list_of_users)
        self.assertIsInstance(list_of_users, List[User])

if __name__ == "__main__":
    unittest.main()
