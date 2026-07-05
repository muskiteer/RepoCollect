"""
Document Ingestion Module
-------------------------
Ingests local documents and converts them into DataItem objects
ready for Cognee ingestion.

Supported formats:
    - PDF
    - Markdown (.md)
    - Text (.txt)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import logging

# pyrefly: ignore [missing-import]
from pypdf import PdfReader

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
    A single unit of content ready to be fed into Cognee.
    """

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        preview = self.content[:80].replace("\n", " ")
        return (
            f"DataItem(type={self.metadata.get('type')!r}, "
            f"path={self.metadata.get('path')!r}, "
            f"preview={preview!r})"
        )


# ---------------------------------------------------------------------------
# Document Ingestor
# ---------------------------------------------------------------------------


class DocumentIngestor:
    """
    Ingest local documents.

    Parameters
    ----------
    root:
        Directory containing files to ingest.
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".md",
        ".txt",
    }

    IGNORE_DIRS = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
    }

    IGNORE_FILES = {
        ".DS_Store",
    }

    def __init__(self, root: str):
        self.root = Path(root)

    # ------------------------------------------------------------------
    # Public Entry Point
    # ------------------------------------------------------------------

    async def ingest_all(self) -> list[DataItem]:
        """
        Walk the directory recursively and ingest every supported document.
        """

        logger.info(
            "[ingest_all] Starting document ingestion from %s",
            self.root,
        )

        items = await self.ingest_directory()

        logger.info(
            "[ingest_all] Finished. Collected %d documents.",
            len(items),
        )

        return items

    # ------------------------------------------------------------------
    # Directory ingestion
    # ------------------------------------------------------------------

    async def ingest_directory(self) -> list[DataItem]:

        items: list[DataItem] = []

        for file in self.root.rglob("*"):

            if not file.is_file():
                continue

            if not self.should_ingest_file(file):
                continue

            item = await self.ingest_file(file)

            if item:
                items.append(item)

        return items

    # ------------------------------------------------------------------
    # Individual file ingestion
    # ------------------------------------------------------------------

    async def ingest_file(self, file: Path) -> DataItem | None:

        logger.info("[ingest_file] %s", file)

        suffix = file.suffix.lower()

        try:

            if suffix == ".pdf":
                content = self.parse_pdf(file)

            elif suffix == ".md":
                content = self.parse_markdown(file)

            elif suffix == ".txt":
                content = self.parse_text(file)

            else:
                return None

            return DataItem(
                content=content,
                metadata={
                    "type": "document",
                    "source": "upload",
                    "filename": file.name,
                    "path": str(file.relative_to(self.root)),
                    "extension": suffix,
                    "size": file.stat().st_size,
                    "modified_at": file.stat().st_mtime,
                },
            )

        except Exception as exc:
            logger.exception(
                "[ingest_file] Failed to ingest %s: %s",
                file,
                exc,
            )
            return None

    # ------------------------------------------------------------------
    # Parsers
    # ------------------------------------------------------------------

    def parse_pdf(self, file: Path) -> str:

        reader = PdfReader(file)

        pages = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n\n".join(pages)

    def parse_markdown(self, file: Path) -> str:

        return file.read_text(
            encoding="utf-8",
            errors="replace",
        )

    def parse_text(self, file: Path) -> str:

        return file.read_text(
            encoding="utf-8",
            errors="replace",
        )

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def should_ingest_file(self, file: Path) -> bool:

        if file.name in self.IGNORE_FILES:
            return False

        if file.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False

        relative = file.relative_to(self.root)

        for part in relative.parts:
            if part in self.IGNORE_DIRS:
                return False

        return True