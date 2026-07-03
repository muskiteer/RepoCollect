"""
GitHub Ingestion Module
-----------------------
Ingests content from a GitHub repository via the GitHub REST API using a
Personal Access Token (PAT) and converts everything into DataItem objects
ready for cognee ingestion.

Planned ingestion targets:
    - Repository files (code, README, markdown docs)
    - Issues + issue comments
    - Pull Requests + PR review comments
    - Discussions
    - Releases
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import logging

import httpx

from internal.json_to_markdown import json_to_markdown

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class DataItem:
    """
    A single unit of content ready to be fed into cognee.

    Attributes
    ----------
    content:
        Markdown-formatted string representing the GitHub artifact.
    metadata:
        Structured dictionary describing the artifact (type, repo, author,
        labels, URL, timestamps, etc.).
    """

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        preview = self.content[:80].replace("\n", " ")
        return (
            f"DataItem(type={self.metadata.get('type')!r}, "
            f"repo={self.metadata.get('repo')!r}, "
            f"preview={preview!r})"
        )


# ---------------------------------------------------------------------------
# GitHub Ingestor (placeholder)
# ---------------------------------------------------------------------------

class GitHubIngestor:
    """
    Fetches and converts GitHub repository content into DataItem objects.

    Parameters
    ----------
    owner:
        GitHub username or organisation that owns the repository.
    repo:
        Repository name.
    pat:
        Personal Access Token with at least `repo` and `read:discussion`
        scopes.
    """

    def __init__(self, owner: str, repo: str, pat: str, since: str | None = None) -> None:
        self.owner = owner
        self.repo = repo
        self.pat = pat
        self.since = since
        self.client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {pat}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    async def ingest_all(self) -> list[DataItem]:
        """
        Run every ingestion method and return the combined list of DataItems.
        """
        logger.info("[ingest_all] Starting full ingestion for %s/%s", self.owner, self.repo)
        items: list[DataItem] = []

        try:
            items += await self.ingest_files()
            items += await self.ingest_issues()
            items += await self.ingest_pull_requests()
            items += await self.ingest_discussions()
            items += await self.ingest_releases()
        finally:
            await self.client.aclose()
            logger.info("[ingest_all] HTTP client closed.")

        logger.info("[ingest_all] Done. Total items collected: %d", len(items))
        return items

    # ------------------------------------------------------------------
    # Individual ingestion methods (stubs)
    # ------------------------------------------------------------------



    async def ingest_files(self) -> list[DataItem]:
        """
        Fetch the repository tree, filter for important files, fetch their contents,
        and return them as DataItems.
        """
        logger.info("[ingest_files] Fetching repository tree for %s/%s ...", self.owner, self.repo)
        import base64
        from pathlib import Path

        # High-value documentation
        DOC_FILES = {
            "README.md",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
            "ARCHITECTURE.md",
            "LICENSE",
        }

        DOC_DIRS = {
            "docs",
            "adr",
            ".github",
        }

        # High-value code directories
        IMPORTANT_CODE_DIRS = {
            "src/api",
            "src/controllers",
            "src/services",
            "src/routes",
            "app",
            "backend",
            "server",
        }

        # Ignore completely
        IGNORE_DIRS = {
            ".git",
            ".github/workflows",
            "node_modules",
            "dist",
            "build",
            "target",
            "vendor",
            ".next",
            ".venv",
            "venv",
            "__pycache__",
            "coverage",
            ".idea",
            ".vscode",
        }

        IGNORE_EXTENSIONS = {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".ico",
            ".pdf",
            ".zip",
            ".gz",
            ".tar",
            ".exe",
            ".dll",
            ".so",
            ".class",
        }

        IGNORE_FILES = {
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
        }

        def should_ingest_file(path: str, include_code: bool = False) -> bool:
            path = path.strip("/")
            p = Path(path)

            # Ignore directories
            for ignored in IGNORE_DIRS:
                if path.startswith(ignored):
                    return False

            # Ignore binary extensions
            if p.suffix.lower() in IGNORE_EXTENSIONS:
                return False

            # Ignore lock files
            if p.name in IGNORE_FILES:
                return False

            # Always include markdown
            if p.suffix.lower() == ".md":
                return True

            # Important root docs
            if p.name in DOC_FILES:
                return True

            # Documentation folders
            for directory in DOC_DIRS:
                if path.startswith(directory):
                    return True

            if not include_code:
                return False

            # Important code folders
            for directory in IMPORTANT_CODE_DIRS:
                if path.startswith(directory):
                    return True

            # Important config files
            if p.name in {
                "Dockerfile",
                "docker-compose.yml",
                "docker-compose.yaml",
                "go.mod",
                "Cargo.toml",
                "pyproject.toml",
                "requirements.txt",
                "package.json",
            }:
                return True

            return False

        items = []

        # Fetch repository tree
        response = await self.client.get(
            f"/repos/{self.owner}/{self.repo}/git/trees/HEAD",
            params={"recursive": 1},
        )
        response.raise_for_status()

        tree = response.json()["tree"]

        for entry in tree:
            if entry["type"] != "blob":
                continue

            path = entry["path"]

            # Skip source code, only keep important documentation
            if not should_ingest_file(path, include_code=False):
                continue

            logger.debug("[ingest_files] Fetching file: %s", path)

            file_response = await self.client.get(
                f"/repos/{self.owner}/{self.repo}/contents/{path}"
            )
            file_response.raise_for_status()

            file = file_response.json()

            if file.get("encoding") != "base64":
                continue

            try:
                content = base64.b64decode(file["content"]).decode(
                    "utf-8",
                    errors="replace",
                )
            except Exception:
                continue

            suffix = Path(path).suffix.lower()

            # Wrap source code in fenced blocks
            if suffix != ".md":
                language = suffix.lstrip(".")
                content = f"# {path}\n\n```{language}\n{content}\n```"

            items.append(
                DataItem(
                    content=content,
                    metadata={
                        "type": "file",
                        "repo": f"{self.owner}/{self.repo}",
                        "path": path,
                        "sha": file["sha"],
                        "size": file["size"],
                        "url": file["html_url"],
                    },
                )
            )

        logger.info("[ingest_files] Done. Collected %d file items.", len(items))
        return items

    async def ingest_issues(self) -> list[DataItem]:
        """
        Fetch all issues (100 per page) and convert each to Markdown.
        """
        logger.info("[ingest_issues] Starting issues ingestion ...")
        items = []
        page = 1

        while True:
            logger.info("[ingest_issues] Fetching page %d ...", page)
            params={
                "state": "all",
                "per_page": 100,
                "page": page,
            }
            if self.since:
                params["since"] = self.since
                
            response = await self.client.get(
                f"/repos/{self.owner}/{self.repo}/issues",
                params=params,
            )
            response.raise_for_status()

            issues = response.json()

            if not issues:
                break

            for issue in issues:
                # Skip pull requests
                if "pull_request" in issue:
                    continue

                items.append(
                    DataItem(
                        content=json_to_markdown(issue),
                        metadata={
                            "type": "issue",
                            "repo": f"{self.owner}/{self.repo}",
                            "number": issue["number"],
                            "author": issue["user"]["login"],
                            "state": issue["state"],
                            "labels": [label["name"] for label in issue.get("labels", [])],
                            "url": issue["html_url"],
                            "created_at": issue["created_at"],
                        },
                    )
                )

            logger.info("[ingest_issues] Page %d: +%d issues (total so far: %d)", page, len([i for i in issues if 'pull_request' not in i]), len(items))
            page += 1

        logger.info("[ingest_issues] Done. Collected %d issue items.", len(items))
        return items

    async def ingest_pull_requests(self) -> list[DataItem]:
        """
        Fetch all PRs + review comments and produce one DataItem per PR.

        TODO:
            1. GET /repos/{owner}/{repo}/pulls?state=all&per_page=100
            2. For each PR fetch GET /repos/{owner}/{repo}/pulls/{number}/comments
               and GET /repos/{owner}/{repo}/pulls/{number}/reviews
            3. Convert to markdown similar to issues, include diff URL
            4. metadata: type="pull_request", repo, number, author, state,
                         labels, base_branch, head_branch, url, created_at, merged_at
        """
        logger.info("[ingest_pull_requests] Starting PR ingestion ...")

        items = []
        page = 1

        while True:
            logger.info("[ingest_pull_requests] Fetching page %d ...", page)
            params={
                "state": "all",
                "per_page": 100,
                "page": page,
                "sort": "updated",
                "direction": "desc"
            }
            
            response = await self.client.get(
                f"/repos/{self.owner}/{self.repo}/pulls",
                params=params,
            )
            response.raise_for_status()

            prs = response.json()

            if not prs:
                break
                
            # If we are using `since`, we can stop paginating once we hit a PR older than `since`
            if self.since:
                oldest_in_page = prs[-1]["updated_at"]
                if oldest_in_page < self.since:
                    # Filter current page for PRs strictly >= since
                    prs = [pr for pr in prs if pr["updated_at"] >= self.since]
                    should_break = True
                else:
                    should_break = False
            else:
                should_break = False

            for pr in prs:
                items.append(
                    DataItem(
                        content=json_to_markdown(pr),
                        metadata={
                            "type": "pull_request",
                            "repo": f"{self.owner}/{self.repo}",
                            "number": pr["number"],
                            "author": pr["user"]["login"],
                            "state": pr["state"],
                            "labels": [label["name"] for label in pr.get("labels", [])],
                            "base_branch": pr["base"]["ref"],
                            "head_branch": pr["head"]["ref"],
                            "url": pr["html_url"],
                            "created_at": pr["created_at"],
                            "merged_at": pr["merged_at"],
                        },
                    )
                )

            logger.info("[ingest_pull_requests] Page %d: +%d PRs (total so far: %d)", page, len(prs), len(items))
            if should_break:
                logger.info("[ingest_pull_requests] Reached PRs older than 'since', stopping pagination.")
                break
            page += 1

        logger.info("[ingest_pull_requests] Done. Collected %d PR items.", len(items))
        return items

    async def ingest_discussions(self) -> list[DataItem]:
        """
        Fetch all repository discussions via GraphQL.
        """
        logger.info("[ingest_discussions] Starting discussions ingestion via GraphQL ...")
        items = []
        cursor = None

        query = """
        query($owner: String!, $repo: String!, $after: String) {
        repository(owner: $owner, name: $repo) {
            discussions(first: 100, after: $after) {
            pageInfo {
                hasNextPage
            endCursor
            }
            nodes {
                number
                title
                body
                createdAt
                url
                category {
                name
                }
                author {
                login
                }
            }
            }
        }
        }
        """

        while True:
            logger.info("[ingest_discussions] Fetching page (cursor=%s) ...", cursor)
            response = await self.client.post(
                "https://api.github.com/graphql",
                json={
                    "query": query,
                    "variables": {
                        "owner": self.owner,
                        "repo": self.repo,
                        "after": cursor,
                    },
                },
            )
            response.raise_for_status()

            discussions = response.json()["data"]["repository"]["discussions"]

            for discussion in discussions["nodes"]:
                items.append(
                    DataItem(
                        content=json_to_markdown(discussion),
                        metadata={
                            "type": "discussion",
                            "repo": f"{self.owner}/{self.repo}",
                            "number": discussion["number"],
                            "author": (
                                discussion["author"]["login"]
                                if discussion["author"] else None
                            ),
                            "category": discussion["category"]["name"],
                            "url": discussion["url"],
                            "created_at": discussion["createdAt"],
                        },
                    )
                )

            logger.info("[ingest_discussions] Fetched %d discussions so far.", len(items))

            if not discussions["pageInfo"]["hasNextPage"]:
                break

            cursor = discussions["pageInfo"]["endCursor"]

        logger.info("[ingest_discussions] Done. Collected %d discussion items.", len(items))
        return items

    async def ingest_releases(self) -> list[DataItem]:
        """
        Fetch all releases and convert release notes to DataItems.
        """
        logger.info("[ingest_releases] Starting releases ingestion ...")
        items = []
        page = 1

        while True:
            logger.info("[ingest_releases] Fetching page %d ...", page)
            response = await self.client.get(
                f"/repos/{self.owner}/{self.repo}/releases",
                params={
                    "per_page": 100,
                    "page": page,
                },
            )
            response.raise_for_status()

            releases = response.json()

            if not releases:
                break

            for release in releases:
                items.append(
                    DataItem(
                        content=release.get("body") or "",
                        metadata={
                            "type": "release",
                            "repo": f"{self.owner}/{self.repo}",
                            "tag": release["tag_name"],
                            "name": release["name"],
                            "author": release["author"]["login"] if release["author"] else None,
                            "url": release["html_url"],
                            "published_at": release["published_at"],
                            "is_prerelease": release["prerelease"],
                        },
                    )
                )

            logger.info("[ingest_releases] Page %d: +%d releases (total so far: %d)", page, len(releases), len(items))
            page += 1

        logger.info("[ingest_releases] Done. Collected %d release items.", len(items))
        return items
