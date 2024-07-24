FROM python:3.10.7

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Possible [ github_tracker_bot/bot.py (default), leader_bot/bot.py ]
CMD ["python", "github_tracker_bot/bot.py"]
