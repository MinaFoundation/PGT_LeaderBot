import github_tracker_bot.helpers.calculate_token as calculator

def handle_daily_exceed_data(daily_commit_data):
    string_data = str(daily_commit_data)
    token_count = calculator.calculate_token_number(string_data)

    if not token_count:
        for commit_data in daily_commit_data:
            commit_data["diff"] = "The diff file exceeds OPENAI token limit. The diff data possibly includes spam data."
    else: 
        return daily_commit_data