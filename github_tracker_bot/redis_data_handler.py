import sys
import os

import redis
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from log_config import get_logger

logger = get_logger(__name__)


@dataclass
class DailyContributionResponse:
    username: str
    date: str
    is_qualified: bool
    explanation: str

    def to_dict(self):
        return asdict(self)


@dataclass
class AIDecision:
    username: str
    repository: str
    date: str
    response: DailyContributionResponse

    def to_dict(self):
        data = asdict(self)
        data["response"] = self.response.to_dict()
        return data


@dataclass
class User:
    user_handle: str
    github_name: str
    repositories: List[str]
    total_daily_contribution_number: int = 0
    total_qualified_daily_contribution_number: int = 0
    qualified_daily_contribution_number_by_month: Dict[str, int] = field(
        default_factory=dict
    )
    qualified_daily_contribution_dates = set()
    qualified_daily_contribution_streak: int = 0
    ai_decisions: List[List[AIDecision]] = field(default_factory=list)

    def validate(self) -> bool:
        if not isinstance(self.repositories, list) or not all(
            isinstance(repo, str) for repo in self.repositories
        ):
            logger.error("Invalid repository list")
            return False
        return True


def create_ai_decisions_class(data):
    decisions = []
    for entry in data:
        response_data = entry["response"]
        response = DailyContributionResponse(
            username=response_data["username"],
            date=response_data["date"],
            is_qualified=response_data["is_qualified"],
            explanation=response_data["explanation"],
        )
        decision = AIDecision(
            username=entry["username"],
            repository=entry["repository"],
            date=entry["date"],
            response=response,
        )
        decisions.append(decision)
    return decisions


class RedisClient:
    def __init__(self, host="localhost", port=6379, db=0, decode_responses=True):
        try:
            self.r = redis.Redis(host=host, port=port, db=db)
            self.r.ping()
            logger.info("Connected to Redis")
        except redis.RedisError as e:
            logger.error(f"Redis connection failed: {e}")
            raise ConnectionError("Failed to connect to Redis")

    def save_user(self, user: User):
        pass

    def get_user(self, user_handle: str) -> User:
        pass

    def delete_user(self, user_handle: str) -> User:
        deleted_data = self.r.delete(f"user:{user_handle}")
        return deleted_data

    def get_ai_decisions_by_user(self, user_handle: str) -> List[List[AIDecision]]:
        user = self.get_user(user_handle)
        if user:
            return user.ai_decisions
        return []

    def get_ai_decisions_by_user_and_daterange(
        self, user_handle: str, since_data, until_date
    ) -> List[List[AIDecision]]:
        pass
