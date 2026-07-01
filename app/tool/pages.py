import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def create_notion_page(parent_id: str, title: str, content: str, token: str) -> Dict[str, Any]:
    """
    Create a new page in Notion.
    """
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # Create a page with a simple text block as content
    payload = {
        "parent": {
            "page_id": parent_id
        },
        "properties": {
            "title": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": content
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully created Notion page with ID {data.get('id')}")
        return data
