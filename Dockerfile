FROM python:3.10.7-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]

# Possible [ github_tracker_bot/bot.py (default), leader_bot/bot.py ]
CMD ["github_tracker_bot/bot.py"]
