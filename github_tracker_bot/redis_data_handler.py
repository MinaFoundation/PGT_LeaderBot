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
    ai_decisions: List[List[AIDecision]] = field(default_factory=list)
    total_daily_contribution_number: int = 0
    total_qualified_daily_contribution_number: int = 0
    qualified_daily_contribution_number_by_month: Dict[str, int] = field(
        default_factory=dict
    )
    qualified_daily_contribution_dates = set()
    qualified_daily_contribution_streak: int = 0

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

    # USER
    def get_user(self, user_handle: str) -> User:
        pass

    def create_user(self, user: User) -> User:
        pass

    def update_user(self, user: User) -> User:
        pass

    def update_user_handle(self, user_handle: str, updated_user_handle: str) -> User:
        pass

    def update_github_name(self, user_handle: str, update_github_name: str) -> User:
        pass

    def update_repositories(self, user_handle: str, repositories: List[str]) -> User:
        pass

    def delete_user(self, user_handle: str) -> User:
        deleted_data = self.r.delete(f"user:{user_handle}")
        return deleted_data

    # AI DECISIONS
    def get_ai_decisions_by_user(self, user_handle: str) -> List[List[AIDecision]]:
        pass

    def get_ai_decisions_by_user_and_daterange(
        self, user_handle: str, since_data, until_date
    ) -> List[List[AIDecision]]:
        pass

    def add_ai_decisions_by_user(self, user_handle: str, ai_decisions: List[AIDecision]):
        pass

    # CONTRIBUTION DATAS
    def get_total_daily_contribution_number(self, user_handle: str) -> int:
        pass

    def set_total_daily_contribution_number(
        self, user_handle: str, updated_number: int
    ) -> User:
        pass

    def get_total_qualified_daily_contribution_number(self, user_handle: str) -> int:
        pass

    def set_total_qualified_daily_contribution_number(
        self, user_handle: str, updated_number: int
    ) -> User:
        pass

    def get_qualified_daily_contribution_number_by_month(
        self, user_handle: str
    ) -> Dict[str, int]:
        pass

    def set_qualified_daily_contribution_number_by_month(
        self, user_handle: str, month: str, number: str
    ):
        pass

    def get_qualified_daily_contribution_dates(self, user_handle: str):
        pass

    def set_qualified_daily_contribution_dates(
        self, user_handle: str, list_of_dates: List[str]
    ):
        pass

    def get_qualified_daily_contribution_streak(self, user_handle: str):
        pass

    def set_qualified_daily_contribution_streak(
        self, user_handle: str, updated_number: str
    ):
        pass
