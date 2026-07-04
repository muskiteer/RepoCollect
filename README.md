# Repollect

> Built with ❤️ for the **WeMakeDevs × Cognee Hackathon** — Jun 29 – Jul 5, 2026

Repollect is an AI-powered organizational memory and developer copilot. It connects GitHub, Discord, Notion, and local documents into a single, searchable knowledge graph. When your team asks a question, Repollect retrieves the exact context across all platforms to give accurate, informed answers using the latest LLM models.

## ✨ Features

* **Multi-Source Knowledge Graph:** Ingests GitHub (Issues, PRs), Discord (server messages), Notion (pages), and local documents (PDF, MD, TXT).
* **Incremental Synchronization:** Lightning-fast syncs that only pull new data since your last ingestion.
* **Auto-Review Scheduler:** A background worker that automatically reviews and comments on new GitHub Issues and Pull Requests.
* **Smart Chat Interface:** Talk to your knowledge graph with specialized slash commands:
  * `/issue` — Create a new GitHub Issue directly from chat
  * `/Notion` — Create a new Notion Page
  * `iss{N}` — Fetch and discuss a specific Issue (e.g., `iss54 why was this closed?`)
  * `pr{N}` — Fetch and discuss a Pull Request
  * `diff{N}` — AI-powered explanation of a PR's code changes
  * `/contributors` — List all contributors and their commit counts
  * `@username` — Get a summary of a specific user's contributions and activity

---

## 🛠️ Tech Stack

**Frontend:**
* React + TypeScript
* Vite (Build Tool)
* React Router (Navigation)

**Backend:**
* Python + FastAPI
* SQLite (Metadata & Chat History)
* Cognee (Knowledge Graph Construction & GraphRAG)
* Groq API (High-speed LLM Inference)
* FastEmbed (Local Sentence-Transformer Embeddings)

---

## 🏗️ Architecture

Repollect is built around a GraphRAG architecture split into three main flows:

1. **Incremental Ingestion Pipeline:**
   Users add API tokens for external platforms. The backend queries GitHub, Notion, and Discord for data updated since the last sync. Data is normalized into markdown and staged into the **Cognee Buffer**. A single `cognify()` pass then processes all buffered data into embeddings and graph nodes, storing relationships across data silos.
2. **Context-Aware Chat:**
   When a user submits a query, the backend performs a semantic search across the Knowledge Graph. For specialized slash commands (like `pr12`), a real-time fetch to the GitHub API pulls live data. Both the live data and the graph context are injected into the Groq LLM prompt for highly accurate generation.
3. **Background Auto-Reviewer:**
   An asynchronous loop continuously polls GitHub for newly opened Issues and PRs. It queries the Knowledge Graph for historical context regarding the touched code/topic, generates a helpful AI review, and automatically posts it as a GitHub comment.

---

## 📁 Repository Structure

```text
cognee/
├── app/                        # Python FastAPI Backend
│   ├── api/
│   │   ├── handlers/           # Core business logic (chat, ingest, sync)
│   │   └── routes/             # FastAPI endpoints
│   ├── ingest/                 # Platform-specific data extractors
│   │   ├── discord/
│   │   ├── files/
│   │   ├── github/
│   │   └── notion/
│   ├── internal/               # Background tasks
│   │   └── scheduler.py        # GitHub auto-reviewer loop
│   ├── tool/                   # Chat-invoked live API tools
│   │   ├── comment.py          # Post GitHub comments
│   │   ├── fetch_contributor.py# Get user profiles
│   │   ├── fetch_diff.py       # Get PR diffs
│   │   ├── fetch_issue.py      # Get live issue data
│   │   └── pages.py            # Create Notion pages
│   ├── utils/                  # Cognee GraphRAG utilities
│   ├── db.py                   # SQLite database initialization
│   └── main.py                 # Application entry point
│
└── ui/                         # React Frontend
    ├── src/
    │   ├── AddProject.tsx      # Project creation UI
    │   ├── BrowseProjects.tsx  # Project list and sync dashboard
    │   ├── ChatView.tsx        # LLM interface with slash commands
    │   └── App.tsx             # Main routing
    └── package.json
```

---

## 🚀 Getting Started

### 1. Clone & Install
```bash
git clone <your-repo-url>
cd cognee

# Backend setup
cd app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../ui
npm install
```

### 2. Environment Variables (`app/.env`)
Create a `.env` file in the `app/` directory with the following structure:

```env
# LLM & Embeddings (Ollama local fallback)
LLM_PROVIDER="ollama"
LLM_MODEL="qwen2.5:7b"
LLM_ENDPOINT="http://localhost:11434/v1"
LLM_API_KEY="ollama"
EMBEDDING_PROVIDER="fastembed"
EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS="384"

# External APIs
GROQ_API=your_groq_api_key
GITHUB_PAT_TOKEN=your_github_token
NOTION_TOKEN=your_notion_token
DISCORD_BOT_TOKEN=your_discord_token

# Scheduler Config
AUTO_REVIEW=True
REVIEW_TIME_MIN=30
```

### 3. Run the App
**Terminal 1 (Backend):**
```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Frontend):**
```bash
cd ui
npm run dev
```

---

## 🔑 How to get API Keys

### Groq API Key
Used for fast LLM inference in the chat interface.
1. Go to [Groq Console](https://console.groq.com/).
2. Sign in and navigate to **API Keys**.
3. Click **Create API Key**, copy it, and paste it as `GROQ_API`.

### GitHub PAT (Personal Access Token)
Required to fetch private repos, read issues/PRs, and post comments.
1. Go to your [GitHub Settings > Developer Settings > Personal access tokens > Tokens (classic)](https://github.com/settings/tokens).
2. Click **Generate new token (classic)**.
3. Give it a name and select the `repo` scope (full control of private repositories).
4. Generate the token and paste it as `GITHUB_PAT_TOKEN`.

### Notion Integration Token
Required to search and read/write Notion pages.
1. Go to [Notion My Integrations](https://www.notion.so/my-integrations).
2. Click **New integration**.
3. Name it "Repollect", select the associated workspace, and save.
4. Copy the **Internal Integration Secret** and paste it as `NOTION_TOKEN`.
5. **CRITICAL:** You must manually share the Notion pages/databases you want Repollect to access. Open a page in Notion, click the `...` menu in the top right, go to **Add connections**, and select your "Repollect" integration.

### Discord Bot Token
Required to read channel messages for the knowledge graph.
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** and name it "Repollect".
3. Go to the **Bot** tab on the left.
4. Under **Privileged Gateway Intents**, enable **Message Content Intent** (crucial for reading messages).
5. Click **Reset Token** to generate a new token. Copy it and paste it as `DISCORD_BOT_TOKEN`.
6. Go to **OAuth2 > URL Generator**.
7. Check the `bot` scope.
8. Under **Bot Permissions**, check `Read Messages/View Channels` and `Read Message History`.
9. Copy the generated URL at the bottom, paste it into your browser, and invite the bot to your server.

---

## 🔮 Future Upgrades / Roadmap

Repollect is designed to evolve from a passive knowledge base into an active, intelligent contributor. Here is what is planned next:

### 1. Expanded Integration Ecosystem
* **Communication:** Slack (channels, threads, files) and Email (engineering mailing lists, RFCs).
* **Project Management:** Linear and Jira integration for tracking epics and sprints.
* **Knowledge Bases:** Confluence, Static Documentation Sites (Docusaurus, Mintlify, GitBook), and YouTube/Loom transcript processing.
* **Code Forges:** GitLab support mirroring our GitHub pipeline.

### 2. Advanced Action Tools
* **Issue Triage & Labeling:** Automatically deduplicate incoming issues, suggest labels, and assign maintainers based on historical expertise.
* **Auto-PR for Known Fixes:** When a bug matches a known pattern in the knowledge graph, automatically generate a draft PR with the historical fix applied.
* **Context-Aware Reply Suggestions:** Draft responses for maintainers grounded entirely in project history (e.g., *"This was tried in PR #482..."*).
* **Knowledge Gap Detection:** Identify unanswered questions in Discord or GitHub and automatically open GitHub Discussions to document the missing context.
* **Project Health Dashboard:** Track "decision debt," locate domain experts, and measure documentation coverage across the codebase.

### 3. Model Context Protocol (MCP) Server
Expose Repollect's slash commands and search capabilities via an **MCP Server** so developers can query the project knowledge graph directly from their IDEs (Cursor, Windsurf) or desktop AI assistants (Claude Desktop).

---

## 💝 Acknowledgments

- **[Cognee](https://cognee.ai)** — The graph-vector hybrid memory that makes Repollect's knowledge graph possible.
- **[WeMakeDevs](https://wemakedevs.org)** — For organizing the hackathon and bringing together builders.
- Every open source project whose public history helped shape and test this tool.

> Made with love by [muskiteer](https://github.com/muskiteer) — for every developer who's ever asked "why does this code exist?"