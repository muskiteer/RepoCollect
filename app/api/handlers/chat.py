import sqlite3
import uuid
from datetime import datetime, timezone
import json
import httpx
import os
import logging
from pydantic import BaseModel
from typing import List, Optional

from utils.recall import recall_data
from tool.Issues import open_github_issue
from tool.pages import create_notion_page

logger = logging.getLogger(__name__)

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str

class SendMessageRequest(BaseModel):
    message: str

def handle_list_conversations(project_id: str, db: sqlite3.Connection) -> List[ConversationResponse]:
    cursor = db.cursor()
    cursor.execute("SELECT id, title, created_at FROM conversations WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
    rows = cursor.fetchall()
    return [ConversationResponse(id=r["id"], title=r["title"] or "New Chat", created_at=r["created_at"]) for r in rows]

def handle_create_conversation(project_id: str, db: sqlite3.Connection) -> ConversationResponse:
    cursor = db.cursor()
    conv_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO conversations (id, project_id, title, created_at) VALUES (?, ?, ?, ?)",
        (conv_id, project_id, "New Chat", now)
    )
    db.commit()
    return ConversationResponse(id=conv_id, title="New Chat", created_at=now)

def handle_get_messages(conversation_id: str, db: sqlite3.Connection) -> List[MessageResponse]:
    cursor = db.cursor()
    cursor.execute("SELECT id, role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conversation_id,))
    rows = cursor.fetchall()
    return [MessageResponse(**dict(r)) for r in rows]

async def _call_llm(messages: list, expect_json: bool = False) -> str:
    api_key = os.getenv("GROQ_API")
    if not api_key:
        raise ValueError("GROQ_API not found in environment variables")
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen/qwen3-32b",
        "messages": messages,
        "temperature": 0.2
    }
    if expect_json:
        payload["response_format"] = {"type": "json_object"}
        
    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, json=payload, timeout=60.0)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]

async def handle_send_message(conversation_id: str, req: SendMessageRequest, db: sqlite3.Connection) -> MessageResponse:
    cursor = db.cursor()
    
    # Verify conversation exists and get project info
    cursor.execute("""
        SELECT c.project_id, p.dataset, p.repo_owner, p.repo_name 
        FROM conversations c 
        JOIN projects p ON c.project_id = p.id 
        WHERE c.id = ?
    """, (conversation_id,))
    conv_data = cursor.fetchone()
    if not conv_data:
        raise ValueError("Conversation not found")
        
    project_id = conv_data["project_id"]
    dataset = conv_data["dataset"]
    repo_owner = conv_data["repo_owner"]
    repo_name = conv_data["repo_name"]
    
    # Fetch tokens
    cursor.execute("SELECT source_type, token FROM project_sources WHERE project_id = ?", (project_id,))
    tokens = {row["source_type"]: row["token"] for row in cursor.fetchall()}
    
    # Save user message
    now = datetime.now(timezone.utc).isoformat()
    msg_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, 'user', ?, ?)",
        (msg_id, conversation_id, req.message, now)
    )
    db.commit()
    
    # Detect tool call
    is_issue = "/issue" in req.message
    is_notion = "/Notion" in req.message
    query = req.message.replace("/issue", "").replace("/Notion", "").strip()
    if not query:
        query = req.message
        
    # Recall context
    try:
        context = await recall_data(query, datasets=[dataset], top_k=5)
        context_str = "\\n".join([str(c) for c in context]) if context else "No additional context found."
    except Exception as e:
        logger.error(f"Failed to fetch context from knowledge graph: {e}")
        context_str = "No additional context found."
    
    # Get conversation history
    cursor.execute("SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT 10", (conversation_id,))
    history = cursor.fetchall()
    
    llm_messages = [{"role": "system", "content": f"You are a helpful assistant for the project {repo_owner}/{repo_name}. Context:\\n{context_str}"}]
    for h in history[:-1]: # Don't add the last one twice
        llm_messages.append({"role": h["role"], "content": h["content"]})
        
    # Add the current user query to history
    llm_messages.append({"role": "user", "content": req.message})
    
    if is_issue:
        llm_messages[0]["content"] += """
        
You need to open a GitHub issue. Based on the user's request and the context provided, return ONLY a valid JSON object with these exact keys:
"title": The title of the issue
"body": The body/description of the issue
"response_text": A friendly message to display to the user confirming you will open the issue, and summarizing what it contains.
"""
        try:
            llm_response = await _call_llm(llm_messages, expect_json=True)
            data = json.loads(llm_response)
            if tokens.get("github"):
                await open_github_issue(repo_owner, repo_name, data["title"], data["body"], tokens["github"])
            assistant_reply = data.get("response_text", "Issue successfully created.")
        except Exception as e:
            logger.error(f"Failed to process /issue tool: {e}", exc_info=True)
            assistant_reply = f"Sorry, I failed to open the GitHub issue. Error: {e}"
            
    elif is_notion:
        llm_messages[0]["content"] += """
        
You need to create a Notion page. Based on the user's request and the context provided, return ONLY a valid JSON object with these exact keys:
"title": The title of the page
"content": The content of the page (plain text)
"parent_id": The ID of the parent page (infer from context or user message, or use a default placeholder if none provided)
"response_text": A friendly message to display to the user confirming the page creation.
"""
        try:
            llm_response = await _call_llm(llm_messages, expect_json=True)
            data = json.loads(llm_response)
            parent_id = data.get("parent_id") or "default_parent_id"
            if tokens.get("notion"):
                await create_notion_page(parent_id, data["title"], data["content"], tokens["notion"])
            assistant_reply = data.get("response_text", "Notion page successfully created.")
        except Exception as e:
            logger.error(f"Failed to process /Notion tool: {e}", exc_info=True)
            assistant_reply = f"Sorry, I failed to create the Notion page. Error: {e}"
            
    else:
        # Standard chat
        try:
            assistant_reply = await _call_llm(llm_messages, expect_json=False)
        except Exception as e:
            logger.error(f"Failed to call LLM: {e}", exc_info=True)
            assistant_reply = "I'm having trouble connecting to the AI model right now."
            
    # Save assistant reply
    asst_id = str(uuid.uuid4())
    asst_now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, 'assistant', ?, ?)",
        (asst_id, conversation_id, assistant_reply, asst_now)
    )
    
    # Auto-update conversation title if it's the first message
    if len(history) <= 1:
        title = req.message[:50] + "..." if len(req.message) > 50 else req.message
        cursor.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id))
        
    db.commit()
    
    return MessageResponse(id=asst_id, role="assistant", content=assistant_reply, created_at=asst_now)
