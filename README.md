# MCP NotebookLM

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-FastMCP_v2-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A powerful MCP (Model Context Protocol) server for **Google NotebookLM** with **automatic notebook discovery**, **multi-profile management**, and **50+ tools** for content generation.

## ✨ Features

- 🔍 **Automatic notebook discovery** - List all your notebooks without manual URLs
- 👥 **Multi-profile support** - Manage multiple Google accounts with isolated profiles
- 🔎 **Unified search** - Search notebooks across ALL profiles simultaneously
- 💬 **Chat with citations** - Ask questions and get answers with source citations
- 📦 **Source management** - Add URLs, files, Google Drive documents
- 🎨 **Content generation** - Podcasts, videos, quizzes, flashcards, slides, and more
- 🔗 **Sharing & collaboration** - Manage access, invite users, generate public links
- 📝 **Notes management** - Full CRUD operations for notebook notes

## 📋 Requirements

- Python 3.11+
- Playwright browsers installed
- Google account with NotebookLM access

## 🛠️ Installation

```bash
git clone https://github.com/Tatine13/mcp-notebooklm.git
cd mcp-notebooklm
python -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
notebooklm login
```

## ⚙️ Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "python",
      "args": ["-m", "mcp_notebooklm"],
      "env": {
        "PLAYWRIGHT_BROWSERS_PATH": "<path-to-playwright-browsers>"
      }
    }
  }
}
```

## 📝 Available Tools (50 Total)

### Authentication & Multi-Profile 🔐
- `setup_auth`, `confirm_auth`, `check_auth`
- `create_profile`, `switch_profile`, `list_profiles`, `get_current_profile`, `delete_profile`, `update_profile`

### Notebook Management
- `list_notebooks`, `list_all_notebooks` 🌍, `search_notebooks` 🔍
- `select_notebook`, `create_notebook`, `rename_notebook`, `delete_notebook`
- `export_notebook`, `get_notebook_info`, `get_current_notebook`

### Source Management
- `list_notebook_sources`, `add_url_source`, `add_file_source`, `batch_add_sources`
- `refresh_source`, `rename_source`, `remove_source`, `download_all_sources`
- `get_source_guide`, `get_source_content`, `check_source_freshness`, `list_drive_sources`

### Research & Discovery 🕵️
- `research_topic` 🌟 - Deep/Fast Research (Web OR Drive) with Auto-Import
- `import_research_sources`

### Chat & Q&A
- `ask_question` - Ask questions with citations
- `get_conversation_history`

### Content Generation
- `create_audio_overview`, `create_video_overview`, `create_quiz`, `create_flashcards`
- `generate_slides`, `generate_infographic`, `generate_mind_map`, `generate_study_guide`
- `generate_report`, `create_data_table`, `download_generated_content`

### Sharing & Collaboration
- `get_share_status`, `set_public_sharing`, `share_with_user`, `remove_share`

### Notes Management
- `manage_note` - CRUD operations (list, create, get, update, delete)

## 🚀 Quick Start

```
"List my notebooks"
"Use the AI Research notebook"
"What are the key findings?"
"Create a podcast about this notebook"
"Switch to my work profile"
```

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [notebooklm-py](https://github.com/teng-lin/notebooklm-py) by teng-lin
- [FastMCP](https://github.com/jlowin/fastmcp) by jlowin
