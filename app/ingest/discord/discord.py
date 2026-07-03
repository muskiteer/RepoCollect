"""
Discord Ingestion Module
------------------------

Ingests content from Discord guilds (servers), channels, threads, and messages
using the Discord REST API (Bot Token).
Converts everything into DataItem objects ready for cognee ingestion.

Pipeline:
    Guilds
      ↓
    Channels & Threads
      ↓
    Messages & Attachments
      ↓
    DataItem (Markdown)

Environment variable required:
    DISCORD_BOT_TOKEN — your Discord bot token (e.g. MTAx...)
"""
from __future__ import annotations
import io
from pypdf import PdfReader
import logging
import os
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timezone, timedelta

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ---------------------------------------------------------------------------
# Discord Constants
# ---------------------------------------------------------------------------
GUILD_TEXT = 0
GUILD_VOICE = 2
GUILD_CATEGORY = 4
GUILD_ANNOUNCEMENT = 5
ANNOUNCEMENT_THREAD = 10
PUBLIC_THREAD = 11
PRIVATE_THREAD = 12
GUILD_STAGE_VOICE = 13
GUILD_FORUM = 15

# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------

@dataclass
class DataItem:
    """
    Markdown document ready for Cognee.
    """
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        preview = self.content[:80].replace("\n", " ")
        return (
            f"DataItem(type={self.metadata.get('type')!r}, "
            f"channel={self.metadata.get('channel_name')!r}, "
            f"author={self.metadata.get('author')!r}, "
            f"preview={preview!r})"
        )

# ---------------------------------------------------------------------------
# Discord Ingestor
# ---------------------------------------------------------------------------

class DiscordIngestor:
    """
    Fetches accessible channels, threads, and messages from Discord.
    """

    BASE_URL = "https://discord.com/api/v10"

    # Discord epoch: first second of 2015 in ms
    DISCORD_EPOCH = 1420070400000

    def __init__(self, token: str | None = None, allowed_guilds: list[str] | None = None, since: str | None = None) -> None:
        resolved_token = token or os.getenv("DISCORD_BOT_TOKEN")
        if not resolved_token:
            raise ValueError(
                "Discord bot token not found. Set DISCORD_BOT_TOKEN in your .env file "
                "or pass it explicitly to DiscordIngestor(token=...)."
            )

        self.allowed_guilds = allowed_guilds or []
        self.since = since
        self.since_snowflake = self._timestamp_to_snowflake(since) if since else None

        logger.info("[DiscordIngestor] Initialised (token present: %s)", bool(resolved_token))

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={
                "Authorization": f"Bot {resolved_token}",
                "Content-Type": "application/json",
            },
        )

    @staticmethod
    def _timestamp_to_snowflake(iso_ts: str) -> str:
        """Convert an ISO-8601 timestamp to a Discord snowflake ID."""
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        ms = int(dt.timestamp() * 1000)
        snowflake = (ms - DiscordIngestor.DISCORD_EPOCH) << 22
        return str(snowflake)
    async def attachment_to_dataitem(
        self,
        attachment: dict,
        guild_name: str,
        channel_name: str,
        message_id: str,    
    ) -> DataItem | None:
        """
        Download an attachment and create a DataItem containing its contents.
        """
        if not self.should_ingest_attachment(attachment):
            logger.info("Skipping attachment %s due to filter", attachment.get("filename"))
            return None

        url = attachment["url"]
        filename = attachment["filename"]
        logger.info("Processing attachment %s from %s", filename, url)

        try:
            response = await self.client.get(url)
            response.raise_for_status()

            text = ""

            if filename.lower().endswith(".pdf"):
                reader = PdfReader(io.BytesIO(response.content))
                text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )
                logger.info("Extracted %d chars from PDF %s", len(text), filename)

            else:
                try:
                    text = response.content.decode("utf-8")
                except UnicodeDecodeError:
                    text = ""
                logger.info("Extracted %d chars from text file %s", len(text), filename)

            if not text.strip():
                logger.info("Skipping attachment %s because extracted text is empty", filename)
                return None

            return DataItem(
                content=text,
                metadata={
                    "type": "discord_attachment",
                    "filename": filename,
                    "url": url,
                    "guild_name": guild_name,
                    "channel_name": channel_name,
                    "message_id": message_id,
                },
            )

        except Exception as e:
            logger.warning(
                "Failed to process attachment %s: %s",
                filename,
                e,
            )
            return None
    
    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------

    def should_ingest_guild(self, guild: dict) -> bool:
        """
        Guild filter:
        - Ignore test servers (could be by name or if not in allowed list)
        - Allow only configured guild IDs
        - Skip unavailable guilds
        """
        if guild.get("unavailable", False):
            return False
            
        if self.allowed_guilds and str(guild["id"]) not in self.allowed_guilds:
            return False
            
        return True

    def should_ingest_channel(self, channel: dict) -> bool:
        """
        Channel filter:
        - Skip non-text channels
        - Skip common noisy channels
        """
        if channel.get("type") in {GUILD_VOICE, GUILD_STAGE_VOICE, GUILD_CATEGORY}:
            return False

        name = channel.get("name", "").lower()

        IGNORE_CHANNELS = {
            "random",
            "off-topic",
            "memes",
            "music",
            "bot-spam",
            "spam",
            "logs",
            "logging",
            "welcome",
            "rules",    
        }

        if any(x in name for x in IGNORE_CHANNELS):
            return False
            
        return True

    def should_ingest_thread(self, thread: dict) -> bool:
        """
        Ingest all accessible threads.
        """
        return True

    def should_ingest_message(self, message: dict) -> bool:
        """
        Message filter:
        - Skip Discord system messages
        - Skip completely empty messages
        """
        # Skip Discord system messages (0=DEFAULT, 19=REPLY, 20=CHAT_INPUT_COMMAND)
        if message.get("type", 0) not in (0, 19, 20):
            return False

        # Skip completely empty messages
        if not message.get("content", "").strip() and not message.get("attachments"):
            return False

        return True

    def should_ingest_attachment(self, attachment: dict) -> bool:
        """
        Attachment filter:
        - Skip all files from discord
        """
        return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def ingest_all(self) -> list[DataItem]:
        """
        Main entrypoint.
        1. Fetch all guilds
        2. Fetch channels and threads for each guild
        3. Fetch messages for each valid channel/thread
        """
        logger.info("[ingest_all] Starting Discord ingestion ...")
        items: list[DataItem] = []

        try:
            guilds = await self.fetch_guilds()
            logger.info("[ingest_all] Found %d allowed guilds.", len(guilds))

            for guild in guilds:
                guild_id = guild["id"]
                guild_name = guild.get("name", "Unknown Guild")
                logger.info("[ingest_all] Processing guild: %s (%s)", guild_name, guild_id)
                
                channels_and_threads = await self.fetch_channels_and_threads(guild_id)
                logger.info("[ingest_all] Found %d valid channels/threads in %s.", len(channels_and_threads), guild_name)
                
                for channel in channels_and_threads:
                    channel_id = channel["id"]
                    channel_name = channel.get("name", "unknown")
                    
                    messages = await self.fetch_messages(channel_id)
                    logger.info("[ingest_all] Fetched %d valid messages from #%s", len(messages), channel_name)
                    
                    seen = set()
                    
                    for msg in messages:
                        content = msg.get("content", "").strip().lower()
                        
                        if content:
                            key = (
                                channel_id,
                                msg.get("author", {}).get("username"),
                                content,
                            )
                            if key in seen:
                                continue
                            seen.add(key)
                            
                        # Add message text if it's not empty
                        item = self.message_to_dataitem(
                            msg,
                            guild_name,
                            channel_name,
                        )
                        if item.content.strip():
                            items.append(item)

                        # Add attachments
                        for attachment in msg.get("attachments", []):
                            attachment_item = await self.attachment_to_dataitem(
                                attachment,
                                guild_name,
                                channel_name,
                                msg["id"],
                            )

                            if attachment_item:
                                items.append(attachment_item)
                        
        finally:
            await self.client.aclose()
            logger.info("[ingest_all] HTTP client closed.")

        logger.info("[ingest_all] Done. Total DataItems collected: %d", len(items))
        return items

    # ------------------------------------------------------------------
    # Fetching logic
    # ------------------------------------------------------------------

    async def fetch_guilds(self) -> list[dict]:
        """
        GET /users/@me/guilds
        """
        logger.info("[fetch_guilds] Fetching bot's guilds ...")
        results = []
        after = None
        
        while True:
            params = {"limit": 200}
            if after:
                params["after"] = after
                
            data = await self.request("GET", "/users/@me/guilds", params=params)
            if not data:
                break
                
            for guild in data:
                if self.should_ingest_guild(guild):
                    results.append(guild)
                    
            if len(data) < 200:
                break
            after = data[-1]["id"]
            
        return results

    async def fetch_channels_and_threads(self, guild_id: str) -> list[dict]:
        """
        GET /guilds/{guild_id}/channels
        GET /guilds/{guild_id}/threads/active
        """
        results = []
        
        # 1. Fetch normal channels
        channels = await self.request("GET", f"/guilds/{guild_id}/channels")
        for channel in channels:
            if self.should_ingest_channel(channel):
                results.append(channel)
                
        # 2. Fetch active threads
        threads_data = await self.request("GET", f"/guilds/{guild_id}/threads/active")
        threads = threads_data.get("threads", [])
        for thread in threads:
            if self.should_ingest_thread(thread):
                results.append(thread)
                
        return results

    async def fetch_messages(self, channel_id: str) -> list[dict]:
        """
        GET /channels/{channel_id}/messages
        Handles pagination backwards through time.
        """
        results = []
        before = None
        page = 0
        
        while True:
            page += 1
            params = {"limit": 100}
            if before:
                params["before"] = before
            # On the first page, use the since snowflake to skip old messages
            if self.since_snowflake and page == 1 and not before:
                params["after"] = self.since_snowflake
                
            data = await self.request("GET", f"/channels/{channel_id}/messages", params=params)
            
            # API might return error if no access
            if isinstance(data, dict) and data.get("code"):
                logger.warning("[fetch_messages] Error fetching messages for channel %s: %s", channel_id, data.get("message"))
                break
                
            if not data:
                break
                
            batch_count = 0
            for msg in data:
                if self.should_ingest_message(msg):
                    results.append(msg)
                    batch_count += 1
                    
            logger.debug("[fetch_messages] Channel %s Page %d: +%d valid messages", channel_id, page, batch_count)
            
            if len(data) < 100:
                break
            before = data[-1]["id"]
            
        return results

    # ------------------------------------------------------------------
    # Data Conversion
    # ------------------------------------------------------------------

    def message_to_dataitem(self, message: dict, guild_name: str, channel_name: str) -> DataItem:
        content = message.get("content", "").strip()
        author = message.get("author", {}).get("username", "Unknown")
        msg_id = message.get("id")
        created_at = message.get("timestamp")
                
        # Combine content
        full_content = content
        
            
        metadata = {
            "type": "discord_message",
            "id": msg_id,
            "guild_name": guild_name,
            "channel_name": channel_name,
            "author": author,
            "created_at": created_at,
        }
        
        return DataItem(content=full_content, metadata=metadata)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    async def request(self, method: str, url: str, **kwargs: Any) -> Any:
        """
        Shared HTTP wrapper.
        """
        logger.debug("[request] %s %s", method.upper(), url)
        response = await self.client.request(method, url, **kwargs)

        if response.status_code == 403:
            logger.warning("[request] 403 Forbidden on %s %s - missing permissions?", method.upper(), url)
            return {"code": 403, "message": "Forbidden"}
            
        if response.status_code != 200:
            logger.warning(
                "[request] %s %s → HTTP %d: %s",
                method.upper(), url, response.status_code, response.text[:300],
            )

        response.raise_for_status()
        return response.json()
