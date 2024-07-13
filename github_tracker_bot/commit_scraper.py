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


async def fetch_commits(
    session: aiohttp.ClientSession, url: str
) -> Optional[List[Dict[str, Any]]]:
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


async def get_user_commits_in_repo(
    username: str, repo_link: str, since: str, until: str
) -> Optional[List[Dict[str, Any]]]:
    repo_pattern = re.compile(r"https?://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/?$")
    if not repo_pattern.match(repo_link):
        logger.error("Invalid GitHub repository link format.")
        return

    try:
        _, owner_repo = repo_link.split("github.com/", 1)
        owner, repo_name = owner_repo.rstrip("/").split("/")

        repo = g.get_repo(f"{owner}/{repo_name}")
        branches = repo.get_branches()

        commit_infos = []
        existing_shas = set()

        async with aiohttp.ClientSession() as session:
            main_branch = None
            other_branches = []

            for branch in branches:
                if branch.name == "main":
                    main_branch = branch
                else:
                    other_branches.append(branch)

            if main_branch:
                branch_name = main_branch.name
                commits_url = (
                    f"https://api.github.com/repos/{owner}/{repo_name}/commits"
                    f"?author={username}&sha={main_branch.name}&since={since}&until={until}"
                )

                commits = await fetch_commits(session, commits_url)

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

            for branch in other_branches:
                branch_name = branch.name
                commits_url = (
                    f"https://api.github.com/repos/{owner}/{repo_name}/commits"
                    f"?author={username}&sha={branch.name}&since={since}&until={until}"
                )

                commits = await fetch_commits(session, commits_url)

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
                        else:
                            continue
                else:
                    logger.info(
                        f"No commits found for user {username} in {repo_name}, {branch.name} branch."
                    )

                logger.debug(
                    f"{username} has {len(commits)} commits in {branch.name} branch"
                )

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
