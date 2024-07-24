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

