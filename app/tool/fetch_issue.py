"""
GitHub Issue Fetcher Tool
-------------------------
Fetches a single GitHub issue by number and returns its content
as structured data for the chat pipeline.
"""

import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


async def fetch_github_issue(
    repo_owner: str,
    repo_name: str,
    issue_number: int,
    token: str,
) -> Dict[str, Any]:
    """
    Fetch a single GitHub issue by number.
    
    Returns a dict with: number, title, body, state, author, labels, 
    comments_count, created_at, url, and a pre-formatted markdown string.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient() as client:
        # Fetch the issue
        res = await client.get(url, headers=headers, timeout=15.0)

        if res.status_code == 404:
            return {"exists": False}

        res.raise_for_status()
        issue = res.json()

        # Fetch comments
        comments_text = ""
        if issue.get("comments", 0) > 0:
            comments_url = f"{url}/comments"
            cres = await client.get(comments_url, headers=headers, params={"per_page": 30}, timeout=15.0)
            if cres.status_code == 200:
                comments = cres.json()
                comment_parts = []
                for c in comments:
                    author = c.get("user", {}).get("login", "unknown")
                    body = c.get("body", "").strip()
                    if body:
                        comment_parts.append(f"**@{author}:**\n{body}")
                comments_text = "\n\n---\n\n".join(comment_parts)

        # Build markdown summary
        labels = ", ".join(l["name"] for l in issue.get("labels", []))
        body = issue.get("body", "") or ""

        markdown = f"""# Issue #{issue['number']}: {issue['title']}

**State:** {issue['state']} | **Author:** @{issue['user']['login']} | **Labels:** {labels or 'none'}
**Created:** {issue['created_at']} | **Comments:** {issue.get('comments', 0)}
**URL:** {issue['html_url']}

---

{body}
"""
        if comments_text:
            markdown += f"\n\n## Comments\n\n{comments_text}"

        logger.info(
            "Fetched issue #%d from %s/%s (%s)",
            issue_number, repo_owner, repo_name, issue["state"],
        )

        return {
            "number": issue["number"],
            "title": issue["title"],
            "body": body,
            "state": issue["state"],
            "author": issue["user"]["login"],
            "labels": labels,
            "comments_count": issue.get("comments", 0),
            "created_at": issue["created_at"],
            "url": issue["html_url"],
            "markdown": markdown,
        }
