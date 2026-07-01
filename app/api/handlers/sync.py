import asyncio
import logging
import sqlite3
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, BackgroundTasks
from pydantic import BaseModel
from ingest.github.github import GitHubIngestor
from ingest.notion.notion import NotionIngestor
from ingest.discord.discord import DiscordIngestor
from utils.remember import add_to_cognee, run_cognify
from api.handlers.ingest import stage_items

logger = logging.getLogger(__name__)

class SyncJobResponse(BaseModel):
    job_id: str
    message: str

class SyncStatusResponse(BaseModel):
    project_id: str
    status: str
    last_synced_at: str | None = None
    last_ingested_at: str | None = None
    active_job_id: str | None = None
    active_job_status: str | None = None
    items_synced: int = 0
    error: str | None = None

async def run_sync_job_background(project_id: str, job_id: str, is_initial: bool):
    import sqlite3
    from db import DB_PATH
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("UPDATE sync_jobs SET status = 'RUNNING', started_at = ? WHERE id = ?", (now, job_id))
        conn.commit()

        # Fetch project
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        project = cursor.fetchone()
        if not project:
            raise ValueError("Project not found")

        dataset = project["dataset"]
        github_owner = project["repo_owner"]
        github_repo = project["repo_name"]

        # Fetch tokens
        cursor.execute("SELECT * FROM project_sources WHERE project_id = ?", (project_id,))
        sources = cursor.fetchall()

        github_token = None
        notion_token = None
        discord_token = None

        for src in sources:
            if src["source_type"] == "github":
                github_token = src["token"]
            elif src["source_type"] == "notion":
                notion_token = src["token"]
            elif src["source_type"] == "discord":
                discord_token = src["token"]

        all_items = []

        if is_initial:
            if github_token:
                logger.info("Running GitHub ingestor for %s/%s", github_owner, github_repo)
                gh_items = await GitHubIngestor(github_owner, github_repo, github_token).ingest_all()
                all_items.extend(gh_items)
                
            if notion_token:
                logger.info("Running Notion ingestor")
                notion_items = await NotionIngestor(notion_token).ingest_all()
                all_items.extend(notion_items)
                
            if discord_token:
                logger.info("Running Discord ingestor")
                # We don't have allowed_guilds saved in db right now, pass empty to ingest all accessible
                discord_items = await DiscordIngestor(discord_token, allowed_guilds=[]).ingest_all()
                all_items.extend(discord_items)
        else:
            import os
            from ingest.files.files import DocumentIngestor
            data_dir = f"./data/{dataset}"
            if os.path.exists(data_dir):
                logger.info("Running Document ingestor on %s", data_dir)
                doc_items = await DocumentIngestor(data_dir).ingest_all()
                all_items.extend(doc_items)
            else:
                logger.info("No local data directory found for sync: %s", data_dir)

        staged, skipped, errors = await stage_items(all_items, dataset)
        
        logger.info("Running cognify on dataset %s", dataset)
        await run_cognify(dataset=dataset)
        
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "UPDATE sync_jobs SET status = 'COMPLETED', completed_at = ?, items_synced = ? WHERE id = ?",
            (now, staged, job_id)
        )
        cursor.execute(
            "UPDATE projects SET last_synced_at = ?, last_ingested_at = ? WHERE id = ?",
            (now, now, project_id)
        )
        conn.commit()
        
    except Exception as e:
        logger.error("Sync job %s failed: %s", job_id, e, exc_info=True)
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "UPDATE sync_jobs SET status = 'FAILED', completed_at = ?, error = ? WHERE id = ?",
            (now, str(e), job_id)
        )
        conn.commit()
    finally:
        conn.close()


def handle_start_sync(project_id: str, background_tasks: BackgroundTasks, db: sqlite3.Connection, is_initial: bool = False) -> SyncJobResponse:
    # Ensure project exists
    cursor = db.cursor()
    cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Check if a job is already running for ANY project (limit to 1 globally)
    cursor.execute("SELECT id FROM sync_jobs WHERE status IN ('PENDING', 'RUNNING')")
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Another sync job is currently running. Please wait for it to finish.")

    job_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO sync_jobs (id, project_id, status) VALUES (?, ?, 'PENDING')",
        (job_id, project_id)
    )
    db.commit()

    # Launch background task
    background_tasks.add_task(run_sync_job_background, project_id, job_id, is_initial)
    
    return SyncJobResponse(
        job_id=job_id,
        message="Initial ingestion started" if is_initial else "Incremental sync started"
    )

def handle_get_status(project_id: str, db: sqlite3.Connection) -> SyncStatusResponse:
    cursor = db.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cursor.execute(
        "SELECT * FROM sync_jobs WHERE project_id = ? ORDER BY rowid DESC LIMIT 1",
        (project_id,)
    )
    job = cursor.fetchone()

    # Determine project status for UI
    project_status = "PENDING"
    if project["last_ingested_at"]:
        project_status = "INDEXED"
    if job and job["status"] in ("PENDING", "RUNNING"):
        project_status = "SYNCING"
    if job and job["status"] == "FAILED" and not project["last_ingested_at"]:
        project_status = "FAILED"

    return SyncStatusResponse(
        project_id=project_id,
        status=project_status,
        last_synced_at=project["last_synced_at"],
        last_ingested_at=project["last_ingested_at"],
        active_job_id=job["id"] if job else None,
        active_job_status=job["status"] if job else None,
        items_synced=job["items_synced"] if job else 0,
        error=job["error"] if job else None
    )
