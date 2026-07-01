from typing import List
from fastapi import APIRouter, Depends
import sqlite3

from db import get_db
from api.handlers.chat import (
    ConversationResponse,
    MessageResponse,
    SendMessageRequest,
    handle_list_conversations,
    handle_create_conversation,
    handle_get_messages,
    handle_send_message
)

router = APIRouter(tags=["Chat"])

@router.get("/projects/{id}/conversations", response_model=List[ConversationResponse])
def list_conversations(id: str, db: sqlite3.Connection = Depends(get_db)):
    return handle_list_conversations(id, db)

@router.post("/projects/{id}/conversations", response_model=ConversationResponse)
def create_conversation(id: str, db: sqlite3.Connection = Depends(get_db)):
    return handle_create_conversation(id, db)

@router.get("/chat/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(conversation_id: str, db: sqlite3.Connection = Depends(get_db)):
    return handle_get_messages(conversation_id, db)

@router.post("/chat/{conversation_id}", response_model=MessageResponse)
async def send_message(conversation_id: str, req: SendMessageRequest, db: sqlite3.Connection = Depends(get_db)):
    return await handle_send_message(conversation_id, req, db)
