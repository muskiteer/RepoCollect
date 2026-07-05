# 🧠 RepoCollect / Cognee — Onboarding Knowledge Layer

> Built for the **WeMakeDevs × Cognee Hackathon** — "The Hangover Part AI: Where's My Context?"  
> Jun 29 – Jul 5, 2026

---

## 📋 Overview

**RepoCollect** (branded internally as **Open Memory**) is an onboarding knowledge layer for open-source projects and new hires. It ingests a project's scattered history — GitHub issues, PRs, Discord threads, Notion docs — into a **hybrid graph-vector knowledge store** (powered by Cognee), then makes that knowledge queryable via:

- A **REST API** (FastAPI) — for custom integrations and the web UI
- An **MCP Server** — so Claude Desktop, Claude Code, Cursor, and Windsurf can ask questions
- A **Web UI** (Vite + React) — chat interface to browse the knowledge graph

The core idea: new contributors join a project and ask questions in plain English, getting answers grounded in **actual project history** — not hallucinations.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER                         │
│                                                             │
│  GitHub API          Discord API        Notion API          │
│  ─────────           ───────────        ──────────          │
│  • Issues            • Server threads   • Pages             │
│  • PRs (open +       • Forum posts      • Databases         │
│    rejected)         • Announcements    • Nested blocks     │
│  • Commit msgs       • Attachments      • Comments          │
│  • Code reviews      (PDF / text)                            │
│  • Discussions                                             │
│  • Releases                                                │
│  • Repo files                                              │
│            │                │                │             │
│            └────────────────┴────────────────┘             │
│                             │                               │
│                    Deduplication + Staging                  │
│              (content hash dedup → cognee.add())            │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼ cognee.cognify()
┌─────────────────────────────────────────────────────────────┐
│                    COGNEE CORE LAYER                        │
│                                                             │
│         Hybrid Graph-Vector Knowledge Store                 │
│                                                             │
│   Entities:  Files, PRs, People, Decisions, Bugs            │
│   Relations: "PR #482 fixed Bug in auth-service             │
│               discussed in #incident-channel                │
│               decided by Alice in 2023 meeting"             │
│                                                             │
│   add()      → buffer content (no LLM)                      │
│   cognify()  → process buffer → embeddings + graph          │
│   recall()   → semantic search + graph traversal            │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      QUERY LAYER                            │
│                                                             │
│   MCP Server  ───────  Claude Desktop / Cursor / Windsurf   │
│   REST API    ───────  Custom integrations                  │
│   Web UI      ───────  Chat interface (Vite + React)       │
└─────────────────────────────────────────────────────────────┘
```

The ingestion pipeline follows a **two-phase** approach:

1. **Phase 1 — Stage:** Each source ingestor fetches data and converts it to `DataItem` objects. Items are deduplicated by content hash and buffered via `cognee.add()`. No LLM/embedding work happens here.
2. **Phase 2 — Cognify:** A single `cognee.cognify()` call processes everything in the buffer — running embeddings, building the knowledge graph, and extracting entities/relations.

This separation means fetching is fast and LLM costs are incurred exactly once per batch.

---

## 📁 Project Structure

```
cognee/
├── Info.md                       # this file
├── README.md                     # setup instructions (Discord bot setup)
├── RepoCollect-architecture.md     # detailed architecture document
├── ingest.md                     # planned ingestion sources list
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # (placeholder — empty)
│
├── app/                          # Backend (FastAPI)
│   ├── main.py                   # FastAPI app creation, router mount, dev entrypoint
│   ├── .env                      # API keys (not tracked)
│   ├── .env.example              # template for .env
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py             # REST endpoints (health, ingest/all)
│   │   └── handler.py            # orchestration: fetch → dedup → add → cognify
│   │
│   ├── ingest/
│   │   ├── github/
│   │   │   └── github.py         # GitHub ingestion (files, issues, PRs, discussions, releases)
│   │   ├── discord/
│   │   │   └── discord.py        # Discord ingestion (guilds, channels, threads, messages, attachments)
│   │   └── notion/
│   │       └── notion.py         # Notion ingestion (pages, databases, blocks → markdown)
│   │
│   ├── internal/
│   │   └── json_to_markdown.py   # utility: JSON → Markdown converter
│   │
│   └── utils/
│       └── remember.py           # cognee.add() + cognee.cognify() wrappers
│
├── ui/                           # Frontend (Vite + React + TypeScript)
│   ├── index.html
│   ├── vite.config.ts            # proxies /api → localhost:8000
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/                  # API client (fetch → /api/v1/*)
│       ├── pages/                # Dashboard, Ingest, Search
│       └── components/           # Layout, SourceCard, ChatPanel
│
└── docs/                         # Documentation site (Next.js)
    ├── next.config.ts
    ├── package.json
    ├── content/                  # Markdown docs
    └── pages/                    # Next.js pages
```

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- Ollama (for local LLM + embeddings) — or a cloud LLM provider key (Gemini)

### Backend

```bash
# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp app/.env.example app/.env
# Edit app/.env with your API keys

# Run the server
uvicorn app.main:app --reload
# → http://localhost:8000
# → API docs at http://localhost:8000/docs
```

### Frontend (UI)

```bash
cd ui
npm install
npm run dev
# → http://localhost:5173
```

### Documentation Site

```bash
cd docs
npm install
npm run dev
# → http://localhost:3000
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `LLM_PROVIDER` | Yes | `"ollama"` or `"gemini"` |
| `LLM_MODEL` | Yes | e.g. `"qwen3:4b"`, `"gemini/gemini-2.5-flash"` |
| `LLM_ENDPOINT` | Ollama | `"http://localhost:11434/v1"` |
| `LLM_API_KEY` | Yes | API key or `"ollama"` for local |
| `EMBEDDING_PROVIDER` | Yes | `"ollama"` |
| `EMBEDDING_MODEL` | Yes | `"nomic-embed-text:latest"` |
| `EMBEDDING_ENDPOINT` | Yes | `"http://localhost:11434/api/embed"` |
| `EMBEDDING_DIMENSIONS` | Yes | `"768"` |
| `GITHUB_PAT_TOKEN` | GitHub ingest | GitHub Personal Access Token |
| `NOTION_TOKEN` | Notion ingest | Notion Integration Token (`secret_...`) |
| `DISCORD_BOT_TOKEN` | Discord ingest | Discord Bot Token (`MTAx...`) |

---

## 🔌 API Reference

All endpoints are mounted under `/api/v1`.

### Health Check

```
GET /api/v1/health
```

Response:
```json
{ "status": "ok" }
```

### Ingest All Sources

```
POST /api/v1/ingest/all
```

Request body:
```json
{
  "github_owner": "facebook",
  "github_repo": "react",
  "discord_allowed_guilds": []
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `github_owner` | string | Yes | GitHub org or username |
| `github_repo` | string | Yes | Repository name |
| `discord_allowed_guilds` | string[] | No | Restrict Discord to specific guild IDs (empty = all) |

Response:
```json
{
  "github_total": 150,
  "notion_total": 12,
  "discord_total": 340,
  "staged_total": 490,
  "duplicates_skipped": 12,
  "errors": {}
}
```

The endpoint:
1. Fetches from **all three sources concurrently** using `asyncio.gather()`
2. Deduplicates items by SHA-256 content hash
3. Stages unique items into Cognee via `cognee.add()`
4. Runs a single `cognee.cognify()` pass to build the knowledge graph

Errors are returned per-source (e.g. `{"github": "ValueError: GITHUB_PAT_TOKEN is not configured."}`) so one source failing doesn't block others.

---

## 📥 Current Ingestion Sources

### 🐙 GitHub (`app/ingest/github/github.py`)

| Artifact | Details |
|---|---|
| **Repository files** | README.md, CONTRIBUTING.md, CHANGELOG.md, LICENSE, docs/, src/ |
| **Issues** | All states (open/closed), with labels, comments, author |
| **Pull Requests** | All states, with review comments, base/head branches |
| **Discussions** | Via GraphQL API, with category tags |
| **Releases** | Release notes, tags, pre-release flag |

The GitHub ingestor intelligently filters files — it skips binaries, lock files, build artifacts, and vendor directories while prioritizing documentation and important source code.

### 💬 Discord (`app/ingest/discord/discord.py`)

| Artifact | Details |
|---|---|
| **Guilds** | Filtered by allowed list; skips unavailable guilds |
| **Channels** | Skips voice, stage, category channels; skips noisy channels (random, memes, spam, etc.) |
| **Threads** | Active threads fetched for each guild |
| **Messages** | History via pagination; removes system messages and exact duplicates |
| **Attachments** | PDF (text extraction via pypdf) and text files; skips binaries (.exe, .zip, .mp4, .mov) |

### 📝 Notion (`app/ingest/notion/notion.py`)

| Artifact | Details |
|---|---|
| **Pages** | Full workspace search, recursive block fetching |
| **Databases** | Metadata extraction |
| **Blocks** | 15+ block type renderers → Markdown (headings, lists, code, quotes, tables, to-do, callouts, equations, etc.) |
| **Rich text** | Bold, italic, code, strikethrough, links preserved |
| **Nested pages** | Recursive child page/database ingestion |

---

## 🚀 Planned & Future Ingestion Sources

New sources follow the same established pattern:

```
SourceIngestor class
  → fetches data via HTTP API / SDK
  → produces list[DataItem] (content + metadata)
  → handler.py deduplicates + stages + cognifies
```

Each new ingestor lives at `app/ingest/<source>/<source>.py`, and a new route (or extended handler) is added in `app/api/`.

### 1. 🌐 Static Documentation Sites

- **Docusaurus, Mintlify, GitBook, MkDocs** — crawl and ingest all pages
- Generic **sitemap-based web crawler** for any docs site
- Preserve page hierarchy and cross-links
- Priority: **High** — most OSS projects have docs sites

### 2. 📁 File Upload / Folder Ingestion

- Direct upload of PDF, DOCX, CSV, JSON, HTML, Markdown, TXT
- **Recursive folder ingestion** — point at a local docs directory
- ZIP upload with batch extraction
- Priority: **High** — enables users to ingest local knowledge

### 3. 💼 Slack

- Public channels, threads, messages, file attachments
- Use Slack API with Bot token + `conversations.history`
- Filter by allowed channels (mirror Discord pattern)
- Priority: **High** — many engineering teams live in Slack

### 4. 📋 Linear / Jira

- Issues, epics, sprints, comments, project descriptions
- Linear: GraphQL API (`linear-sdk` Python package)
- Jira: REST API with JQL queries
- Priority: **Medium** — critical for project management context

### 5. 🦊 GitLab

- Mirror GitHub ingestor: Issues, MRs, Wiki, Releases, Snippets
- Self-hosted GitLab support via custom endpoint
- Priority: **Medium** — large OSS ecosystem

### 6. 📖 Confluence

- Spaces, pages, attachments, comments, labels
- Confluence REST API with pagination
- Convert storage format → Markdown
- Priority: **Medium** — common enterprise knowledge base

### 7. 📧 Email

- Engineering mailing lists, RFC discussions, decision threads
- IMAP / Gmail API integration
- Thread reconstruction from message subjects/references
- Priority: **Low** — many OSS projects have critical context in mailing lists

### 8. 📡 RSS / Blog Feeds

- Engineering blogs, changelog RSS, release notes
- Periodic polling for new content
- Priority: **Low** — keeps memory fresh with external context

### 9. 🎥 YouTube / Loom Transcripts

- Tech talks, walkthroughs, meeting recordings
- YouTube Data API captions / Loom API
- Timestamps + transcript → searchable text
- Priority: **Low** — rich but unstructured source

### 10. 📂 Local File System Watch

- Watch directories for new/modified `.md`, `.rst`, `.txt` files
- `watchdog`-based auto-ingestion on file change
- Priority: **Low** — power-user feature

---

## 🛠️ Action Tools — Beyond Passive Ingestion

The system is designed to evolve from a **read-only knowledge base** into an **active contributor** that can participate in project workflows. These tools use the knowledge graph context to make intelligent actions — not blind automation.

### Architecture Pattern

Each action tool follows the same pattern:

```
User / Webhook trigger
  → ActionTool class
  → recalls() relevant context from Cognee knowledge graph
  → LLM decides action based on context + prompt
  → executes via source API (GitHub, Discord, etc.)
  → reports result
```

Each action lives at `app/actions/<source>/<action>.py`, exposed as both a **REST endpoint** and an **MCP tool**.

### 🐙 GitHub Actions

#### 1. 🔍 PR Review Assistant

```
POST /api/v1/actions/github/review-pr
```

- Automatically reviews open PRs when triggered (via webhook or manual)
- Uses `cognee.recall()` to find related issues, past PRs, and decisions relevant to the changed code
- Generates a review comment with:
  - Links to past discussions / decisions that affect this change
  - Potential regressions flagged based on historical bug patterns
  - Style/pattern consistency checks against the repo's established practices
- Posts the review inline on the PR

**MCP tool:** `review_pull_request(owner, repo, pr_number)`

#### 2. 🏷️ Issue Triage & Labeling

```
POST /api/v1/actions/github/triage-issue
```

- When a new issue is opened, automatically:
  - Searches for duplicate issues via semantic similarity
  - Suggests labels based on historical labeling patterns
  - Assigns to the most relevant contributor based on past work
  - Adds a comment linking to related discussions / past fixes

**MCP tool:** `triage_issue(owner, repo, issue_number)`

#### 3. 💬 Context-Aware Reply Suggestion

```
POST /api/v1/actions/github/suggest-reply
```

- When a maintainer is about to reply to an issue or PR comment
- Queries the knowledge graph for relevant prior art
- Suggests a draft reply grounded in project history
- Example: *"This was actually discussed in PR #482. Here's what was tried and why it was rejected..."*

**MCP tool:** `suggest_reply(owner, repo, issue_number, comment_id)`

#### 4. 🧠 Knowledge Gap Detection → Open Discussion

- Analyzes incoming questions (issues, Discord messages)
- If the query has no match in the knowledge graph (`recall()` returns weak results):
  - Automatically opens a **GitHub Discussion** tagging relevant maintainers
  - Suggests the question as documentation to be written
  - This closes the loop: questions that can't be answered become new knowledge artifacts

**MCP tool:** `suggest_discussion_topic(owner, repo, topic, context)`

#### 5. 🔄 Auto-PR for Known Fix Patterns

- When a new issue matches a known bug pattern from the knowledge graph:
  - Retrieves the historical fix pattern via `recall()`
  - Generates a draft PR with the fix applied
  - Opens it as a draft PR with links to the relevant historical context
- Example: *"PR #1234 fixed a race condition in the auth service. This new issue matches that pattern — here's a draft fix."*

**MCP tool:** `suggest_fix_pr(owner, repo, issue_number)`

#### 6. 📊 Project Health Dashboard

```
GET /api/v1/actions/github/health?owner=foo&repo=bar
```

- Analyzes the knowledge graph to produce:
  - **Decision debt:** How many open questions have no documented decision?
  - **Stale PRs:** PRs waiting longer than average with no activity
  - **Expert locator:** Who owns each module based on PR history and review patterns
  - **Knowledge density:** Which areas have the most/least documentation coverage

**MCP tool:** `project_health(owner, repo)`

### 💬 Discord Actions

#### 7. 🤖 FAQ Auto-Responder

- Monitors Discord channels for common questions
- Queries the knowledge graph for the best answer
- Posts a contextual reply with links to relevant GitHub issues / PRs / docs
- If no answer found, flags it for the knowledge gap detector

**MCP tool:** `answer_discord_question(guild_id, channel_id, message_id)`

#### 8. 🧵 Thread Summarizer

- When a Discord thread reaches N messages or X hours old:
  - Summarizes the thread
  - Posts summary back in the channel
  - Archives the summary into the knowledge graph

**MCP tool:** `summarize_discord_thread(guild_id, thread_id)`

### 🔌 Unified MCP Server Tools

All actions are also exposed as MCP tools for use inside Claude Desktop, Claude Code, Cursor, and Windsurf:

```python
@mcp.tool()
async def review_pull_request(owner: str, repo: str, pr_number: int) -> str:
    """Review a PR using project history context."""

@mcp.tool()
async def triage_issue(owner: str, repo: str, issue_number: int) -> str:
    """Auto-triage an issue: dedup, label, assign."""

@mcp.tool()
async def suggest_reply(owner: str, repo: str, issue_number: int, comment_id: int) -> str:
    """Suggest a context-aware reply grounded in project history."""

@mcp.tool()
async def answer_question(query: str, channel: str) -> str:
    """Answer a question using the knowledge graph, posted to the channel."""

@mcp.tool()
async def project_health(owner: str, repo: str) -> str:
    """Analyze project health metrics from the knowledge graph."""
```

### Implementation Priority

| Tool | Complexity | Impact | Priority |
|---|---|---|---|
| Issue Triage & Labeling | Low | High | **P0** |
| Context-Aware Reply Suggestion | Medium | High | **P0** |
| PR Review Assistant | High | High | **P1** |
| FAQ Auto-Responder (Discord) | Medium | Medium | **P1** |
| Thread Summarizer (Discord) | Low | Medium | **P1** |
| Knowledge Gap Detection | Medium | High | **P1** |
| Project Health Dashboard | Medium | Medium | **P2** |
| Auto-PR for Known Fixes | High | Medium | **P2** |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI + uvicorn (port 8000) |
| **Memory / Knowledge Graph** | Cognee (`cognee[fastembed]`) |
| **LLM Provider** | Ollama (local) or Gemini (cloud) |
| **Embeddings** | `nomic-embed-text` via Ollama |
| **Ingestion HTTP** | `httpx` (async) |
| **PDF Extraction** | `pypdf` |
| **Frontend** | Vite + React + TypeScript (port 5173) |
| **Doc Site** | Next.js (port 3000) |
| **Auth / Tokens** | GitHub PAT, Notion Integration Token, Discord Bot Token |

---

## 🗺️ Development Roadmap

| Day | Goal |
|---|---|
| **Day 1** (Jun 29) | Set up Cognee Cloud, build GitHub ingestion pipeline |
| **Day 2** (Jun 30) | Build Smart Memory Router (tagging + filtering) |
| **Day 3** (Jul 1) | Discord ingestion + Notion ingestion |
| **Day 4** (Jul 2) | Build MCP server with `remember`, `recall`, `forget`, `improve` tools |
| **Day 5** (Jul 3) | Web UI / chat interface + REST API refinement |
| **Day 6** (Jul 4) | Polish, test on real OSS repos, fix edge cases |
| **Day 7** (Jul 5) | Record demo video, finalize README, submit |

---

## 🤝 Contributing

### Adding a New Ingestion Source

1. Create `app/ingest/<source>/<source>.py` with a class that:
   - Takes credentials in `__init__`
   - Has an `async def ingest_all() -> list[DataItem]` method
   - Uses the same `DataItem` dataclass pattern (content + metadata)
   - Implements `should_ingest_*` filter methods for noise reduction

2. Add a route in `app/api/routes.py` or extend the handler in `handler.py`

3. Add the required env variable to `app/.env.example`

### Code Conventions

- **No comments** in production code unless absolutely necessary
- Logging at `INFO` level for high-level pipeline events, `DEBUG` for per-item details
- Each ingestor defines its own `DataItem` dataclass (deduplication to shared model is a future improvement)
- All HTTP clients are async (`httpx`) and closed in `finally` blocks
- Content deduplication uses SHA-256 of normalized whitespace

---

> *Inspired by LORE (GitLab AI Hackathon 2026) — extended for the open source world.*  
> *Built with Cognee × WeMakeDevs Hackathon, Jun 29 – Jul 5, 2026*
