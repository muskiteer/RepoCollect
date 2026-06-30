from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE, override=True)

print(f"Loaded .env from: {ENV_FILE}")
print("LLM_PROVIDER =", os.getenv("LLM_PROVIDER"))
print("LLM_MODEL =", os.getenv("LLM_MODEL"))

# Fetch GitHub PAT
GITHUB_PAT_TOKEN = os.getenv("GITHUB_PAT_TOKEN")

if not GITHUB_PAT_TOKEN:
    raise ValueError("GITHUB_PAT_TOKEN is not set in the .env file.")

from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="Cognee Ingestion API",
    description="Ingests GitHub repositories (and more) into cognee for RAG / knowledge-graph workflows.",
    version="0.1.0",
)

app.include_router(router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)