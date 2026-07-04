"""
GitHub Contributor Fetcher Tool
--------------------------------
Fetches contributor profiles and their activity (PRs, Issues, Commits)
for a given GitHub repository.

Usage patterns:
  /contributors          → list all contributors with stats
  @username              → full profile of that contributor
  @username <question>   → answer question about their work
"""

import httpx
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


async def fetch_all_contributors(
    repo_owner: str,
    repo_name: str,
    token: str,
) -> List[Dict[str, Any]]:
    """
    Fetch all contributors for a repo with their commit counts.
    Returns a list sorted by contributions descending.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contributors"

    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(url, headers=headers, params={"per_page": 100})
        res.raise_for_status()
        contributors = res.json()

    return [
        {
            "login": c["login"],
            "contributions": c["contributions"],
            "avatar_url": c.get("avatar_url", ""),
            "html_url": c.get("html_url", ""),
            "type": c.get("type", "User"),
        }
        for c in contributors
        if c.get("type") != "Bot"
    ]


async def fetch_contributor_profile(
    repo_owner: str,
    repo_name: str,
    username: str,
    token: str,
) -> Dict[str, Any]:
    """
    Fetch a full activity profile for a specific contributor:
    - Their authored PRs (merged + open)
    - Issues they opened
    - Commit count

    Returns {"exists": False} if the user has no activity in this repo.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    search_base = "https://api.github.com/search/issues"

    async with httpx.AsyncClient(timeout=20.0) as client:

        # 1. Commit count from contributors list
        contrib_res = await client.get(
            f"{base}/contributors",
            headers=headers,
            params={"per_page": 100},
        )
        commit_count = 0
        if contrib_res.status_code == 200:
            for c in contrib_res.json():
                if c.get("login", "").lower() == username.lower():
                    commit_count = c.get("contributions", 0)
                    break

        # 2. PRs authored by this user
        pr_res = await client.get(
            search_base,
            headers=headers,
            params={
                "q": f"repo:{repo_owner}/{repo_name} type:pr author:{username}",
                "per_page": 30,
                "sort": "created",
                "order": "desc",
            },
        )
        prs = pr_res.json().get("items", []) if pr_res.status_code == 200 else []

        # 3. Issues opened by this user
        issue_res = await client.get(
            search_base,
            headers=headers,
            params={
                "q": f"repo:{repo_owner}/{repo_name} type:issue author:{username}",
                "per_page": 30,
                "sort": "created",
                "order": "desc",
            },
        )
        issues = issue_res.json().get("items", []) if issue_res.status_code == 200 else []

        # 4. User profile info
        user_res = await client.get(
            f"https://api.github.com/users/{username}",
            headers=headers,
        )
        user_info = user_res.json() if user_res.status_code == 200 else {}

    # Check if user has any activity at all in this repo
    if commit_count == 0 and not prs and not issues:
        # Could be a valid user but not a contributor to THIS repo
        if user_res.status_code == 404:
            return {"exists": False, "reason": "user_not_found"}
        return {"exists": False, "reason": "no_activity"}

    # Build PR summary lines
    pr_lines = []
    for pr in prs[:15]:
        state = pr.get("state", "open")
        merged = pr.get("pull_request", {}).get("merged_at")
        status = "merged" if merged else state
        pr_lines.append(
            f"- [{status.upper()}] #{pr['number']}: {pr['title']} ({pr.get('created_at', '')[:10]})"
        )

    # Build issue summary lines
    issue_lines = []
    for iss in issues[:15]:
        state = iss.get("state", "open")
        issue_lines.append(
            f"- [{state.upper()}] #{iss['number']}: {iss['title']} ({iss.get('created_at', '')[:10]})"
        )

    # Build full markdown profile
    name = user_info.get("name") or username
    bio = user_info.get("bio") or ""
    company = user_info.get("company") or ""
    location = user_info.get("location") or ""
    public_repos = user_info.get("public_repos", "?")

    pr_section = "\n".join(pr_lines) if pr_lines else "_No pull requests found._"
    issue_section = "\n".join(issue_lines) if issue_lines else "_No issues found._"

    markdown = f"""# Contributor Profile: @{username}

**Name:** {name} | **Company:** {company or 'N/A'} | **Location:** {location or 'N/A'}
**Bio:** {bio or 'N/A'}
**GitHub:** https://github.com/{username} | **Public Repos:** {public_repos}

---

## Contributions to {repo_owner}/{repo_name}

| Metric | Count |
|--------|-------|
| Commits | {commit_count} |
| Pull Requests | {len(prs)} |
| Issues Opened | {len(issues)} |

## Pull Requests

{pr_section}

## Issues Opened

{issue_section}
"""

    logger.info(
        "Fetched contributor profile for @%s in %s/%s — %d commits, %d PRs, %d issues",
        username, repo_owner, repo_name, commit_count, len(prs), len(issues),
    )

    return {
        "exists": True,
        "username": username,
        "name": name,
        "commit_count": commit_count,
        "pr_count": len(prs),
        "issue_count": len(issues),
        "prs": prs,
        "issues": issues,
        "markdown": markdown,
    }


def format_contributors_list(contributors: List[Dict[str, Any]], repo_owner: str, repo_name: str) -> str:
    """Format the full contributor list as a markdown table."""
    if not contributors:
        return f"No contributors found for {repo_owner}/{repo_name}."

    rows = "\n".join(
        f"| {i+1} | @{c['login']} | {c['contributions']} |"
        for i, c in enumerate(contributors[:30])
    )
    return f"""# Contributors — {repo_owner}/{repo_name}

| # | Username | Commits |
|---|----------|---------|
{rows}

_Type `@username` to get a full profile of any contributor._
"""
