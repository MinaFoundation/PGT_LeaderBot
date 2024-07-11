import os
import sys
import re
import asyncio
import aiohttp

from github import Github, GithubException

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from log_config import get_logger

logger = get_logger(__name__)

GITHUB_TOKEN = config.GITHUB_TOKEN
g = Github(GITHUB_TOKEN)

async def fetch_commits(session, url):
    headers = {'Authorization': 'token ' + GITHUB_TOKEN}
    all_commits = []
    
    while url:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                commits = await response.json()
                all_commits.extend(commits)

                if 'Link' in response.headers:
                    links = response.headers['Link']
                    match = re.search(r'<([^>]+)>;\s*rel="next"', links)
                    url = match.group(1) if match else None
                else:
                    url = None
            else:
                error_message = await response.text()
                logger.error(f"Failed to fetch commits: {error_message}")
                return None
    
    return all_commits

async def get_user_commits_in_repo(username, repo_link):
    if not re.match(r'https?://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/?$', repo_link):
        logger.error("Invalid GitHub repository link format.")
        return
    
    try:
        _, owner_repo = repo_link.split("github.com/", 1)
        owner, repo_name = owner_repo.rstrip("/").split("/")

        repo = g.get_repo(f"{owner}/{repo_name}")

        commits_url = f"https://api.github.com/repos/{owner}/{repo_name}/commits?author={username}"

        async with aiohttp.ClientSession() as session:
            commits = await fetch_commits(session, commits_url)
            if commits:
                for commit in commits:
                    commit_info = {
                        'message': commit['commit']['message'],
                        'date': commit['commit']['committer']['date']
                    }
                    logger.debug(f"Commit Info: {commit_info}")
            else:
                logger.info(f"No commits found for user {username} in {repo_name}.")
            
            logger.debug(f"{username}, has {len(commits)} commits")
            
    except GithubException as e:
        logger.error(f"GitHub API Error: {e}")


if __name__ == '__main__':
    asyncio.run(get_user_commits_in_repo('berkingurcan', 'https://github.com/UmstadAI/zkAppUmstad'))
