# 📦 Installation & Deep Configuration Guide

This guide covers the deployment of the **MCP NotebookLM** server, with a focus on **Authentication** and **Multi-Profile Management**.

---

## 📋 Prerequisites

1.  **Python 3.11+**: Essential for the specific async features used.
2.  **Google Account**: To access NotebookLM.
3.  **Browsers**: This project uses **Playwright** (Chromium) to automate Google interactions.

---

## 🛠️ Step-by-Step Installation

### 1. Clone & Install
```bash
git clone https://github.com/Tatine13/mcp-notebooklm.git
cd mcp-notebooklm

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (Editable mode)
pip install -e .
```

### 2. Browser Setup (Critical)
The server needs a browser to log in.
- **Option A (Recommended)**: Use system-installed Playwright browsers.
  ```bash
  export PLAYWRIGHT_BROWSERS_PATH="/path/to/ms-playwright"
  ```
- **Option B**: Let Playwright manage them.
  ```bash
  playwright install chromium
  ```

---

## 🔐 Authentication : The Complete Manual

Authentication is the most critical part. We use a **Headless-First** approach with **Interactive Fallback**.

### Procedure for HUMANS (Initial Setup)
You cannot log in headlessly the first time due to Google's rigorous checks (2FA, CAPTCHA).

1.  **Stop any running MCP server**.
2.  **Run the Login Command**:
    ```bash
    # Inside your venv
    notebooklm login
    ```
3.  **Interact**:
    - A Chrome window will open.
    - Log in to your Google Account.
    - Wait for the NotebookLM homepage to load.
    - Close the window.
4.  **Verification**:
    - A `storage_state.json` file is created in `~/.mcp-notebooklm/profiles/default/`.
    - This token is valid for ~30 days.

### Procedure for AI / Headless Usage
Once the `storage_state.json` exists:
- The AI (Claude/Gemini) connects to the MCP server.
- The server loads the JSON token.
- **No browser window appears** (Headless mode is default).
- If the token expires, the AI tools (`list_notebooks`, etc.) will return an error requesting a re-login.

---

## 👤 Multi-Profile Management (Advanced)

This MCP server supports multiple isolated Google accounts seamlessly.

### How it works
Each profile is a separate directory in `~/.mcp-notebooklm/profiles/<profile_name>/`. It contains its own:
- `storage_state.json` (Auth cookies)
- `cookies.json`
- Local cache

### creating a New Profile
To add a second account (e.g., "Work"):

1.  **AI Command**:
    > "Create a new profile named 'work'"
    *(Tool: `create_profile(name='work')`)*

2.  **Switch Context**:
    > "Switch to profile 'work'"
    *(Tool: `switch_profile(name='work')`)*

3.  **Authenticate**:
    The strictly isolated 'work' profile has no tokens yet.
    - **Trigger**: Run `setup_auth(headless=False)`.
    - **Action**: Opens a *new, clean* browser instance.
    - **Input**: Log in with your Work Google Account.

### Managing Profiles
- **List**: `list_profiles()` shows all available environments.
- **Current**: `get_current_profile()` tells you where you are.
- **Isolation**: Work performed in 'work' (notebook creation, sources) is invisible to 'default' and vice-versa.

---

## ⚙️ Configuration for MCP Clients

### Claude Desktop / Code
```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["-m", "mcp_notebooklm"],
      "env": {
        "PLAYWRIGHT_BROWSERS_PATH": "/path/to/browsers",
        "NOTEBOOKLM_HEADLESS": "true"
      }
    }
  }
}
```

### Gemini CLI / OpenCode
```json
{
  "mcpServers": {
    "notebooklm": {
        "command": "python",
        "args": ["-m", "mcp_notebooklm"],
        "env": {
          "MCP_NOTEBOOKLM_LOG_LEVEL": "INFO"
        }
    }
  }
}
```
