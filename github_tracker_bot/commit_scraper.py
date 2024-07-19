import os
import sys
import re
import asyncio
import aiohttp
from typing import Optional, List, Dict, Any
from github import Github, GithubException

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from log_config import get_logger

logger = get_logger(__name__)

GITHUB_TOKEN = config.GITHUB_TOKEN
g = Github(GITHUB_TOKEN)


async def fetch_commits(session: aiohttp.ClientSession, url: str) -> Optional[List[Dict[str, Any]]]:
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    all_commits = []

    while url:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    commits = await response.json()
                    all_commits.extend(commits)

                    if "Link" in response.headers:
                        links = response.headers["Link"]
                        match = re.search(r'<([^>]+)>;\s*rel="next"', links)
                        url = match.group(1) if match else None
                    else:
                        url = None
                else:
                    error_message = await response.text()
                    logger.error(f"Failed to fetch commits: {error_message}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Client error while fetching commits: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while fetching commits: {e}")
            return None

    return all_commits


async def fetch_commits_for_branch(
    session: aiohttp.ClientSession,
    owner: str,
    repo_name: str,
    username: str,
    branch_name: str,
    since: str,
    until: str,
    existing_shas: set
) -> List[Dict[str, Any]]:
    commits_url = (
        f"https://api.github.com/repos/{owner}/{repo_name}/commits"
        f"?author={username}&sha={branch_name}&since={since}&until={until}"
    )

    commits = await fetch_commits(session, commits_url)
    commit_infos = []

    if commits:
        for commit in commits:
            commit_sha = commit["sha"]
            if commit_sha not in existing_shas:
                commit_info = {
                    "message": commit["commit"]["message"],
                    "date": commit["commit"]["committer"]["date"],
                    "branch": branch_name,
                    "sha": commit_sha,
                    "author": commit["commit"]["author"]["name"],
                    "username": username,
                    "repo": f"{owner}/{repo_name}",
                }
                commit_infos.append(commit_info)
                existing_shas.add(commit_sha)
                logger.debug(f"Commit Info: {commit_info}")

    return commit_infos


async def get_user_commits_in_repo(username: str, repo_link: str, since: str, until: str) -> Optional[List[Dict[str, Any]]]:
    repo_pattern = re.compile(r"https?://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/?$")
    if not repo_pattern.match(repo_link):
        logger.error("Invalid GitHub repository link format.")
        return None

    try:
        _, owner_repo = repo_link.split("github.com/", 1)
        owner, repo_name = owner_repo.rstrip("/").split("/")

        repo = g.get_repo(f"{owner}/{repo_name}")
        branches = repo.get_branches()

        existing_shas = set()
        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_commits_for_branch(session, owner, repo_name, username, branch.name, since, until, existing_shas)
                for branch in branches
            ]

            results = await asyncio.gather(*tasks)
            commit_infos = [commit_info for result in results for commit_info in result]

        logger.debug(commit_infos)
        logger.debug(f"Total commit number in the array: {len(commit_infos)}")

        return commit_infos

    except GithubException as e:
        logger.error(f"GitHub API Error: {e}")
        return None


if __name__ == "__main__":
    since_date = "2024-07-03T00:00:00Z"  # ISO 8601 format
    until_date = "2024-07-04T00:00:00Z"

    asyncio.run(
        get_user_commits_in_repo(
            "berkingurcan",
            "https://github.com/UmstadAI/zkAppUmstad",
            since_date,
            until_date,
        )
    )
