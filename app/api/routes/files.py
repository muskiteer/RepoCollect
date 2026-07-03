import os
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@router.post("/{project_dataset}/upload")
async def upload_files(
    project_dataset: str,
    files: List[UploadFile] = File(...),
):
    """
    Upload files to a project's data directory for ingestion.
    Supports PDF, Markdown, and Text files.
    """
    ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt"}
    
    dest_dir = DATA_DIR / project_dataset
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    saved = []
    
    for file in files:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.warning("Skipping unsupported file: %s", file.filename)
            continue
            
        # Sanitize filename
        safe_name = file.filename.replace("/", "_").replace("\\", "_")
        dest_path = dest_dir / safe_name
        
        content = await file.read()
        dest_path.write_bytes(content)
        saved.append(safe_name)
        logger.info("Saved file: %s (%d bytes)", dest_path, len(content))
    
    return {
        "uploaded": len(saved),
        "files": saved,
        "directory": str(dest_dir),
    }
