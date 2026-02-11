# 📘 MCP NotebookLM - Project Bible & Summary

> **Version**: 1.0.1 (Production Ready)
> **Status**: Stable / Maintained
> **Core Library**: `notebooklm-py` (Fork: Tatine13)

A comprehensive, production-grade MCP server for Google NotebookLM, exposing **50+ tools** to AI agents. This project bridges the gap between LLMs (Claude, models via OpenRouter) and your personal knowledge base in NotebookLM.

---

## 🏗️ Architecture & Technology Stack

### Core Components
1.  **FastMCP Server** (`server.py`): The main entry point, handling request routing, tool execution, and lifecycle management.
2.  **Client Wrapper** (`client.py`): A robust wrapper around the `notebooklm-py` library, handling authentication persistence and session management.
3.  **Library Fork** (`notebooklm-py` @ Tatine13): A maintained fork of the reverse-engineered API, patching critical bugs in source addition (RPC parameter alignment) and artifact generation.
4.  **Playwright Runtime**: Utilizes the existing Oracle ecosystem's Playwright browsers (Chromium) to handle Google authentication and complex web interactions.

### Directory Structure
```
mcp-NotebookLLM/
├── src/mcp_notebooklm/
│   ├── server.py            # Main MCP Server definition
│   ├── client.py            # Client Wrapper & Auth Manager
│   ├── contracts.py         # Pydantic models & data structures
│   └── tools/               # Modular Tool Implementations
│       ├── auth.py          # Authentication tools
│       ├── notebooks.py     # Notebook CRUD & discovery
│       ├── sources.py       # Source management (URL, File, Drive)
│       ├── chat.py          # Chat & History
│       ├── artifacts.py     # Generation (Audio, Video, Quiz...)
│       ├── research_tools.py# Deep Research integration
│       ├── sharing.py       # Collaboration features
│       └── profiles.py      # Multi-profile management
├── config/                  # Configuration files
├── tests/                   # Extensive test suite
└── logs/                    # Runtime logs
```

---

## 🛠️ Complete Tool Catalog (50 Tools)

### 🔐 Authentication & Profiles (8)
*Tools to manage identity and session isolation. Essential for multi-account usage.*
- `setup_auth`: Interactive login flow (opens browser).
- `check_auth`: Verifies if the current session is valid.
- `confirm_auth`: Finalizes the login process after browser interaction.
- `create_profile`: Creates a separated storage constraint (new account).
- `switch_profile`: Hot-swaps the active user profile.
- `list_profiles`: Shows all available profiles.
- `get_current_profile`: Returns metadata of the active session.
- `update_profile`: Updates profile metadata (name, description).

### 📓 Notebook Management (10)
*Lifecycle management of notebooks. No manual URLs required.*
- `list_notebooks`: **Auto-discovery** of all notebooks in the account.
- `list_all_notebooks`: Aggregated view across ALL profiles.
- `search_notebooks`: Semantic/Keyword search in notebook titles.
- `select_notebook`: Sets the "Active Context" for subsequent commands.
- `create_notebook`: Instantiates a new empty notebook.
- `rename_notebook`: Renames an existing notebook.
- `delete_notebook`: Permanently removes a notebook.
- `get_notebook_info`: detailed metadata (source count, date, etc.).
- `get_current_notebook`: Returns the currently active notebook context.
- `export_notebook`: Dumps all metadata and source list to JSON.

### 📚 Source Management (12)
*Ingestion and management of knowledge sources. The "R" in RAG.*
- `add_url_source`: Ingests Web pages or YouTube videos (transcript).
- `add_file_source`: Uploads local files (PDF, TXT, MD, MP3...).
- `batch_add_sources`: Optimized bulk ingestion of multiple mixed sources.
- `list_notebook_sources`: Metadata of all sources in a notebook.
- `list_drive_sources`: Specific view for Google Drive linked sources.
- `get_source_content`: **Retrieves full indexed text** of a source.
- `get_source_guide`: Retrieves AI-generated summary & keywords.
- `check_source_freshness`: Compares local/Drive version vs NotebookLM version.
- `refresh_source`: Triggers a re-sync of a specific source.
- `rename_source`: Renames a source citation title.
- `remove_source`: Deletes a source from the notebook.
- `download_all_sources`: Backs up all source text content locally.

### 🕵️ Research & Discovery (2)
*Autonomous agents for information gathering.*
- `research_topic`: Performs Deep or Fast web/drive research and returns references.
- `import_research_sources`: Imports selected results from research directly into the notebook.

### 💬 Chat & Analysis (3)
*Direct interaction with the Language Model.*
- `ask_question`: Sends a prompt to the notebook. Returns Answer + Citations.
- `configure_chat`: Sets system persona (e.g., "Critical Critic", "Tutor").
- `get_conversation_history`: Retrieves past turns of the chat session.

### 🎨 Content Generation (Artifacts) (10)
*Transforming knowledge into new formats.*
- `create_audio_overview`: Generates Podcasts (Deep Dive, Brief, etc.).
- `create_video_overview`: Generates AI Videos with avatars.
- `generate_slides`: Creates Presentation Decks (PDF).
- `generate_infographic`: Creates Visual Summaries (PNG).
- `generate_mind_map`: Creates conceptual Mind Maps (JSON).
- `generate_study_guide`: Creates Review Guides / Cheat Sheets.
- `create_quiz`: Generates interactive Quizzes (JSON/MD).
- `create_flashcards`: Generates Study Cards (JSON/MD).
- `generate_report`: Generates comprehensive text reports/blog posts.
- `create_data_table`: Extracts structured data (CSV).

### 🔧 Artifact Management (4)
- `list_notebook_artifacts`: Shows all generated assets in a notebook.
- `download_generated_content`: Downloads artifacts (MP3, MP4, PDF, etc.).
- `monitor_artifact`: Tracks generation progress (polling).
- `delete_notebook_artifact`: Removes a generated asset.

### 🤝 Collaboration & Notes (5)
- `share_with_user`: Invites email addresses (Viewer/Editor).
- `remove_share`: Revokes access.
- `get_share_status`: Audits permissions and public link status.
- `set_public_sharing`: Toggles "Anyone with link" access.
- `manage_note`: CRUD for sticky notes within the notebook.

---

## ⚙️ Configuration & Environment

### Environment Variables
| Variable | Description | Required | Default |
|----------|-------------|:--------:|---------|
| `PLAYWRIGHT_BROWSERS_PATH` | Path to Playwright browsers | ✅ | (System path) |
| `NOTEBOOKLM_HEADLESS` | Run browser in background | ❌ | `true` |
| `NOTEBOOKLM_TIMEOUT` | Global operation timeout | ❌ | `60` (seconds) |
| `MCP_NOTEBOOKLM_LOG_LEVEL` | Logging verbosity | ❌ | `INFO` |

### Caching System
The system implements a **File-Based Cache** (`~/.cache/mcp-notebooklm/`) to reduce latency:
- **Notebook Lists**: Cached for 5 minutes.
- **Source Lists**: Cached for 1 minute.
- **Artifacts**: Cached until explicit refresh.
*To force refresh, most list tools accept a `refresh=True` parameter.*

### Retry & Resilience
- **Smart Retries**: Network flakiness is handled with exponential backoff (3 retries).
- **Circuit Breaker**: If authentication fails repeatedly, the system fails fast to prevent account locking.
- **Human-in-the-loop**: Auth flows degrade gracefully to interactive mode if tokens expire.

---

## 🔄 Development Workflow

### Contributing
This project relies on a **Fork** of `notebooklm-py`.
- **Do not** submit PRs regarding source-add fixes to this repo if they belong in the library.
- See `CONTRIBUTING.md` for the workflow to submit upstream fixes.

### Testing
Run the full suite using `pytest`:
```bash
# Activation
source /mnt/windows/App_Wubuntu/python_envs/mcp-notebooklm/bin/activate
# Run
pytest tests/
```
