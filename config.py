import os
from dotenv import load_dotenv

load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

GOOGLE_CREDENTIALS = "leaderbot-kr-6dc75af94571.json"
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

if LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    print(f"Invalid log level '{LOG_LEVEL}', defaulting to 'INFO'")
    LOG_LEVEL = "INFO"


MAXIMUM_COMMIT_TOKEN_COUNT = 11000
OPENAI_TOKEN_LIMIT = 124000
