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
class User:
    user_handle: str
    github_name: str
    repositories: List[str]
    total_daily_contribution_number: int = 0
    total_qualified_daily_contribution_number: int = 0
    qualified_daily_contribution_number_by_month: Dict[str, int] = field(
        default_factory=dict
    )
    qualified_daily_contribution_streak: int = 0

    def validate(self) -> bool:
        if not isinstance(self.repositories, list) or not all(
            isinstance(repo, str) for repo in self.repositories
        ):
            logger.error("Invalid repository list")
            return False
        return True


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


class RedisClient:
    def __init__(self, host="localhost", port=6379, db=0):
        try:
            self.r = redis.Redis(host=host, port=port, db=db)
            self.r.ping()
            logger.info("Connected to Redis")
        except redis.RedisError as e:
            logger.error(f"Redis connection failed: {e}")
            raise ConnectionError("Failed to connect to Redis")

    def save_user(self, user: User):
        if user.validate():
            self.r.hset(f"user:{user.user_handle}", user.__dict__)

    def get_user(self, user_handle: str) -> User:
        data = self.r.hgetall(f"user:{user_handle}")
        if data:
            user_dict = {
                k.decode("utf-8"): (
                    json.loads(v)
                    if k
                    in ["repositories", "qualified_daily_contribution_number_by_month"]
                    else v.decode("utf-8")
                )
                for k, v in data.items()
            }
            return User(**user_dict)
        return None

    def save_decision(self, decision: AIDecision):
        key = f"decision:{decision.username}:{decision.date}"
        decision_dict = decision.__dict__.copy()
        decision_dict["response"] = decision.response.__dict__
        self.r.set(key, json.dumps(decision_dict))

    def get_decision(self, username: str, date: str) -> AIDecision:
        data = self.r.get(f"decision:{username}:{date}")
        if data:
            decision_dict = json.loads(data)
            response_dict = decision_dict.pop("response")
            decision_dict["response"] = DailyContributionResponse(**response_dict)
            return AIDecision(**decision_dict)
        return None
