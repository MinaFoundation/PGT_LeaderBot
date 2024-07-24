# LeaderBot
Tool that will track and rank contributions across the different Mina developer programs.

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
    ```

6. You need to have google credentials .json file which has access your spreadsheet in the root folder. [Click for more information.](https://developers.google.com/workspace/guides/create-credentials)

7. Run tests:
    ```sh
    invoke test
    ```

8. Run github tracker bot:
    ```sh
    invoke bot
    ```

    For other invoke tasks look to: [tasks.py](./tasks.py)

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

#### 2. Control Scheduler

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


