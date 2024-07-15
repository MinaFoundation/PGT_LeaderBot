import tiktoken
import github_tracker_bot.prompts as prompts

from log_config import get_logger

logger = get_logger(__name__)

def calculate_token_number(data):
    system_token_count = prompts.SYSTEM_MESSAGE_DAILY_DECIDE_COMMIT
    message_token_count = 1000

    enc = tiktoken.encoding_for_model("gpt-4o")
    token_integers = enc.encode(system_token_count + " " + data)
    num_token = len(token_integers) + message_token_count

    logger.debug(f"Number of tokens are: {num_token}")

    return num_token < 120000
