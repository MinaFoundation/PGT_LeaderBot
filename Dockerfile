FROM python:3.10.7

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY github_tracker_bot github_tracker_bot
COPY leader_bot leader_bot
COPY utils utils
COPY config.py .
COPY log_config.py .
COPY __init__.py .

# Possible [ github_tracker_bot/bot.py (default), leader_bot/bot.py ]
CMD ["python", "github_tracker_bot/bot.py"]
