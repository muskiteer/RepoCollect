import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def leave_github_comment(repo_owner: str, repo_name: str, issue_number: int, body: str, token: str) -> Dict[str, Any]:
    """
    Leave a comment on a GitHub Issue or Pull Request.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    payload = {"body": body}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully posted comment on #{issue_number} in {repo_owner}/{repo_name}")
        return data
