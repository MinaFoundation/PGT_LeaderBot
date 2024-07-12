import os
import sys
import asyncio
import aiohttp
from typing import List, Optional, Dict, Any

from github import Github

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from log_config import get_logger

logger = get_logger(__name__)

GITHUB_TOKEN = config.GITHUB_TOKEN
g = Github(GITHUB_TOKEN)

async def fetch_diff(repo: str, sha: str) -> Optional[str]:
    url = f"https://api.github.com/repos/{repo}/commits/{sha}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    commit_data = await response.json()
                    diff_url = commit_data["html_url"] + ".diff"

                    async with session.get(diff_url, headers=headers) as diff_response:
                        if diff_response.status == 200:
                            return await diff_response.text()
                        else:
                            logger.error(f"Failed to fetch diff: {await diff_response.text()}")
                            return None
                else:
                    logger.error(f"Failed to fetch commit data: {await response.text()}")
                    return None
    except aiohttp.ClientError as e:
        logger.error(f"Client error while fetching diff: {e}")
        return None
    except asyncio.TimeoutError:
        logger.error("Request timed out while fetching diff")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while fetching diff: {e}")
        return None

def concatenate_diff_to_commit_info(commit_info: Dict[str, Any], diff: Optional[str]) -> Dict[str, Any]:
    result = {
        "repo": commit_info["repo"],
        "author": commit_info["author"],
        "date": commit_info["date"],
        "message": commit_info["message"],
        "sha": commit_info["sha"],
        "branch": commit_info["branch"],
    }
    
    if diff is not None:
        result["diff"] = diff
    else:
        result["diff"] = ""
    
    return result

async def process_commits(commit_infos: List[Dict[str, Any]]):
    processed_commits = []
    for commit_info in commit_infos:
        diff = await fetch_diff(commit_info["repo"], commit_info["sha"])
        processed_commit = concatenate_diff_to_commit_info(commit_info, diff)
        processed_commits.append(processed_commit)
        logger.debug(f"Processed commit: {processed_commit}")
    
    return processed_commits

if __name__ == "__main__":
    repo_name = "UmstadAI/zkAppUmstad"
    sha = "092c20a73859e0b4a4591f815efbdcab08df4df8"
    diff = asyncio.run(fetch_diff(repo_name, sha))

    if diff:
        logger.info(f"Fetched diff successfully: {diff}")
    else:
        logger.error("Failed to fetch diff")
