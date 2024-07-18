import unittest
from unittest.mock import patch, Mock
from github_tracker_bot.read_sheet import read_sheet, get_google_sheets_service
import config


class TestReadSheet(unittest.TestCase):

    @patch("github_tracker_bot.read_sheet.build")
    @patch("github_tracker_bot.read_sheet.Credentials")
    def test_get_google_sheets_service_success(self, mock_credentials, mock_build):
        mock_creds = Mock()
        mock_credentials.from_service_account_file.return_value = mock_creds
        mock_service = Mock()
        mock_build.return_value = mock_service

        service = get_google_sheets_service()

        mock_credentials.from_service_account_file.assert_called_once_with(
            config.GOOGLE_CREDENTIALS,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        mock_build.assert_called_once_with("sheets", "v4", credentials=mock_creds)
        self.assertEqual(service, mock_service)

    @patch("github_tracker_bot.read_sheet.get_google_sheets_service")
    def test_read_sheet_success(self, mock_get_service):
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["Name", "Age", "REPOSITORIES"],
                ["Alice", "30", "repo1, repo2"],
                ["Bob", "25", "repo3"],
            ]
        }

        expected_data = [
            {"Name": "Alice", "Age": "30", "REPOSITORIES": ["repo1", "repo2"]},
            {"Name": "Bob", "Age": "25", "REPOSITORIES": ["repo3"]},
        ]

        data = read_sheet(config.SPREADSHEET_ID)
        self.assertEqual(data, expected_data)

    @patch("github_tracker_bot.read_sheet.get_google_sheets_service")
    def test_read_sheet_no_data(self, mock_get_service):
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {}

        data = read_sheet(config.SPREADSHEET_ID)
        self.assertEqual(data, [])

    @patch("github_tracker_bot.read_sheet.get_google_sheets_service")
    def test_read_sheet_error(self, mock_get_service):
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.side_effect = Exception(
            "API error"
        )

        data = read_sheet(config.SPREADSHEET_ID)
        self.assertEqual(data, [])

    @patch("github_tracker_bot.read_sheet.get_google_sheets_service")
    def test_read_sheet_incomplete_rows(self, mock_get_service):
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["Name", "Age", "REPOSITORIES"],
                ["Alice", "30"],
                ["Bob", "25", "repo3"],
            ]
        }

        expected_data = [
            {"Name": "Alice", "Age": "30", "REPOSITORIES": []},
            {"Name": "Bob", "Age": "25", "REPOSITORIES": ["repo3"]},
        ]

        data = read_sheet(config.SPREADSHEET_ID)
        self.assertEqual(data, expected_data)

    @patch("github_tracker_bot.read_sheet.get_google_sheets_service")
    def test_read_sheet_extra_columns(self, mock_get_service):
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["Name", "Age", "REPOSITORIES"],
                ["Alice", "30", "repo1, repo2", "extra"],
                ["Bob", "25", "repo3", "extra"],
            ]
        }

        expected_data = [
            {"Name": "Alice", "Age": "30", "REPOSITORIES": ["repo1", "repo2"]},
            {"Name": "Bob", "Age": "25", "REPOSITORIES": ["repo3"]},
        ]

        data = read_sheet(config.SPREADSHEET_ID)
        self.assertEqual(data, expected_data)

    @patch("github_tracker_bot.read_sheet.get_google_sheets_service")
    def test_read_sheet_extra_header_columns(self, mock_get_service):
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["Name", "Age", "REPOSITORIES", "Extra"],
                ["Alice", "30", "repo1, repo2", "extra1"],
                ["Bob", "25", "repo3", "extra2"],
            ]
        }

        expected_data = [
            {
                "Name": "Alice",
                "Age": "30",
                "REPOSITORIES": ["repo1", "repo2"],
                "Extra": "extra1",
            },
            {"Name": "Bob", "Age": "25", "REPOSITORIES": ["repo3"], "Extra": "extra2"},
        ]

        data = read_sheet(config.SPREADSHEET_ID)
        self.assertEqual(data, expected_data)

    @patch("github_tracker_bot.read_sheet.get_google_sheets_service")
    def test_read_sheet_empty_cells(self, mock_get_service):
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["Name", "Age", "REPOSITORIES"],
                ["Alice", "", "repo1, repo2"],
                ["", "25", "repo3"],
            ]
        }

        expected_data = [
            {"Name": "Alice", "Age": "", "REPOSITORIES": ["repo1", "repo2"]},
            {"Name": "", "Age": "25", "REPOSITORIES": ["repo3"]},
        ]

        data = read_sheet(config.SPREADSHEET_ID)
        self.assertEqual(data, expected_data)


if __name__ == "__main__":
    unittest.main()
