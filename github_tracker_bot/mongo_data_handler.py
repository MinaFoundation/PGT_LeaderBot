import sys
import os

import json
import config

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pymongo import MongoClient
from pymongo.collection import Collection

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


def get_database():
    client = MongoClient(config.MONGO_HOST)
    return client[config.MONGO_DB]


class MongoDBManagement:
    def __init__(self, db, collection):
        self.db = db
        self.collection: Collection = collection

    # USER
    def get_user(self, user_handle: str) -> Optional[User]:
        try:
            user_data = self.collection.find_one({"user_handle": user_handle})
            if user_data:
                return user_data
            return None
        except Exception as e:
            logger.error(f"Cannot find the user with handle '{user_handle}': {e}")
            raise

    def create_user(self, user: Any) -> User:
        try:
            if not user.validate():
                raise ValueError("Invalid user data")

            user_dict = user.to_dict()
            result = self.collection.insert_one(user_dict)
            if result.inserted_id:
                return user_dict
            else:
                raise RuntimeError("Failed to insert user into the database")
        except ValueError as e:
            logger.error(f"User validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

    def update_user(self, user: User) -> User:
        pass

    def update_user_handle(self, user_handle: str, updated_user_handle: str) -> User:
        pass

    def update_github_name(self, user_handle: str, update_github_name: str) -> User:
        pass

    def update_repositories(self, user_handle: str, repositories: List[str]) -> User:
        pass

    def delete_user(self, user_handle: str) -> User:
        pass

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
