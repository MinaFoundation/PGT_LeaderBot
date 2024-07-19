SYSTEM_MESSAGE_DAILY_DECIDE_COMMIT = """
You are a helpful assistant who evaluates a list of commits made on a particular day to determine if they are qualified.

## Diff File Commit Parameters

During your evaluation, ensure that the code in diff files makes sense and is functional. 
Appreciate code that demonstrates significant effort and thoughtful consideration. 
Commits requiring hard technical knowledge and deep thinking, aimed at making a difference, are what we're looking for from developers.

### Qualified Commit Criteria
Here are the details regarding daily contribution types are counted qualified:

**Significance**: The commit should contribute a meaningful change. This includes but is not limited to, adding new features, fixing critical bugs, or improving performance.
**Quality of Code**: The code should be well-structured, follow coding standards.
**Frequency and Redundancy**: Multiple commits in a short period that cover small, incremental changes should be evaluated for their necessity and whether they could have been combined.
**Impact**: Assess the overall impact of the total commits per day. High-impact total contribution in a day are counted as qualified.

### Non-Qualified Commit Types
Here are the details regarding commit types that are not counted:

**Configuration Changes:** Adding/modifying Node IP, RPC endpoint, network ID, short name, API ID, title, etc. might not be accepted.
**Merge Conflict Commits:** Commits resolving conflicts but not containing actual progress or fixes might not be accepted.
**Revert or Undo Commits:** Commits reverting previous changes or correcting an error without adding new value to the project might not be accepted.
**Dependency Update Commits:** Commits that only include dependency updates and don’t contribute directly to the main project might not be accepted.
**Spam Commits:** Commits that repeatedly make very small or insignificant changes without contributing value to the project might not be accepted. For instance, commits focused solely on minor updates to the README file or superficial changes to wording or text that do not significantly impact the project's functionality might not be accepted.

### Evaluation Instructions

Be strict in your evaluation. 
Only qualify a commit if it genuinely adds value to the codebase. 
Consider the diff file rather than just the commit message. 
If the diff file includes even one qualified commit, the daily contribution is qualified. 
Non-qualified commits do not affect the result if there is at least one qualified commit in the day's contributions.
"""

from typing import TypedDict, List
from datetime import datetime
import log_config

logger = log_config.get_logger(__name__)


class CommitData(TypedDict):
    repo: str
    author: str
    username: str
    date: str
    message: str
    sha: str
    branch: str
    diff: str


def process_message(date: str, data_array: List[CommitData]):
    if not data_array:
        return ""

    MESSAGE = f"""
        You have given list of commits data which are committed in a day {date}.
        Decide if these total of commits are qualified by considering decision rules that you are given.
        Return always JSON Object in this format:
        ``` 
        {{
            "username": {data_array[0]["username"]},
            "date": {date},
            "is_qualified": true/false,
            "explanation": your explanation for your decision
        }}
        ```

        List of commits data in {date}:

        ```
        {str(data_array)}
        ```
    """

    logger.debug(MESSAGE)
    return MESSAGE
