# LeaderBot
Tool that will track and rank contributions across the different Mina developer programs. Consists of two bot:

1. **[Github Tracker Bot](#github-tracker-bot)**
2. **[Leaderbot](#leaderbot-1)**

## Getting Started

### Prerequisites
- Python 3.10
- MongoDB
- Google Cloud Service Account with access to Google Sheets API
- Docker

### Installation & Setup
1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/PGT_LeaderBot.git
   cd PGT_LeaderBot
   ```


2. In the root folder install virtual env and create virtual env:
    ```sh
    pip install virtualenv
    virtualenv venv
    ```

    Activate it:
    ```sh
    source venv/bin/activate
    ```

3. Install dependencies with:
    ```sh
    pip install -r requirements.txt
    ```

4. Configure the environment variables
    
    Create .env file in the root folder and add environment variables as shown in the .env.example file:

    ```
    GITHUB_TOKEN='your_github_token'
    DISCORD_TOKEN='your_discord_token'
    GOOGLE_SHEETS_CREDENTIALS='path_to_your_google_sheets_credentials.json'
    OPENAI_API_KEY='your_openai_api_key'

    MONGO_HOST='mongodb://localhost:27017/'
    MONGO_DB="example_db"
    MONGO_COLLECTION="example_collection"

    SPREADSHEET_ID='spread_sheet_id'
    LOG_LEVEL=DEBUG

    GUILD_ID=XXXXXXXX
    GMAIL_ADDRESS=xyz@gmail.com
    LEADERBOARD_FORUM_CHANNEL_ID=XXXXXXXXXXXXXXXXX
    ```

6. You need to have google credentials .json file which has access your spreadsheet in the root folder. Need to enable Google Sheets API and Google Drive API. [Click for more information.](https://developers.google.com/workspace/guides/create-credentials)

7. Run tests:
    ```sh
    invoke test
    ```

8. Run [github tracker bot](#github-tracker-bot):
    ```sh
    invoke bot
    ```

    For other invoke tasks look to: [tasks.py](./tasks.py)

9. To run [Leaderbot](#leaderbot-1) discord bot, you need to have Discord bot in a specific server.

    ```sh
    invoke leaderbot
    ```

-------------------------
## Github Tracker Bot

### Overview

Github Tracker Bot fetchs to Google Spreadsheets which includes discord handle, github username and repositories. After getting these informations it fetches github commits data between specific timeframes given by user or day by day for all branches. After pre-processing the commits data. The bot sends total daily commits data(diff file) to OPENAI API to decide are these commits qualified with [prompt.](./github_tracker_bot/prompts.py)

Then gets the decisions data and insert them to MongoDB to further usage.


Date formats are ISO 8601 with Z suffix which is UTC. For example:
```"2023-01-24T00:00:00Z"```

### API Usage 
`bot.py` is the main script for running a FastAPI service that provides functionality to schedule and run tasks to fetch results from a spreadsheet within specified time frames. The script includes endpoints to start and stop a scheduler, as well as to run tasks on demand.

### API Endpoints

#### 1. Run task manually for specific timeframes:
**Endpoint:** `/run-task`  
**Method:** `POST`

This endpoint allows you to run a task immediately and manually for a specified time frame.

##### Request Body:

- `since` (str): Start datetime in ISO 8601 format (e.g., `2023-07-24T00:00:00Z`).
- `until` (str): End datetime in ISO 8601 format (e.g., `2023-07-25T00:00:00Z`).

##### Example Request:

```json
{
  "since": "2023-07-24T00:00:00Z",
  "until": "2023-07-25T00:00:00Z"
}
```

##### Example Response:
```json
{
  "message": "Task run successfully with provided times"
}
```

#### 2. Run task for specific user:
**Endpoint:** `/run-task-for-user?username=johndoe`  
**Method:** `POST`

This endpoint allows you to run a task immediately and manually for a specified time frame and specific user.

##### Request Body:

- `since` (str): Start datetime in ISO 8601 format (e.g., `2023-07-24T00:00:00Z`).
- `until` (str): End datetime in ISO 8601 format (e.g., `2023-07-25T00:00:00Z`).

##### Example Request:
Endpoint: `/run-task-for-user?username=berkingurcan`

```json
{
    "since": "2023-07-24T00:00:00Z",
    "until": "2023-07-25T00:00:00Z"
}
```

##### Example Response:
```json
{
  "message": "Task run successfully with provided times"
}
```

#### 3. Control Scheduler

**Endpoint:** `/control-scheduler`  
**Method:** `POST`

This endpoint allows you to start or stop the scheduler that runs tasks at specified minutes intervals. It is minutes for now to test. It will be hours.

##### Request Body:
- `action`(str): Action to perform (`start` or `stop`).
- `interval_minutes` (int, optional): Interval in minutes(for now) at which the scheduler should run the task (only required when action is `start`).

##### Example Requests:
###### Start Scheduler:
```json
{
  "action": "start",
  "interval_minutes": 5
}
```

###### Stop Scheduler:
```json
{
  "action": "stop"
}
```

##### Example Responses:
###### Start Scheduler:
```json
{
  "message": "Scheduler started with interval of 5 minutes"
}
```

###### Stop Scheduler:
```json
{
  "message": "Scheduler stopped"
}
```


### Classes

#### User
The [`User`](./github_tracker_bot/mongo_data_handler.py) class is a nested dataclass designed to store and manage information about a user, including their GitHub-related activities and AI decisions regarding their contributions. This class stores 4 necessary data:
- **user_handle**: `str`
- **github_name**: `str`
- **repositories**: `List[str]`
- **ai_decisions**: `List[List[AIDecision]]`

Remaining fields can be calculated using helper functions in the [helper_functions.py](./github_tracker_bot/helpers/helper_functions.py).

#### AIDecision

The `AIDecision` Class stores AI decision related to a user's daily contribution for specific github repository. It includes details about the repository, date, and a nested response indicating the qualification status of the contribution which is `DailyContributionResponse` Class.

- **username**: `str`
- **repository**: `str`
- **date**: `str`
- **response**: `DailyContributionResponse`

#### DailyContributionResponse

The `DailyContributionResponse` class is another dataclass to store information about a user's daily contribution response returned by OPENAI API for specific repository. It includes details about the contribution's qualification status and an AI explanation for it. 

- **username**: str
- **date**: str
- **is_qualified**: bool
- **explanation**: str

<details>
<summary>Click to see full code of <b>User, AIDecision and DailyContributionResponse</b> Classes 
</summary>

```py
@dataclass
class DailyContributionResponse:
    username: str
    date: str
    is_qualified: bool
    explanation: str

    def to_dict(self):
        """Converts the dataclass to a dictionary."""
        return asdict(self)

@dataclass
class AIDecision:
    username: str
    repository: str
    date: str
    response: DailyContributionResponse

    def to_dict(self):
        """Converts the dataclass to a dictionary, including nested response."""
        data = asdict(self)
        data["response"] = self.response.to_dict()
        return data


@dataclass
class User:
    user_handle: str
    github_name: str
    repositories: List[str]
    ai_decisions: List[List[AIDecision]] = field(default_factory=list)
    total_daily_contribution_number: int = 0
    total_qualified_daily_contribution_number: int = 0
    qualified_daily_contribution_number_by_month: Dict[str, int] = field(
        default_factory=dict
    )
    qualified_daily_contribution_dates: set = field(default_factory=set)
    qualified_daily_contribution_streak: int = 0

    def validate(self) -> bool:
        """Validates the User instance."""
        if not isinstance(self.repositories, list) or not all(
            isinstance(repo, str) for repo in self.repositories
        ):
            logger.error("Invalid repository list")
            return False
        return True

    def to_dict(self):
        """Converts the dataclass to a dictionary."""
        return {
            "user_handle": self.user_handle,
            "github_name": self.github_name,
            "repositories": self.repositories,
            "ai_decisions": [
                [decision.to_dict() for decision in decisions]
                for decisions in self.ai_decisions
            ],
            "total_daily_contribution_number": self.total_daily_contribution_number,
            "total_qualified_daily_contribution_number": self.total_qualified_daily_contribution_number,
            "qualified_daily_contribution_number_by_month": self.qualified_daily_contribution_number_by_month,
            "qualified_daily_contribution_dates": list(
                self.qualified_daily_contribution_dates
            ),
            "qualified_daily_contribution_streak": self.qualified_daily_contribution_streak,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "User":
        """Creates a User instance from a dictionary."""
        ai_decisions = [
            [
                AIDecision(
                    username=decision["username"],
                    repository=decision["repository"],
                    date=decision["date"],
                    response=DailyContributionResponse(
                        username=decision["response"]["username"],
                        date=decision["response"]["date"],
                        is_qualified=decision["response"]["is_qualified"],
                        explanation=decision["response"]["explanation"],
                    ),
                )
                for decision in decisions
            ]
            for decisions in data.get("ai_decisions", [])
        ]
        return User(
            user_handle=data["user_handle"],
            github_name=data["github_name"],
            repositories=data.get("repositories", []),
            ai_decisions=ai_decisions,
            total_daily_contribution_number=data.get(
                "total_daily_contribution_number", 0
            ),
            total_qualified_daily_contribution_number=data.get(
                "total_qualified_daily_contribution_number", 0
            ),
            qualified_daily_contribution_number_by_month=data.get(
                "qualified_daily_contribution_number_by_month", {}
            ),
            qualified_daily_contribution_dates=set(
                data.get("qualified_daily_contribution_dates", [])
            ),
            qualified_daily_contribution_streak=data.get(
                "qualified_daily_contribution_streak", 0
            ),
        )

```
</details>

#### MongoDBManagement

This class can be used to initalize and use database management. Explained [here](#database-management)


### Scripts
Scripts Explanation
### Helpers
Helper functions explanations
### Database Management
[This](./github_tracker_bot/mongo_data_handler.py) database management script provides functionalities to manage user data and AI decisions in a MongoDB database. It supports creating, reading, updating, and deleting user records, as well as managing AI decisions and contribution data associated with users.

#### Features
1. ##### User Management:
    - **Create, Read, Update, Delete (CRUD) Operations:** Manage user records in the database including creation, retrieval, updating user details, and deletion.
    - **Validation:** Each user instance undergoes validation to ensure data integrity before any CRUD operation.
2. ##### AI Decision Handling:
    - **Retrieve AI Decisions:** Fetch AI decisions based on user identity, with options to filter by date range.
    - **Add AI Decisions:** Append new AI decisions to a user’s existing record.
    - **Update Contribution Data:** Recalculates and updates user statistics based on new AI decisions, utilizing helper functions for detailed metrics like total and qualified contributions, monthly breakdowns, and streak calculations. These calculations made in [here.](./github_tracker_bot/helpers/helper_functions.py)
3. ##### Contribution Data Management:
    - **Get/Set Operations for Contribution Metrics:** Retrieve or update contribution-related metrics such as total daily contributions, qualified contributions, and contribution streaks.
    - **Date-wise Management:** Manage specific dates for qualified contributions, allowing for additions, updates, and retrieval.

-------

## Leaderbot
Discord Bot for interacting with Google Sheets and data received from Github Scraper Bot to Mongo DB.

### Usage
Explained [here](#installation--setup).

Additionally, need to enable google drive api to use sheet sharing functionality.

### Commands

#### **`/commits-sheet-create`**

**Description:** Creates a Google Sheet with contributions data.

**Usage:**

`/commits-sheet-create spreadsheet_name: <name> email_address: <optional email>`

* **spreadsheet_name:** Name for the new Google Sheet.
* **email_address:** (Optional) Email address to share the spreadsheet with. If not provided, the default email from the configuration will be used.

#### **`/commits-sheet-update`**

**Description:** Updates the Google Sheet with the latest contributions data in the Mongo DB. 

**Usage:**

`/commits-sheet-update spreadsheet_id: <id>`

* **spreadsheet_id:** Copy and Paste ID of the Google Sheet to be updated.

#### **`/leaderboard-create`**

**Description:** Creates and updates a leaderboard sheet in the specified sheet for a specific month by using current data. If `spreadsheet_id` is empty it will use the last created or updated sheet id. After creating the leaderboard, it will send the leaderboard to discord channel as message. If the leaderboard exists for specified date, it updates the leaderboard.

**Usage:**

`/leaderboard-create spreadsheet_id: <optional id> date: <YYYY-MM>`

* **spreadsheet_id:** (Optional) ID of the Google Sheet to store the leaderboard. If not provided, the last created or updated sheet will be used.
* **date:** (Optional) Date in "YYYY-MM" format. If not provided, the current month will be used.

#### **`/leaderboard-view`**

**Description:** Displays the leaderboard in the specified Discord Forum thread.

**Usage:**

`/leaderboard-view thread_id: <THREAD_ID> date: <YYYY-MM>`

* **thread_id:** The ID of the thread where the leaderboard should be displayed.
* **date:** (Optional) Date in "YYYY-MM" format. If not provided, the current month will be used.


#### **`/main-sheet-edit`**

**Description:** Creates a modal to edit the Google Sheet which includes commits data from Discord.

**Usage:**

`/main-sheet-edit operation: <operation>`

* **operation:** Operation to perform on the sheet. Valid options are: **`insert`** for adding new user, **`update`** to update user data, **`add_repo`** to add repository, **`delete`** the user data.

#### **`/leaderboard-start-auto-post`**

**Description:** Automatically posts the leaderboard and updates the sheet with given id every day at a specified time.

**Usage:**

`/leaderboard-start-auto-post date: <YYYY-MM> time: <HH:MM> spreadsheet_id: <optional id>`

* **date:** Date in "YYYY-MM" format.
* **time:** Time in "HH-MM" format.
* **spreadsheet_id:** (Optional) ID of the Google Sheet. If not provided, the last created or updated sheet will be used. If not created or updated before, it will post leader bot but will not update any sheet.

#### **`/leaderboard-stop-auto-post`**

**Description:** Stops the auto-post leaderboard task started for a specific date.

**Usage:**

`/leaderboard-stop-auto-post date: <YYYY-MM>`

* **date:** Date in "YYYY-MM" format for which the auto-post task should be stopped.

#### **`/leaderboard-closure-month`**

**Description:** Opens a thread which includes Leaderboard for the month. Gets forum channel id from the .env file.

**Usage:**

`/leaderboard-closure-month: <YYYY-MM>`

* **date:** Date in "YYYY-MM" format.

--------------

## Contributions
To make a contribution, follow these steps:

1. Make an issue that includes details about the feature or bug or something else.
2. Get that issue tested by: Cristina Echeverry.
3. Get that issue approved by the product owners: es92 or Cristina Echeverry.
4. Write a PR and get it approved by the code owners and Mina devops: Es92 (code owner), berkingurcan (developer & codeco-owner), johnmarcou (Mina devops). Each PR must correspond to an approved issue. By default, PRs should be merged by the PR submitter, though in some cases if changes are needed, they can be merged by code owners.
