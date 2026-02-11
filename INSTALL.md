# Installation & Configuration

## 🚀 Quick Start

### 1. Prerequisite: Python Environment

Ensure you have a Python 3.11+ environment with the package installed.

```bash
# Verify installation
python -m mcp_notebooklm
```

### 2. Configure Your Client (Claude Code / Gemini CLI)

Add this entry to your MCP `settings.json`.

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "/path/to/your/venv/bin/python",
      "args": [
        "-m",
        "mcp_notebooklm"
      ],
      "env": {
        "PLAYWRIGHT_BROWSERS_PATH": "/path/to/playwright/browsers"
      }
    }
  }
}
```

> **Note**: `PLAYWRIGHT_BROWSERS_PATH` is optional if Playwright is installed globally or in standard locations.

### 3. NotebookLM Authentication

The first time run requires a one-time Google login:

```bash
# Activate your virtual environment
source .venv/bin/activate

# Launch interactive login
notebooklm login
```
This will open a Chrome window. Log in to your Google account, then close the window. The session is saved locally.

---

## 🧪 Testing the Server

```bash
# Basic health check
python tests/test_basic.py

# Verify imports
python -c "from mcp_notebooklm import mcp; print('✅ OK:', mcp.name)"
```

---

## 🔧 Maintenance

### Updating the Package

If you installed via git:

```bash
cd mcp-NotebookLLM
git pull
pip install -e .
```

---

## 📊 Feature Highlights

| Feature | Description |
|---------|-------------|
| **Auto-Discovery** | No need to paste URLs. `list_notebooks` finds them all. |
| **Multi-Profile** | Support for multiple Google accounts with isolation. |
| **Full RAG** | Chat, Cite, and Retrieve source content. |
| **Content Factory** | Generate Audio, Video, Briefings, Slides, and more. |
