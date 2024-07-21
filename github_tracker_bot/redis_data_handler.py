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

    def to_dict(self):
        return {
            "user_handle": self.user_handle,
            "github_name": self.github_name,
            "repositories": self.repositories,
            "ai_decisions": [
                [decision.to_dict() for decision in decisions]
                for decisions in self.ai_decisions
            ],
            "total_daily_contribution_number": self.total_daily_contribution_number,
            "total_qualified_daily_contribution_number": self.total_qualified_daily_contribution_number,
            "qualified_daily_contribution_number_by_month": self.qualified_daily_contribution_number_by_month,
            "qualified_daily_contribution_dates": list(
                self.qualified_daily_contribution_dates
            ),
            "qualified_daily_contribution_streak": self.qualified_daily_contribution_streak,
        }


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
            self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.r.ping()
            logger.info("Connected to Redis")
        except redis.RedisError as e:
            logger.error(f"Redis connection failed: {e}")
            raise ConnectionError("Failed to connect to Redis")

    # USER
    def get_user(self, user_handle: str) -> User:
        try:
            user_data = self.r.get(f"user:{user_handle}")
            if user_data:
                user_dict = user_data
                return User(**user_dict)
            return None
        except redis.RedisError as e:
            logger.error(f"Failed to get user {user_handle}: {e}")
            raise

    def create_user(self, user: User) -> User:
        try:
            if not user.validate():
                raise ValueError("Invalid user data")
            user_data = json.dumps(user.to_dict())
            self.r.set(f"user:{user.user_handle}", user_data)
            return user
        except redis.RedisError as e:
            logger.error(f"Failed to create user {user.user_handle}: {e}")
            raise
        except ValueError as e:
            logger.error(e)
            raise

    def update_user(self, user: User) -> User:
        try:
            if not self.r.exists(f"user:{user.user_handle}"):
                raise KeyError(f"User {user.user_handle} does not exist")
            if not user.validate():
                raise ValueError("Invalid user data")
            user_data = json.dumps(user.to_dict())
            self.r.set(f"user:{user.user_handle}", user_data)
            return user
        except redis.RedisError as e:
            logger.error(f"Failed to update user {user.user_handle}: {e}")
            raise
        except KeyError as e:
            logger.error(e)
            raise
        except ValueError as e:
            logger.error(e)
            raise

    def update_user_handle(self, user_handle: str, updated_user_handle: str) -> User:
        try:
            if not self.r.exists(f"user:{user_handle}"):
                raise KeyError(f"User {user_handle} does not exist")
            user_data = self.r.get(f"user:{user_handle}")
            user_dict = user_data
            user_dict["user_handle"] = updated_user_handle
            self.r.set(f"user:{updated_user_handle}", json.dumps(user_dict))
            self.r.delete(f"user:{user_handle}")
            return User(**user_dict)
        except redis.RedisError as e:
            logger.error(f"Failed to update user handle from {user_handle} to {updated_user_handle}: {e}")
            raise
        except KeyError as e:
            logger.error(e)
            raise

    def update_github_name(self, user_handle: str, update_github_name: str) -> User:
        try:
            if not self.r.exists(f"user:{user_handle}"):
                raise KeyError(f"User {user_handle} does not exist")
            user_data = self.r.get(f"user:{user_handle}")
            user_dict = user_data
            user_dict["github_name"] = update_github_name
            self.r.set(f"user:{user_handle}", json.dumps(user_dict))
            return User(**user_dict)
        except redis.RedisError as e:
            logger.error(f"Failed to update GitHub name for user {user_handle}: {e}")
            raise
        except KeyError as e:
            logger.error(e)
            raise

    def update_repositories(self, user_handle: str, repositories: List[str]) -> User:
        try:
            if not self.r.exists(f"user:{user_handle}"):
                raise KeyError(f"User {user_handle} does not exist")
            user_data = self.r.get(f"user:{user_handle}")
            user_dict = user_data
            user_dict["repositories"] = repositories
            self.r.set(f"user:{user_handle}", json.dumps(user_dict))
            return User(**user_dict)
        except redis.RedisError as e:
            logger.error(f"Failed to update repositories for user {user_handle}: {e}")
            raise
        except KeyError as e:
            logger.error(e)
            raise

    def delete_user(self, user_handle: str) -> User:
        try:
            deleted_data = self.r.delete(f"user:{user_handle}")
            return deleted_data == 1
        except redis.RedisError as e:
            logger.error(f"Failed to delete user {user_handle}: {e}")
            raise

    # AI DECISIONS
    def get_ai_decisions_by_user(self, user_handle: str) -> List[List[AIDecision]]:
        pass

    def get_ai_decisions_by_user_and_daterange(
        self, user_handle: str, since_data, until_date
    ) -> List[List[AIDecision]]:
        pass

    def add_ai_decisions_by_user(
        self, user_handle: str, ai_decisions: List[AIDecision]
    ):
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
