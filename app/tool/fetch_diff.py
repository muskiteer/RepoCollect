"""
GitHub PR Diff Fetcher Tool
---------------------------
Fetches the file-level diff of a GitHub pull request.
Returns structured data with per-file changes and a unified diff summary.
"""

import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def fetch_github_diff(
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    token: str,
) -> Dict[str, Any]:
    """
    Fetch the diff of a GitHub PR.

    Returns:
        A dict with:
          - exists (bool)       : False if 404
          - pr_title (str)
          - files (list)        : per-file change summary
          - diff_markdown (str) : formatted summary for LLM
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"

    async with httpx.AsyncClient(timeout=20.0) as client:
        # Check PR exists first
        pr_res = await client.get(f"{base}/pulls/{pr_number}", headers=headers)

        if pr_res.status_code == 404:
            return {"exists": False}

        pr_res.raise_for_status()
        pr = pr_res.json()

        # Fetch changed files
        files_res = await client.get(
            f"{base}/pulls/{pr_number}/files",
            headers=headers,
            params={"per_page": 100},
        )
        files_res.raise_for_status()
        files = files_res.json()

    # Build per-file summary
    file_lines = []
    for f in files:
        status = f.get("status", "modified")
        filename = f.get("filename", "")
        additions = f.get("additions", 0)
        deletions = f.get("deletions", 0)
        patch = f.get("patch", "")  # actual unified diff

        icon = {"added": "➕", "removed": "❌", "renamed": "🔀", "modified": "✏️"}.get(status, "✏️")
        file_lines.append({
            "filename": filename,
            "status": status,
            "additions": additions,
            "deletions": deletions,
            "patch": patch,
        })

        file_lines[-1]["summary_line"] = (
            f"{icon} `{filename}` — {status} | +{additions} / -{deletions}"
        )

    total_additions = sum(f["additions"] for f in file_lines)
    total_deletions = sum(f["deletions"] for f in file_lines)

    # Build a markdown block for the LLM
    files_overview = "\n".join(f["summary_line"] for f in file_lines)

    # Include patches for files (limit to avoid huge prompts — first 10 files)
    patch_sections = []
    for f in file_lines[:10]:
        if f["patch"]:
            patch_sections.append(
                f"### `{f['filename']}` ({f['status']})\n```diff\n{f['patch']}\n```"
            )

    patches_md = "\n\n".join(patch_sections) if patch_sections else "_No patch data available._"

    diff_markdown = f"""# PR #{pr['number']} Diff: {pr['title']}

**Author:** @{pr['user']['login']} | **State:** {pr['state']} | **Merged:** {'Yes' if pr.get('merged') else 'No'}
**Total:** {len(file_lines)} file(s) changed | +{total_additions} additions / -{total_deletions} deletions
**URL:** {pr['html_url']}

## Files Changed

{files_overview}

## Patches

{patches_md}
"""

    logger.info(
        "Fetched diff for PR #%d from %s/%s — %d files",
        pr_number, repo_owner, repo_name, len(file_lines),
    )

    return {
        "exists": True,
        "pr_title": pr["title"],
        "pr_number": pr["number"],
        "files": file_lines,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "diff_markdown": diff_markdown,
    }
