import asyncio
import os
import logging
import sqlite3
from datetime import datetime, timezone
import httpx

from db import DB_PATH
from tool.comment import leave_github_comment
from utils.recall import recall_data
from api.handlers.chat import _call_llm

logger = logging.getLogger(__name__)

async def fetch_new_issues_prs(repo_owner: str, repo_name: str, token: str, since: str):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    # If since is provided, fetch everything updated since then. 
    params = {"since": since, "state": "open"} if since else {"state": "open", "sort": "created", "direction": "desc", "per_page": 5}
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers, params=params)
        res.raise_for_status()
        return res.json()

async def poll_github_projects():
    """
    Background worker that polls GitHub for new PRs/Issues and leaves automated AI reviews.
    """
    logger.info("[Scheduler] Polling system started...")
    
    while True:
        auto_review = os.getenv("AUTO_REVIEW", "False").lower() in ("true", "1", "yes")
        if not auto_review:
            await asyncio.sleep(60)
            continue
            
        try:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Fetch all projects with a GitHub token
            cursor.execute("""
                SELECT p.id, p.repo_owner, p.repo_name, p.dataset, p.last_polled_at, s.token 
                FROM projects p 
                JOIN project_sources s ON p.id = s.project_id 
                WHERE s.source_type = 'github'
            """)
            projects = cursor.fetchall()
            
            now = datetime.now(timezone.utc).isoformat()
            
            for p in projects:
                since = p["last_polled_at"]
                issues = await fetch_new_issues_prs(p["repo_owner"], p["repo_name"], p["token"], since)
                
                for issue in issues:
                    # Ignore issues/PRs created before `since` to avoid duplicate comments
                    created_at = issue["created_at"]
                    if since and created_at <= since:
                        continue
                        
                    is_pr = "pull_request" in issue
                    item_type = "Pull Request" if is_pr else "Issue"
                    title = issue.get("title", "")
                    body = issue.get("body", "") or ""
                    
                    logger.info(f"[Scheduler] New {item_type} detected: #{issue['number']} - Generating AI review...")
                    
                    # 1. Recall context from knowledge graph
                    query = f"{title}\n{body}"
                    try:
                        context = await recall_data(query, datasets=[p["dataset"]], top_k=5)
                        context_str = "\\n".join([str(c) for c in context]) if context else "No relevant context found in knowledge graph."
                    except Exception as e:
                        logger.error(f"[Scheduler] Failed to fetch context for #{issue['number']}: {e}")
                        context_str = "Could not retrieve context due to an error."
                    
                    # 2. Ask LLM to generate response
                    system_prompt = f"""You are an expert AI maintainer for the repository {p['repo_owner']}/{p['repo_name']}.
A new {item_type} has been opened. Please provide a helpful, constructive, and detailed review or response.
Use the following context from the project's knowledge graph to inform your response:

{context_str}
"""
                    llm_messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Title: {title}\\n\\nBody:\\n{body}\\n\\nPlease review this {item_type}."}
                    ]
                    
                    try:
                        ai_review = await _call_llm(llm_messages, expect_json=False)
                        final_comment = f"🤖 **Automated AI Review**\\n\\n{ai_review}"
                        
                        await leave_github_comment(
                            p["repo_owner"], p["repo_name"], issue["number"], final_comment, p["token"]
                        )
                    except Exception as e:
                        logger.error(f"[Scheduler] Failed to generate or post AI review on #{issue['number']}: {e}")
                    
                # Update the last_polled_at timestamp for this project
                cursor.execute("UPDATE projects SET last_polled_at = ? WHERE id = ?", (now, p["id"]))
                conn.commit()
                
        except Exception as e:
            logger.error(f"[Scheduler] Error during polling cycle: {e}", exc_info=True)
        finally:
            if 'conn' in locals():
                conn.close()
            
        # Poll every 60 seconds
        await asyncio.sleep(60)
