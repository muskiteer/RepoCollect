import asyncio
import hashlib
import logging
import os

from pydantic import BaseModel

from ingest.github.github import GitHubIngestor
from ingest.notion.notion import NotionIngestor
from ingest.discord.discord import DiscordIngestor

from utils.remember import add_to_cognee, run_cognify

logger = logging.getLogger(__name__)

DATASET = "test"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class IngestAllRequest(BaseModel):
    github_owner: str
    github_repo: str
    discord_allowed_guilds: list[str] = []


class IngestAllResponse(BaseModel):
    github_total: int
    notion_total: int
    discord_total: int
    staged_total: int
    duplicates_skipped: int
    errors: dict[str, str]


# ---------------------------------------------------------------------------
# Step 1 — Stage
# ---------------------------------------------------------------------------

async def stage_items(items: list) -> tuple[int, int, dict[str, str]]:
    """
    Deduplicates by content hash, then calls cognee.add() for each unique item.

    This does NOT trigger any LLM/embedding work — it just buffers content.

    Returns:
        staged:   number of items successfully staged
        skipped:  duplicates dropped
        errors:   map of item index → error string
    """
    logger.info("[stage_items] Deduplicating %d item(s) …", len(items))

    seen: set[str] = set()
    unique: list = []

    empty_skipped = 0
    for item in items:
        content = item.content if hasattr(item, "content") else str(item)

        # 1. Drop empty documents
        content = content.strip()
        if not content:
            empty_skipped += 1
            continue

        # 2. Normalize whitespace before hashing so "Hello\n\n" == "Hello"
        normalized = " ".join(content.split())
        h = hashlib.sha256(normalized.encode()).hexdigest()

        if h in seen:
            continue
        seen.add(h)
        unique.append(item)

    if empty_skipped:
        logger.info("[stage_items] Dropped %d empty item(s) before dedup", empty_skipped)

    skipped = len(items) - len(unique)
    logger.info(
        "[stage_items] %d unique item(s) to stage, %d duplicate(s) dropped",
        len(unique), skipped,
    )

    staged = 0
    errors: dict[str, str] = {}

    for i, item in enumerate(unique):
        content = item.content if hasattr(item, "content") else str(item)
        try:
            await add_to_cognee(content, dataset=DATASET)
            staged += 1
            logger.debug("[stage_items] Staged %d/%d", staged, len(unique))
        except Exception as exc:
            errors[f"stage_{i}"] = f"{type(exc).__name__}: {exc}"
            logger.warning(
                "[stage_items] Item %d/%d failed to stage — %s: %s",
                i + 1, len(unique), type(exc).__name__, exc,
            )

    logger.info(
        "[stage_items] Done — staged=%d skipped=%d errors=%d",
        staged, skipped, len(errors),
    )
    return staged, skipped, errors


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

async def handle_ingest_all(body: IngestAllRequest) -> IngestAllResponse:
    github_pat    = os.getenv("GITHUB_PAT_TOKEN")
    notion_token  = os.getenv("NOTION_TOKEN")
    discord_token = os.getenv("DISCORD_BOT_TOKEN")

    logger.info(
        "[handle_ingest_all] Starting — repo=%s/%s | discord_guilds=%s | dataset=%r",
        body.github_owner, body.github_repo,
        body.discord_allowed_guilds or "all",
        DATASET,
    )

    errors: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Step 1 — Fetch from all three sources concurrently (no LLM yet)
    # ------------------------------------------------------------------

    async def run_github():
        if not github_pat:
            raise ValueError("GITHUB_PAT_TOKEN is not configured.")
        logger.info("[handle_ingest_all] → GitHub: %s/%s", body.github_owner, body.github_repo)
        items = await GitHubIngestor(
            owner=body.github_owner,
            repo=body.github_repo,
            pat=github_pat,
        ).ingest_all()
        logger.info("[handle_ingest_all] ✓ GitHub: %d items", len(items))
        return items

    async def run_notion():
        if not notion_token:
            raise ValueError("NOTION_TOKEN is not configured.")
        logger.info("[handle_ingest_all] → Notion workspace")
        items = await NotionIngestor(token=notion_token).ingest_all()
        logger.info("[handle_ingest_all] ✓ Notion: %d items", len(items))
        return items

    async def run_discord():
        if not discord_token:
            raise ValueError("DISCORD_BOT_TOKEN is not configured.")
        logger.info("[handle_ingest_all] → Discord (guilds=%s)", body.discord_allowed_guilds or "all")
        items = await DiscordIngestor(
            token=discord_token,
            allowed_guilds=body.discord_allowed_guilds,
        ).ingest_all()
        logger.info("[handle_ingest_all] ✓ Discord: %d items", len(items))
        return items

    ingest_results = await asyncio.gather(
        run_github(),
        run_notion(),
        run_discord(),
        return_exceptions=True,
    )

    def extract(result, source: str):
        if isinstance(result, BaseException):
            logger.error(
                "[handle_ingest_all] ✗ %s failed — %s: %s",
                source, type(result).__name__, result,
            )
            return [], f"{type(result).__name__}: {result}"
        return result, None

    github_items,  github_err  = extract(ingest_results[0], "github")
    notion_items,  notion_err  = extract(ingest_results[1], "notion")
    discord_items, discord_err = extract(ingest_results[2], "discord")

    for k, v in {"github": github_err, "notion": notion_err, "discord": discord_err}.items():
        if v is not None:
            errors[k] = v

    all_items = github_items + notion_items + discord_items
    logger.info(
        "[handle_ingest_all] Fetch complete — github=%d notion=%d discord=%d total=%d",
        len(github_items), len(notion_items), len(discord_items), len(all_items),
    )

    # ------------------------------------------------------------------
    # Step 2 — Deduplicate and stage ALL items into cognee.
    #           No LLM work happens here — just buffering.
    #
    #   GitHub ─┐
    #   Notion ─┼─▶  add() × N unique items  ─▶  cognee buffer
    #   Discord ─┘
    # ------------------------------------------------------------------

    staged, skipped, stage_errors = await stage_items(all_items)
    errors.update(stage_errors)

    # ------------------------------------------------------------------
    # Step 3 — ONE cognify() call processes everything in the buffer.
    #
    #   cognee buffer  ─▶  cognify()  ─▶  Knowledge Graph
    #
    # This is the single point where embeddings and graph extraction run.
    # ------------------------------------------------------------------

    logger.info(
        "[handle_ingest_all] Staging complete (%d unique). "
        "Starting ONE cognify() pass on dataset=%r …",
        staged, DATASET,
    )

    try:
        await run_cognify(dataset=DATASET)
        logger.info("[handle_ingest_all] ✓ cognify() complete")
    except Exception as exc:
        logger.error(
            "[handle_ingest_all] ✗ cognify() failed — %s: %s",
            type(exc).__name__, exc,
        )
        errors["cognify"] = f"{type(exc).__name__}: {exc}"

    logger.info(
        "[handle_ingest_all] All done — staged=%d skipped=%d errors=%s",
        staged, skipped, list(errors.keys()) or "none",
    )

    return IngestAllResponse(
        github_total=len(github_items),
        notion_total=len(notion_items),
        discord_total=len(discord_items),
        staged_total=staged,
        duplicates_skipped=skipped,
        errors=errors,
    )