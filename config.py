import os
from dotenv import load_dotenv

load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GUILD_ID = os.getenv("GUILD_ID")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
LEADERBOARD_FORUM_CHANNEL_ID = os.getenv("LEADERBOARD_FORUM_CHANNEL_ID")

GOOGLE_CREDENTIALS = "leaderbot-kr-6dc75af94571.json"

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

ENDPOINT = os.getenv("ENDPOINT")

if LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    print(f"Invalid log level '{LOG_LEVEL}', defaulting to 'INFO'")
    LOG_LEVEL = "INFO"


MAXIMUM_COMMIT_TOKEN_COUNT = 11000
OPENAI_TOKEN_LIMIT = 124000
