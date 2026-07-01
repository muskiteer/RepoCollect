import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def open_github_issue(repo_owner: str, repo_name: str, title: str, body: str, token: str) -> Dict[str, Any]:
    """
    Open a new issue on GitHub.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    payload = {
        "title": title,
        "body": body
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully opened issue #{data.get('number')} in {repo_owner}/{repo_name}")
        return data


