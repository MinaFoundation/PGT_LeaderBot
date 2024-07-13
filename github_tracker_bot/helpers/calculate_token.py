# Calculate token with Prompts and diffs
# Return if exceeds
# if exceeds use divider(diff_divider.py)
# use it before ``message = prompts.process_message(date, data_array)`` and give separate arrays according to exceed
import tiktoken
import github_tracker_bot.prompts as prompts


def calculate_token_number(data):
    system_token_count = prompts.SYSTEM_MESSAGE_DAILY_DECIDE_COMMIT
    message_token_count = 1000

    enc = tiktoken.encoding_for_model("gpt-4o")
    token_integers = enc.encode(system_token_count + " " + data)
    num_token = len(token_integers) + message_token_count

    return num_token < 120000
