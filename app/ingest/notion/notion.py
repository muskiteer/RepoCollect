"""
Notion Ingestion Module
-----------------------

Ingests content from a Notion workspace using the Notion REST API and
converts everything into DataItem objects ready for cognee ingestion.

Pipeline:
    Search
      ↓
    Pages / Databases
      ↓
    Fetch Metadata
      ↓
    Fetch Blocks (recursive)
      ↓
    Markdown Conversion
      ↓
    DataItem

Environment variable required:
    NOTION_TOKEN  — your Notion integration token (secret_xxx...)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


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
            f"title={self.metadata.get('title')!r}, "
            f"preview={preview!r})"
        )


# ---------------------------------------------------------------------------
# Notion Ingestor
# ---------------------------------------------------------------------------

class NotionIngestor:
    """
    Fetches every accessible page from Notion and converts it into
    markdown DataItems.

    Token is read automatically from the NOTION_TOKEN env variable,
    or you can pass one explicitly via the ``token`` parameter.
    """

    BASE_URL = "https://api.notion.com/v1"

    def __init__(self, token: str | None = None, since: str | None = None) -> None:
        resolved_token = token or os.getenv("NOTION_TOKEN")
        if not resolved_token:
            raise ValueError(
                "Notion token not found. Set NOTION_TOKEN in your .env file "
                "or pass it explicitly to NotionIngestor(token=...)."
            )

        self.since = since
        logger.info("[NotionIngestor] Initialised (token present: %s, since=%s)", bool(resolved_token), since)

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {resolved_token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def ingest_all(self) -> list[DataItem]:
        """
        Main entrypoint.

        1. Search workspace for all pages & databases.
        2. Deduplicate by page id.
        3. Ingest every unique page.
        """
        logger.info("[ingest_all] Starting Notion workspace ingestion ...")
        items: list[DataItem] = []

        try:
            pages = await self.search_pages()
            logger.info("[ingest_all] Found %d objects from search.", len(pages))

            seen: set[str] = set()
            for page in pages:
                page_id = page["id"]
                if page_id in seen:
                    continue
                seen.add(page_id)

                item = await self.ingest_page(page)
                if item:
                    items.append(item)
                    logger.info(
                        "[ingest_all] Ingested page '%s' → total so far: %d",
                        item.metadata.get("title", page_id),
                        len(items),
                    )

        finally:
            await self.client.aclose()
            logger.info("[ingest_all] HTTP client closed.")

        logger.info("[ingest_all] Done. Total DataItems collected: %d", len(items))
        return items

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search_pages(self) -> list[dict]:
        """
        POST /search — handles pagination via start_cursor.
        Returns every page and database the integration can access.
        """
        logger.info("[search_pages] Searching workspace ...")
        results: list[dict] = []
        start_cursor: str | None = None
        page_num = 0

        while True:
            page_num += 1
            body: dict[str, Any] = {"page_size": 100}
            if start_cursor:
                body["start_cursor"] = start_cursor
            if self.since:
                body["filter"] = {
                    "timestamp": "last_edited_time",
                    "last_edited_time": {"after": self.since}
                }

            logger.info(
                "[search_pages] Fetching page %d (cursor=%s, since=%s) ...",
                page_num, start_cursor, self.since,
            )
            data = await self.request("POST", "/search", json=body)

            batch = data.get("results", [])
            results.extend(batch)
            logger.info(
                "[search_pages] Page %d: +%d objects (total so far: %d)",
                page_num, len(batch), len(results),
            )

            if not data.get("has_more"):
                break
            start_cursor = data.get("next_cursor")

        logger.info("[search_pages] Done. Total objects found: %d", len(results))
        return results

    # ------------------------------------------------------------------
    # Page
    # ------------------------------------------------------------------

    async def ingest_page(self, page: dict) -> DataItem | None:
        """
        Convert one Notion page or database into one DataItem.
        """
        page_id = page["id"]
        title = self.extract_title(page)
        logger.info("[ingest_page] Processing '%s' (id=%s)", title, page_id)

        try:
            blocks = await self.fetch_all_blocks(page_id)
            logger.info("[ingest_page] '%s' — %d blocks fetched.", title, len(blocks))
            content = self.blocks_to_markdown(blocks)
            metadata = self.build_metadata(page)
            return DataItem(content=content, metadata=metadata)

        except Exception as exc:
            logger.warning("[ingest_page] Skipping '%s' due to error: %s", title, exc)
            return None

    # ------------------------------------------------------------------
    # Blocks
    # ------------------------------------------------------------------

    async def fetch_all_blocks(self, block_id: str) -> list[dict]:
        """
        Recursively fetch every child block (handles pagination).
        """
        blocks: list[dict] = []
        children = await self.fetch_children(block_id)

        for block in children:
            blocks.append(block)
            if block.get("has_children"):
                nested = await self.fetch_all_blocks(block["id"])
                blocks.extend(nested)

        return blocks

    async def fetch_children(self, block_id: str) -> list[dict]:
        """
        GET /blocks/{id}/children — with pagination.
        """
        results: list[dict] = []
        start_cursor: str | None = None

        while True:
            params: dict[str, Any] = {"page_size": 100}
            if start_cursor:
                params["start_cursor"] = start_cursor

            data = await self.request(
                "GET", f"/blocks/{block_id}/children", params=params
            )
            results.extend(data.get("results", []))

            if not data.get("has_more"):
                break
            start_cursor = data.get("next_cursor")

        return results

    # ------------------------------------------------------------------
    # Markdown
    # ------------------------------------------------------------------

    def blocks_to_markdown(self, blocks: list[dict]) -> str:
        """
        Convert a flat list of blocks into a single markdown string.
        """
        lines: list[str] = []
        for block in blocks:
            rendered = self.render_block(block)
            if rendered:
                lines.append(rendered)
        return "\n".join(lines)

    def render_block(self, block: dict) -> str:
        """
        Dispatch to the correct renderer based on block type.
        """
        block_type: str = block.get("type", "unknown")
        renderer = {
            "paragraph":            self.render_paragraph,
            "heading_1":            self.render_heading_1,
            "heading_2":            self.render_heading_2,
            "heading_3":            self.render_heading_3,
            "bulleted_list_item":   self.render_bulleted_list_item,
            "numbered_list_item":   self.render_numbered_list_item,
            "to_do":                self.render_to_do,
            "toggle":               self.render_toggle,
            "quote":                self.render_quote,
            "callout":              self.render_callout,
            "divider":              self.render_divider,
            "code":                 self.render_code,
            "image":                self.render_image,
            "bookmark":             self.render_bookmark,
            "equation":             self.render_equation,
            "table":                self.render_table,
            "synced_block":         self.render_synced_block,
            "child_page":           self.render_child_page,
            "child_database":       self.render_child_database,
        }.get(block_type)

        if renderer:
            return renderer(block)
        return self.render_unknown(block)

    # ------------------------------------------------------------------
    # Individual block renderers
    # ------------------------------------------------------------------

    def render_paragraph(self, block: dict) -> str:
        return self.rich_text(block["paragraph"]["rich_text"])

    def render_heading_1(self, block: dict) -> str:
        return f"# {self.rich_text(block['heading_1']['rich_text'])}"

    def render_heading_2(self, block: dict) -> str:
        return f"## {self.rich_text(block['heading_2']['rich_text'])}"

    def render_heading_3(self, block: dict) -> str:
        return f"### {self.rich_text(block['heading_3']['rich_text'])}"

    def render_bulleted_list_item(self, block: dict) -> str:
        return f"- {self.rich_text(block['bulleted_list_item']['rich_text'])}"

    def render_numbered_list_item(self, block: dict) -> str:
        return f"1. {self.rich_text(block['numbered_list_item']['rich_text'])}"

    def render_to_do(self, block: dict) -> str:
        data = block["to_do"]
        checkbox = "[x]" if data.get("checked") else "[ ]"
        return f"- {checkbox} {self.rich_text(data['rich_text'])}"

    def render_toggle(self, block: dict) -> str:
        summary = self.rich_text(block["toggle"]["rich_text"])
        return f"<details><summary>{summary}</summary></details>"

    def render_quote(self, block: dict) -> str:
        text = self.rich_text(block["quote"]["rich_text"])
        return f"> {text}"

    def render_callout(self, block: dict) -> str:
        data = block["callout"]
        icon = data.get("icon", {})
        emoji = icon.get("emoji", "💡") if icon.get("type") == "emoji" else "💡"
        text = self.rich_text(data["rich_text"])
        return f"> {emoji} {text}"

    def render_divider(self, block: dict) -> str:
        return "---"

    def render_code(self, block: dict) -> str:
        data = block["code"]
        language = data.get("language", "").lower()
        code = self.rich_text(data["rich_text"])
        return f"```{language}\n{code}\n```"

    def render_image(self, block: dict) -> str:
        data = block["image"]
        img_type = data.get("type")
        if img_type == "external":
            url = data["external"]["url"]
        elif img_type == "file":
            url = data["file"]["url"]
        else:
            url = ""
        caption = self.rich_text(data.get("caption", []))
        alt = caption or "image"
        return f"![{alt}]({url})"

    def render_bookmark(self, block: dict) -> str:
        data = block["bookmark"]
        url = data.get("url", "")
        caption = self.rich_text(data.get("caption", []))
        label = caption or url
        return f"[{label}]({url})"

    def render_equation(self, block: dict) -> str:
        expr = block["equation"].get("expression", "")
        return f"$${expr}$$"

    def render_table(self, block: dict) -> str:
        # Table rows are child blocks fetched recursively via fetch_all_blocks.
        return "_[table]_"

    def render_synced_block(self, block: dict) -> str:
        # Content already captured via recursive fetch.
        return ""

    def render_child_page(self, block: dict) -> str:
        title = block.get("child_page", {}).get("title", "child page")
        return f"**[Child Page: {title}]**"

    def render_child_database(self, block: dict) -> str:
        title = block.get("child_database", {}).get("title", "child database")
        return f"**[Child Database: {title}]**"

    def render_unknown(self, block: dict) -> str:
        block_type = block.get("type", "unknown")
        logger.debug("[render_unknown] Unhandled block type: %s", block_type)
        return f"_[{block_type}]_"

    # ------------------------------------------------------------------
    # Rich Text
    # ------------------------------------------------------------------

    def rich_text(self, items: list[dict]) -> str:
        """
        Convert Notion rich_text array into a plain markdown string,
        preserving bold, italic, code, and strikethrough annotations.
        """
        parts: list[str] = []
        for item in items:
            text = item.get("plain_text", "")
            annotations = item.get("annotations", {})

            if annotations.get("code"):
                text = f"`{text}`"
            if annotations.get("bold"):
                text = f"**{text}**"
            if annotations.get("italic"):
                text = f"*{text}*"
            if annotations.get("strikethrough"):
                text = f"~~{text}~~"

            href = item.get("href")
            if href:
                text = f"[{text}]({href})"

            parts.append(text)

        return "".join(parts)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def build_metadata(self, page: dict) -> dict[str, Any]:
        """
        Build a metadata dictionary from a Notion page/database object.
        """
        object_type = page.get("object", "page")
        page_id = page["id"]
        title = self.extract_title(page)
        properties = page.get("properties", {})
        last_edited = page.get("last_edited_time", "")
        created_time = page.get("created_time", "")
        url = page.get("url", f"https://notion.so/{page_id.replace('-', '')}")
        parent = page.get("parent", {})
        parent_type = parent.get("type", "unknown")

        return {
            "type": object_type,
            "id": page_id,
            "title": title,
            "url": url,
            "created_at": created_time,
            "last_edited_at": last_edited,
            "parent_type": parent_type,
            "property_count": len(properties),
        }

    def extract_title(self, page: dict) -> str:
        """
        Extract the page title regardless of whether it's a page or database.
        """
        # Databases store title as a top-level list
        title_list = page.get("title")
        if isinstance(title_list, list):
            return self.rich_text(title_list) or "Untitled"

        # Pages store title inside properties
        properties = page.get("properties", {})
        for prop in properties.values():
            if prop.get("type") == "title":
                rt = prop.get("title", [])
                if rt:
                    return self.rich_text(rt)

        return "Untitled"

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> dict:
        """
        Shared HTTP wrapper.
        Logs every request, raises on HTTP errors, returns decoded JSON.
        """
        logger.debug("[request] %s %s", method.upper(), url)
        response = await self.client.request(method, url, **kwargs)

        if response.status_code != 200:
            logger.warning(
                "[request] %s %s → HTTP %d: %s",
                method.upper(), url, response.status_code, response.text[:300],
            )

        response.raise_for_status()
        return response.json()
