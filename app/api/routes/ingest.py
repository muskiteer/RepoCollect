# import os

# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel

# from ingest.github.github import GitHubIngestor
# from ingest.notion.notion import NotionIngestor
# from ingest.discord.discord import DiscordIngestor

# router = APIRouter()


# # ---------------------------------------------------------------------------
# # Request / Response schemas
# # ---------------------------------------------------------------------------

# class GithubIngestRequest(BaseModel):
#     owner: str
#     repo: str


# class GithubIngestResponse(BaseModel):
#     message: str
#     total_items: int
#     repo: str


# class NotionIngestResponse(BaseModel):
#     message: str
#     total_items: int


# class DiscordIngestRequest(BaseModel):
#     allowed_guilds: list[str] = []


# class DiscordIngestResponse(BaseModel):
#     message: str
#     total_items: int


# # ---------------------------------------------------------------------------
# # Health
# # ---------------------------------------------------------------------------

# @router.get("/health", tags=["Health"])
# async def health() -> dict:
#     return {"status": "ok"}


# # ---------------------------------------------------------------------------
# # GitHub ingestion
# # ---------------------------------------------------------------------------

# @router.post("/ingest/github", response_model=GithubIngestResponse, tags=["Ingestion"])
# async def ingest_github(body: GithubIngestRequest) -> GithubIngestResponse:
#     """
#     Ingest a GitHub repository using the PAT stored in .env.
#     """
#     github_pat = os.getenv("GITHUB_PAT_TOKEN")

#     if not github_pat:
#         raise HTTPException(
#             status_code=500,
#             detail="GITHUB_PAT_TOKEN is not configured.",
#         )

#     try:
#         ingestor = GitHubIngestor(
#             owner=body.owner,
#             repo=body.repo,
#             pat=github_pat,
#         )
#         items = await ingestor.ingest_all()

#         # TODO: feed `items` into cognee here

#         return GithubIngestResponse(
#             message="Ingestion complete (placeholder — cognee call pending)",
#             total_items=len(items),
#             repo=f"{body.owner}/{body.repo}",
#         )

#     except Exception as exc:
#         detail = str(exc) or f"{type(exc).__name__} (no message)"
#         raise HTTPException(status_code=500, detail=detail) from exc


# # ---------------------------------------------------------------------------
# # Notion ingestion
# # ---------------------------------------------------------------------------

# @router.post("/ingest/notion", response_model=NotionIngestResponse, tags=["Ingestion"])
# async def ingest_notion() -> NotionIngestResponse:
#     """
#     Ingest all accessible pages from the Notion workspace.
#     Token is read from NOTION_TOKEN in .env — no body required.
#     """
#     notion_token = os.getenv("NOTION_TOKEN")

#     if not notion_token:
#         raise HTTPException(
#             status_code=500,
#             detail="NOTION_TOKEN is not configured in .env.",
#         )

#     try:
#         ingestor = NotionIngestor(token=notion_token)
#         items = await ingestor.ingest_all()

#         # TODO: feed `items` into cognee here

#         return NotionIngestResponse(
#             message="Notion ingestion complete (placeholder — cognee call pending)",
#             total_items=len(items),
#         )

#     except Exception as exc:
#         detail = str(exc) or f"{type(exc).__name__} (no message)"
#         raise HTTPException(status_code=500, detail=detail) from exc


# # ---------------------------------------------------------------------------
# # Discord ingestion
# # ---------------------------------------------------------------------------

# @router.post("/ingest/discord", response_model=DiscordIngestResponse, tags=["Ingestion"])
# async def ingest_discord(body: DiscordIngestRequest) -> DiscordIngestResponse:
#     """
#     Ingest Discord guilds, channels, threads, and messages.
#     Token is read from DISCORD_BOT_TOKEN in .env.
#     Optionally pass `allowed_guilds` (list of guild IDs) to restrict to specific servers.
#     """
#     discord_token = os.getenv("DISCORD_BOT_TOKEN")

#     if not discord_token:
#         raise HTTPException(
#             status_code=500,
#             detail="DISCORD_BOT_TOKEN is not configured in .env.",
#         )

#     try:
#         ingestor = DiscordIngestor(
#             token=discord_token,
#             allowed_guilds=body.allowed_guilds
#         )
#         items = await ingestor.ingest_all()

#         # TODO: feed `items` into cognee here

#         return DiscordIngestResponse(
#             message="Discord ingestion complete (placeholder — cognee call pending)",
#             total_items=len(items),
#         )

#     except Exception as exc:
#         detail = str(exc) or f"{type(exc).__name__} (no message)"
#         raise HTTPException(status_code=500, detail=detail) from exc


from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health() -> dict:
    return {"status": "ok"}