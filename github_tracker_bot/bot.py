import sys
import os
import json
import asyncio
from collections import OrderedDict
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from log_config import get_logger

logger = get_logger(__name__)


async def main(username, repo_link, since_date, until_date):
    pass



if __name__ == "__main__":
    username = "berkingurcan"
    repo_link = "https://github.com/UmstadAI/zkappumstad"
    since_date = "2023-11-01T00:00:00Z"  # ISO 8601 format
    until_date = "2023-11-30T00:00:00Z"

    asyncio.run(main(username, repo_link, since_date, until_date))
