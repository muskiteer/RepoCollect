import uuid
import httpx
from typing import Optional, List
from fastapi import HTTPException
from pydantic import BaseModel
import sqlite3

class ProjectCreate(BaseModel):
    repo_owner: str
    repo_name: str
    dataset: Optional[str] = None
    github_token: str
    notion_token: Optional[str] = None
    discord_token: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    repo_owner: str
    repo_name: str
    dataset: str
    status: str = "PENDING"
    last_synced_at: Optional[str] = None
    last_ingested_at: Optional[str] = None

class AuthenticateRequest(BaseModel):
    source_type: str  # e.g., GitHub, Notion, Discord
    token: str

async def validate_token(source_type: str, token: str, repo_owner: str = None, repo_name: str = None):
    source_type = source_type.lower()
    async with httpx.AsyncClient() as client:
        if source_type == "github":
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Cognee-App"
            }
            resp = await client.get(
                f"https://api.github.com/repos/{repo_owner}/{repo_name}",
                headers=headers
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=401, 
                    detail=f"Invalid GitHub token or missing permissions for repo {repo_owner}/{repo_name}. Status: {resp.status_code}"
                )
                
        elif source_type == "notion":
            headers = {
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28"
            }
            resp = await client.get("https://api.notion.com/v1/users/me", headers=headers)
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail=f"Invalid Notion token. Status: {resp.status_code}")
                
        elif source_type == "discord":
            headers = {
                "Authorization": f"Bot {token}"
            }
            resp = await client.get("https://discord.com/api/v10/users/@me", headers=headers)
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail=f"Invalid Discord Bot token. Status: {resp.status_code}")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source type: {source_type}")


async def handle_create_project(project: ProjectCreate, db: sqlite3.Connection) -> ProjectResponse:
    await validate_token("github", project.github_token, project.repo_owner, project.repo_name)
    
    if project.notion_token:
        await validate_token("notion", project.notion_token)
    if project.discord_token:
        await validate_token("discord", project.discord_token)
        
    project_id = str(uuid.uuid4())
    dataset = project.dataset or f"{project.repo_owner}/{project.repo_name}"
    
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO projects (id, repo_owner, repo_name, dataset) VALUES (?, ?, ?, ?)",
        (project_id, project.repo_owner, project.repo_name, dataset)
    )
    
    sources = [
        (str(uuid.uuid4()), project_id, "github", project.github_token, True)
    ]
    if project.notion_token:
        sources.append((str(uuid.uuid4()), project_id, "notion", project.notion_token, True))
    if project.discord_token:
        sources.append((str(uuid.uuid4()), project_id, "discord", project.discord_token, True))
        
    cursor.executemany(
        "INSERT INTO project_sources (id, project_id, source_type, token, permissions_validated) VALUES (?, ?, ?, ?, ?)",
        sources
    )
    db.commit()
    
    return ProjectResponse(
        id=project_id,
        repo_owner=project.repo_owner,
        repo_name=project.repo_name,
        dataset=dataset
    )


def handle_list_projects(db: sqlite3.Connection) -> List[ProjectResponse]:
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.id, p.repo_owner, p.repo_name, p.dataset, p.last_synced_at, p.last_ingested_at,
               (SELECT status FROM sync_jobs WHERE project_id = p.id ORDER BY rowid DESC LIMIT 1) as job_status
        FROM projects p
    """)
    rows = cursor.fetchall()
    results = []
    for row in rows:
        r = dict(row)
        status = "PENDING"
        if r["last_ingested_at"]:
            status = "INDEXED"
        if r["job_status"] in ("PENDING", "RUNNING"):
            status = "SYNCING"
        if r["job_status"] == "FAILED" and not r["last_ingested_at"]:
            status = "FAILED"
            
        r["status"] = status
        results.append(ProjectResponse(**r))
    return results


def handle_get_project(id: str, db: sqlite3.Connection) -> ProjectResponse:
    cursor = db.cursor()
    cursor.execute("SELECT id, repo_owner, repo_name, dataset FROM projects WHERE id = ?", (id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(**dict(row))


from utils.forget import delete_dataset
import logging

logger = logging.getLogger(__name__)

async def handle_delete_project(id: str, db: sqlite3.Connection) -> dict:
    cursor = db.cursor()
    cursor.execute("SELECT dataset FROM projects WHERE id = ?", (id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
        
    dataset = row["dataset"]
    
    try:
        await delete_dataset(dataset)
    except Exception as e:
        logger.error(f"Failed to delete dataset {dataset} from cognee: {e}")

    cursor.execute("DELETE FROM projects WHERE id = ?", (id,))
    cursor.execute("DELETE FROM project_sources WHERE project_id = ?", (id,))
    db.commit()
    return {"message": "Project deleted successfully"}


async def handle_authenticate_project(id: str, auth: AuthenticateRequest, db: sqlite3.Connection) -> dict:
    cursor = db.cursor()
    cursor.execute("SELECT id, repo_owner, repo_name FROM projects WHERE id = ?", (id,))
    project = cursor.fetchone()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    source_type = auth.source_type.lower()
    
    await validate_token(source_type, auth.token, project["repo_owner"], project["repo_name"])
    
    source_id = str(uuid.uuid4())
    
    cursor.execute("DELETE FROM project_sources WHERE project_id = ? AND source_type = ?", (id, source_type))
    
    cursor.execute(
        """
        INSERT INTO project_sources (id, project_id, source_type, token, permissions_validated)
        VALUES (?, ?, ?, ?, ?)
        """,
        (source_id, id, source_type, auth.token, True)
    )
    db.commit()
    return {"message": f"{auth.source_type} authenticated successfully for project {id}"}
