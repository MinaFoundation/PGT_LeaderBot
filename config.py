import os
from dotenv import load_dotenv

load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

SHARED_SECRET = os.getenv("SHARED_SECRET")

GUILD_ID = os.getenv("GUILD_ID")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
LEADERBOARD_FORUM_CHANNEL_ID = os.getenv("LEADERBOARD_FORUM_CHANNEL_ID")
LEADERBOARD_ADMIN_CHANNEL_ID = int(os.getenv("LEADERBOARD_ADMIN_CHANNEL_ID", "0"))

GOOGLE_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

GTP_ENDPOINT = os.getenv("GTP_ENDPOINT")

# OpenAI API retry configuration
# Maximum number of retry attempts for OpenAI API errors (403, rate limits, server errors, etc.)
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
# Initial delay in seconds before retrying (will increase exponentially with each retry)
OPENAI_INITIAL_RETRY_DELAY = int(os.getenv("OPENAI_INITIAL_RETRY_DELAY", "60"))

if LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    print(f"Invalid log level '{LOG_LEVEL}', defaulting to 'INFO'")
    LOG_LEVEL = "INFO"


MAXIMUM_COMMIT_TOKEN_COUNT = 11000
OPENAI_TOKEN_LIMIT = 124000
