import sys
import os

import config

from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Union

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure

from log_config import get_logger

logger = get_logger(__name__)


@dataclass
class DailyContributionResponse:
    username: str
    date: str
    is_qualified: bool
    explanation: str

    def to_dict(self):
        """Converts the dataclass to a dictionary."""
        return asdict(self)


@dataclass
class AIDecision:
    username: str
    repository: str
    date: str
    response: DailyContributionResponse

    def to_dict(self):
        """Converts the dataclass to a dictionary, including nested response."""
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
    qualified_daily_contribution_dates: set = field(default_factory=set)
    qualified_daily_contribution_streak: int = 0

    def validate(self) -> bool:
        """Validates the User instance."""
        if not isinstance(self.repositories, list) or not all(
            isinstance(repo, str) for repo in self.repositories
        ):
            logger.error("Invalid repository list")
            return False
        return True

    def to_dict(self):
        """Converts the dataclass to a dictionary."""
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

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "User":
        """Creates a User instance from a dictionary."""
        ai_decisions = [
            [
                AIDecision(
                    username=decision["username"],
                    repository=decision["repository"],
                    date=decision["date"],
                    response=DailyContributionResponse(
                        username=decision["response"]["username"],
                        date=decision["response"]["date"],
                        is_qualified=decision["response"]["is_qualified"],
                        explanation=decision["response"]["explanation"],
                    ),
                )
                for decision in decisions
            ]
            for decisions in data.get("ai_decisions", [])
        ]
        return User(
            user_handle=data["user_handle"],
            github_name=data["github_name"],
            repositories=data.get("repositories", []),
            ai_decisions=ai_decisions,
            total_daily_contribution_number=data.get(
                "total_daily_contribution_number", 0
            ),
            total_qualified_daily_contribution_number=data.get(
                "total_qualified_daily_contribution_number", 0
            ),
            qualified_daily_contribution_number_by_month=data.get(
                "qualified_daily_contribution_number_by_month", {}
            ),
            qualified_daily_contribution_dates=set(
                data.get("qualified_daily_contribution_dates", [])
            ),
            qualified_daily_contribution_streak=data.get(
                "qualified_daily_contribution_streak", 0
            ),
        )


class MongoDBManagement:
    def __init__(self, db, collection):
        self.db = db
        self.collection: Collection = collection

    # USER
    def get_user(self, user_handle: str) -> Optional[User]:
        try:
            user_data = self.collection.find_one({"user_handle": user_handle})
            if user_data:
                user = User.from_dict(user_data)

                if not user.validate():
                    logger.error("Invalid user data")
                    return None
                return user
            return None
        except Exception as e:
            logger.error(f"Cannot find the user with handle '{user_handle}': {e}")
            raise

    def create_user(self, user: Any) -> Optional[User]:
        try:
            if not user.validate():
                raise ValueError("Invalid user data")

            user_dict = user.to_dict()
            result = self.collection.insert_one(user_dict)
            if result.inserted_id:
                return user
            else:
                raise RuntimeError("Failed to insert user into the database")
        except Exception as e:
            logger.error(f"Failed to create user {user.user_handle}: {e}")
            raise

    def update_user(self, user_handle: str, update_user: User) -> Optional[User]:
        """Updates an existing user in the database."""
        try:
            if not self.get_user(user_handle):
                return None

            if not update_user.validate():
                raise ValueError("Invalid user data")

            update_user_dict = update_user.to_dict()
            result = self.collection.update_one(
                {"user_handle": user_handle}, {"$set": update_user_dict}
            )
            if result.modified_count > 0:
                return self.get_user(update_user_dict["user_handle"])
            else:
                raise RuntimeError(
                    f"Failed to update user {user_handle} in the database"
                )
        except Exception as e:
            logger.error(f"Failed to update user, {user_handle}: {e}")
            raise

    def update_field(self, user_handle: str, field_name: str, field_value: Any) -> Any:
        """Updates a specific field of a user in the database."""
        try:
            result = self.collection.update_one(
                {"user_handle": user_handle}, {"$set": {field_name: field_value}}
            )
            if result.modified_count > 0:
                return field_value
            else:
                raise RuntimeError(
                    f"Failed to update {field_name} for user {user_handle}"
                )
        except Exception as e:
            logger.error(f"Failed to update {field_name}: {e}")
            raise

    def delete_user(self, user_handle: str) -> Optional[str]:
        """Deletes a user from the database."""
        try:
            result = self.collection.delete_one({"user_handle": user_handle})
            if result.deleted_count > 0:
                return user_handle
            return None
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            raise

    # AI DECISIONS
    def get_ai_decisions_by_user(self, user_handle: str) -> List[List[AIDecision]]:
        """Retrieves AI decisions for a specific user."""
        try:
            user = self.get_user(user_handle)
            if user:
                return user.ai_decisions
            return []
        except Exception as e:
            logger.error(f"Failed to get AI decisions for user {user_handle}: {e}")
            raise

    def add_ai_decisions_by_user(
        self, user_handle: str, ai_decisions: List[AIDecision]
    ):
        """Adds AI decisions to a specific user."""
        try:
            user = self.get_user(user_handle)
            if not user:
                raise ValueError(f"User with handle '{user_handle}' does not exist")

            user.ai_decisions.append(ai_decisions)
            result = self.update_user(user_handle, user)
            return result
        except Exception as e:
            logger.error(f"Failed to add AI decisions for user {user_handle}: {e}")
            raise

    def get_ai_decisions_by_user_and_daterange(
        self, user_handle: str, since_date, until_date
    ) -> List[List[AIDecision]]:
        """Retrieves AI decisions for a specific user within a date range."""
        try:
            user = self.get_user(user_handle)
            if not user:
                return []

            since_dt = datetime.strptime(since_date, "%Y-%m-%d")
            until_dt = datetime.strptime(until_date, "%Y-%m-%d")

            filtered_decisions = []
            for decision_list in user.ai_decisions:
                filtered_list = [
                    decision
                    for decision in decision_list
                    if since_dt
                    <= datetime.strptime(decision.date, "%Y-%m-%d")
                    <= until_dt
                ]
                if filtered_list:
                    filtered_decisions.append(filtered_list)

            return filtered_decisions
        except Exception as e:
            logger.error(
                f"Failed to get AI decisions for user {user_handle} in date range: {e}"
            )
            raise

    # CONTRIBUTION DATAS
    def get_total_daily_contribution_number(self, user_handle: str) -> int:
        """Retrieves the total daily contribution number for a specific user."""
        try:
            user = self.get_user(user_handle)
            if user:
                return user.total_daily_contribution_number
            return 0
        except Exception as e:
            logger.error(
                f"Failed to get total daily contribution number for user {user_handle}: {e}"
            )
            raise

    def set_total_daily_contribution_number(
        self, user_handle: str, updated_number: int
    ) -> Optional[User]:
        """Sets the total daily contribution number for a specific user."""
        try:
            user = self.get_user(user_handle)
            if not user:
                raise ValueError(f"User with handle '{user_handle}' does not exist")

            user.total_daily_contribution_number = updated_number
            updated_user = self.update_user(user_handle, user)
            return updated_user
        except Exception as e:
            logger.error(
                f"Failed to set total daily contribution number for user {user_handle}: {e}"
            )
            raise

    def get_total_qualified_daily_contribution_number(self, user_handle: str) -> int:
        """Retrieves the total qualified daily contribution number for a specific user."""
        try:
            user = self.get_user(user_handle)
            if user:
                return user.total_qualified_daily_contribution_number
            return 0
        except Exception as e:
            logger.error(
                f"Failed to get total qualified daily contribution number for user {user_handle}: {e}"
            )
            raise

    def set_total_qualified_daily_contribution_number(
        self, user_handle: str, updated_number: int
    ) -> Optional[User]:
        """Sets the total qualified daily contribution number for a specific user."""
        try:
            user = self.get_user(user_handle)
            if not user:
                raise ValueError(f"User with handle '{user_handle}' does not exist")

            user.total_qualified_daily_contribution_number = updated_number
            updated_user = self.update_user(user_handle, user)
            return updated_user
        except Exception as e:
            logger.error(
                f"Failed to set total qualified daily contribution number for user {user_handle}: {e}"
            )
            raise

    def get_qualified_daily_contribution_number_by_month(
        self, user_handle: str
    ) -> Dict[str, int]:
        """Retrieves the qualified daily contribution number by month for a specific user."""
        try:
            user = self.get_user(user_handle)
            if user:
                return user.qualified_daily_contribution_number_by_month
            return 0
        except Exception as e:
            logger.error(
                f"Failed to get total qualified daily contribution number for user {user_handle}: {e}"
            )
            raise

    def set_qualified_daily_contribution_number_by_month(
        self, user_handle: str, set_of_data: Dict[str, int]
    ):
        """Sets the qualified daily contribution number by month for a specific user."""
        try:
            user = self.get_user(user_handle)
            if not user:
                raise ValueError(f"User with handle '{user_handle}' does not exist")

            user.qualified_daily_contribution_number_by_month = set_of_data
            updated_user = self.update_user(user_handle, user)
            return updated_user
        except Exception as e:
            logger.error(
                f"Failed to set total qualified daily contribution number for user {user_handle}: {e}"
            )
            raise

    def add_qualified_daily_contribution_number_by_month(
        self, user_handle: str, year: str, month: str, number: int
    ):
        """Adds one qualified daily contribution number with year, month and number strings. If dates exists, replaces with new value."""
        try:
            user = self.get_user(user_handle)
            if not user:
                raise ValueError(f"User with handle '{user_handle}' does not exist")

            current_data = user.qualified_daily_contribution_number_by_month

            key = f"{year}-{month.zfill(2)}"

            current_data[key] = number

            user.qualified_daily_contribution_number_by_month = current_data
            updated_user = self.update_user(user_handle, user)

            return updated_user
        except Exception as e:
            logger.error(
                f"Failed to add qualified daily contribution number by month for user {user_handle}: {e}"
            )
            raise

    def get_qualified_daily_contribution_dates(self, user_handle: str) -> set:
        """Retrieves the qualified daily contribution dates for a specific user."""
        try:
            user = self.get_user(user_handle)
            if user:
                return user.qualified_daily_contribution_dates
            return 0
        except Exception as e:
            logger.error(
                f"Failed to get total qualified daily contribution dates {user_handle}: {e}"
            )
            raise

    def set_qualified_daily_contribution_dates(
        self, user_handle: str, set_of_dates: Union[set, List[str]]
    ):
        """Sets in a set qualified daily contribution dates"""
        try:
            user = self.get_user(user_handle)
            if not user:
                raise ValueError(f"User with handle '{user_handle}' does not exist")

            set_of_dates_to_dict = dict.fromkeys(set_of_dates, 1)
            updated_user = self.update_field(user_handle, "qualified_daily_contribution_dates", set_of_dates_to_dict)
            return updated_user
        except Exception as e:
            logger.error(
                f"Failed to set total qualified daily contribution dates for user {user_handle}: {e}"
            )
            raise

    def add_qualified_daily_contribution_dates(
        self, user_handle: str, dates: List[str]
    ):
        """Adds date or dates to qualified daily contribution dates set"""
        try:
            user = self.get_user(user_handle)
            if not user:
                raise ValueError(f"User with handle '{user_handle}' does not exist")

            new_set_dates = user.qualified_daily_contribution_dates

            for date in dates:
                new_set_dates.add(date)

            updated_user = self.set_qualified_daily_contribution_dates(
                user_handle, new_set_dates
            )

            return updated_user

        except Exception as e:
            logger.error(
                f"Failed to add qualified daily contribution dates for user {user_handle}: {e}"
            )
            raise

    def get_qualified_daily_contribution_streak(self, user_handle: str):
        """Retrieves the qualified daily contribution streak for a specific user."""
        try:
            user = self.get_user(user_handle)
            if user:
                return user.qualified_daily_contribution_streak
            return 0
        except Exception as e:
            logger.error(
                f"Failed to get qualified daily contribution streak for user {user_handle}: {e}"
            )
            raise

    def set_qualified_daily_contribution_streak(
        self, user_handle: str, updated_number: str
    ):
        """Sets the total daily contribution streak for a specific user."""
        try:
            user = self.get_user(user_handle)
            if not user:
                raise ValueError(f"User with handle '{user_handle}' does not exist")

            user.qualified_daily_contribution_streak = updated_number
            updated_user = self.update_user(user_handle, user)
            return updated_user
        except Exception as e:
            logger.error(
                f"Failed to set total daily contribution number for user {user_handle}: {e}"
            )
            raise
