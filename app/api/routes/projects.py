from typing import List
from fastapi import APIRouter, Depends
import sqlite3

from db import get_db
from api.handlers.projects import (
    ProjectCreate,
    ProjectResponse,
    AuthenticateRequest,
    handle_create_project,
    handle_list_projects,
    handle_get_project,
    handle_delete_project,
    handle_authenticate_project
)

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: sqlite3.Connection = Depends(get_db)):
    return await handle_create_project(project, db)

@router.get("", response_model=List[ProjectResponse])
def list_projects(db: sqlite3.Connection = Depends(get_db)):
    return handle_list_projects(db)

@router.get("/{id}", response_model=ProjectResponse)
def get_project(id: str, db: sqlite3.Connection = Depends(get_db)):
    return handle_get_project(id, db)

@router.delete("/{id}")
async def delete_project(id: str, db: sqlite3.Connection = Depends(get_db)):
    return await handle_delete_project(id, db)

@router.post("/{id}/authenticate")
async def authenticate_project(id: str, auth: AuthenticateRequest, db: sqlite3.Connection = Depends(get_db)):
    return await handle_authenticate_project(id, auth, db)

from fastapi import BackgroundTasks
from api.handlers.sync import handle_start_sync, handle_get_status, SyncJobResponse, SyncStatusResponse

@router.post("/{id}/ingest", response_model=SyncJobResponse)
def ingest_project(id: str, background_tasks: BackgroundTasks, db: sqlite3.Connection = Depends(get_db)):
    return handle_start_sync(id, background_tasks, db, is_initial=True)

@router.post("/{id}/sync", response_model=SyncJobResponse)
def sync_project(id: str, background_tasks: BackgroundTasks, db: sqlite3.Connection = Depends(get_db)):
    return handle_start_sync(id, background_tasks, db, is_initial=False)

@router.get("/{id}/status", response_model=SyncStatusResponse)
def project_status(id: str, db: sqlite3.Connection = Depends(get_db)):
    return handle_get_status(id, db)
