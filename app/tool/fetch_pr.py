"""
GitHub PR Fetcher Tool
----------------------
Fetches a single GitHub pull request by number and returns its content
as structured data for the chat pipeline.
"""

import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def fetch_github_pr(
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    token: str,
) -> Dict[str, Any]:
    """
    Fetch a single GitHub PR by number including review comments.

    Returns a dict with: number, title, body, state, author, labels,
    base/head branches, merged status, review comments, and a pre-formatted
    markdown string.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Fetch the PR
        res = await client.get(url, headers=headers)

        if res.status_code == 404:
            return {"exists": False}

        res.raise_for_status()
        pr = res.json()

        # Fetch review comments
        reviews_text = ""
        reviews_url = f"{url}/reviews"
        rres = await client.get(reviews_url, headers=headers, params={"per_page": 30}, timeout=15.0)
        if rres.status_code == 200:
            reviews = rres.json()
            review_parts = []
            for r in reviews:
                author = r.get("user", {}).get("login", "unknown")
                state = r.get("state", "")
                body = (r.get("body") or "").strip()
                if body:
                    review_parts.append(f"**@{author}** ({state}):\n{body}")
            reviews_text = "\n\n---\n\n".join(review_parts)

        # Fetch regular comments (conversation)
        comments_text = ""
        comments_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_number}/comments"
        cres = await client.get(comments_url, headers=headers, params={"per_page": 30}, timeout=15.0)
        if cres.status_code == 200:
            comments = cres.json()
            comment_parts = []
            for c in comments:
                author = c.get("user", {}).get("login", "unknown")
                body = (c.get("body") or "").strip()
                if body:
                    comment_parts.append(f"**@{author}:**\n{body}")
            comments_text = "\n\n---\n\n".join(comment_parts)

        # Build markdown summary
        labels = ", ".join(l["name"] for l in pr.get("labels", []))
        body = pr.get("body", "") or ""
        merged = pr.get("merged", False)
        base_branch = pr.get("base", {}).get("ref", "?")
        head_branch = pr.get("head", {}).get("ref", "?")

        state_str = "merged" if merged else pr["state"]

        markdown = f"""# PR #{pr['number']}: {pr['title']}

**State:** {state_str} | **Author:** @{pr['user']['login']} | **Labels:** {labels or 'none'}
**Branch:** `{head_branch}` → `{base_branch}` | **Merged:** {'Yes' if merged else 'No'}
**Created:** {pr['created_at']} | **Changed files:** {pr.get('changed_files', '?')} | **+{pr.get('additions', '?')} / -{pr.get('deletions', '?')}**
**URL:** {pr['html_url']}

---

{body}
"""
        if reviews_text:
            markdown += f"\n\n## Reviews\n\n{reviews_text}"
        if comments_text:
            markdown += f"\n\n## Comments\n\n{comments_text}"

        logger.info(
            "Fetched PR #%d from %s/%s (%s)",
            pr_number, repo_owner, repo_name, state_str,
        )

        return {
            "number": pr["number"],
            "title": pr["title"],
            "body": body,
            "state": state_str,
            "author": pr["user"]["login"],
            "labels": labels,
            "base_branch": base_branch,
            "head_branch": head_branch,
            "merged": merged,
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "changed_files": pr.get("changed_files", 0),
            "created_at": pr["created_at"],
            "url": pr["html_url"],
            "markdown": markdown,
        }
