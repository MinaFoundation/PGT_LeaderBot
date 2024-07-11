import unittest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from github_tracker_bot.read_sheet import read_sheet


class TestReadSheet(unittest.TestCase):

    @patch("googleapiclient.discovery.build")
    def test_read_sheet(self, mock_build):
        mock_service = MagicMock()
        mock_sheet = mock_service.spreadsheets.return_value
        mock_values = mock_sheet.values.return_value
        mock_get = mock_values.get.return_value

        mock_get.execute.return_value = {
            "values": [
                ["USER HANDLE", "GITHUB NAME", "REPOSITORIES"],
                [
                    "berkingurcan",
                    "berkingurcan",
                    "https://github.com/UmstadAI/zkAppUmstad, https://github.com/UmstadAI/discord-umstad, https://github.com/zkcloudworker/zkcloudworker-lib",
                ],
                [
                    "dfst",
                    "dfstio",
                    "https://github.com/dfstio/minanft-rollup, https://github.com/zkcloudworker/zkcloudworker-lib, https://github.com/zkcloudworker/zkcloudworker-aws, ",
                ],
                [
                    "mario_zito",
                    "mazito",
                    "https://github.com/zkcloudworker/zkcloudworker-aws, https://github.com/Identicon-Dao/socialcap",
                ],
            ]
        }

        mock_build.return_value = mock_service

        with patch("builtins.print") as mock_print:  # Mocking print to capture output
            read_sheet()

            mock_build.assert_called_once_with(
                "sheets", "v4", credentials=unittest.mock.ANY
            )
            mock_service.spreadsheets.assert_called_once()
            mock_values.get.assert_called_once_with(
                spreadsheetId=unittest.mock.ANY, range="A1:D99999"
            )
            mock_get.execute.assert_called_once()

            expected_calls = [
                unittest.mock.call(["USER HANDLE", "GITHUB NAME", "REPOSITORIES"]),
                unittest.mock.call(
                    [
                        "berkingurcan",
                        "berkingurcan",
                        "https://github.com/UmstadAI/zkAppUmstad, https://github.com/UmstadAI/discord-umstad, https://github.com/zkcloudworker/zkcloudworker-lib",
                    ]
                ),
                unittest.mock.call(
                    [
                        "dfst",
                        "dfstio",
                        "https://github.com/dfstio/minanft-rollup, https://github.com/zkcloudworker/zkcloudworker-lib, https://github.com/zkcloudworker/zkcloudworker-aws, ",
                    ]
                ),
                unittest.mock.call(
                    [
                        "mario_zito",
                        "mazito",
                        "https://github.com/zkcloudworker/zkcloudworker-aws, https://github.com/Identicon-Dao/socialcap",
                    ]
                ),
            ]
            mock_print.assert_has_calls(expected_calls, any_order=False)


if __name__ == "__main__":
    unittest.main()
