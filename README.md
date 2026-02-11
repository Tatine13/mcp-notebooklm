# ... (README content as read previously) ...
# MCP NotebookLM

MCP server for Google NotebookLM with automatic notebook discovery, based on the `notebooklm-py` library.

## 🚀 Features

- ✅ **Automatic notebook discovery** - List all your notebooks without manual URLs
- ✅ **Chat with citations** - Ask questions and get answers with source citations  
- ✅ **Source management** - Add URLs, files, Google Drive documents
- ✅ **Content generation** - Generate podcasts, videos, quizzes, flashcards
- ✅ **Playwright integration** - Uses existing Playwright installation from Oracle ecosystem

## 📋 Requirements

- Python 3.11+
- `PLAYWRIGHT_BROWSERS_PATH` environment variable set
- Google account with NotebookLM access

## 🛠️ Installation

### 1. Clone and setup

```bash
cd /home/fkomp/Bureau/oracle/tools/mcp-NotebookLLM
./scripts/install.sh
```

### 2. Ensure environment variables are set

Add to your `~/.bashrc`:

```bash
export PLAYWRIGHT_BROWSERS_PATH="/mnt/windows/App_Wubuntu/playraightNav/ms-playwright"
```

### 3. Authenticate with NotebookLM

```bash
/mnt/windows/App_Wubuntu/python_envs/mcp-notebooklm/bin/notebooklm login
```

### 4. Configure MCP client

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "/mnt/windows/App_Wubuntu/python_envs/mcp-notebooklm/bin/python",
      "args": ["-m", "mcp_notebooklm"]
    }
  }
}
```

## 📝 Usage

Once configured, you can use these tools in your MCP client:

### Authentication & Multi-Profile 🔐
- `setup_auth` - Set up authentication
- `check_auth` - Check authentication status
- `create_profile` - Create a new isolated profile
- `switch_profile` - Switch active profile
- `list_profiles` - List all profiles
- `get_current_profile` - Get current profile info
- `delete_profile` - Delete a profile
- `update_profile` - Update profile metadata

### Notebook Management
- `list_notebooks` - List notebooks in current profile
- `list_all_notebooks` - **List all notebooks across ALL profiles** 🌍
- `search_notebooks` - **Search notebooks across ALL profiles** 🔍
- `select_notebook` - Select a notebook to work with
- `create_notebook` - Create a new notebook
- `rename_notebook` - Rename a notebook (New)
- `delete_notebook` - Delete a notebook (New)
- `export_notebook` - Export notebook metadata and sources (New)
- `get_notebook_info` - Get detailed notebook information
- `get_current_notebook` - Get the currently selected notebook

### Source Management
- `list_notebook_sources` - List all sources in a notebook
- `add_url_source` - Add a URL source (website, YouTube)
- `add_file_source` - Add a file source (PDF, text)
- `refresh_source` - Refresh a source
- `rename_source` - Rename a source
- `delete_source` - Delete a source permanently
- `download_all_sources` - Download text content of all sources
- `get_source_guide` - Get AI-generated summary & keywords for a source 🆕
- `get_source_content` - Get full indexed text content of a source 🆕
- `check_source_freshness` - Check if a source needs refresh 🆕
- `list_drive_sources` - List Drive sources with freshness status 🆕

### Research & Discovery 🕵️
- `research_topic` - **Deep/Fast Research (Web OR Drive) with Auto-Import** 🌟
- `import_research_sources` - Import specific sources from research

### Chat & Q&A
- `ask_question` - Ask questions with citations
- `get_conversation_history` - Get chat history
- `clear_conversation` - Clear chat history

### Content Generation
- `create_audio_overview` - Generate a podcast (audio overview)
- `create_video_overview` - Generate a video
- `create_quiz` - Generate a quiz
- `create_flashcards` - Generate flashcards
- `generate_slides` - Generate a presentation slide deck
- `generate_infographic` - Generate an infographic
- `generate_mind_map` - Generate a mind map
- `generate_study_guide` - Generate a study guide
- `generate_report` - Generate a detailed report with instructions
- `create_data_table` - Generate a data table 🆕
- `download_generated_content` - Download generated content

### Sharing & Collaboration 🆕
- `get_share_status` - Get current sharing settings & collaborators
- `set_public_sharing` - Enable/disable public link access
- `share_with_user` - Share notebook with a user by email
- `remove_share` - Remove a user's access to the notebook

### Notes Management 🆕
- `manage_note` - CRUD operations for notes (list, create, get, update, delete)

**Total: 50 tools available!**



## 🏗️ Architecture

- **Environment**: Decentralized Python virtual environment in `/mnt/windows/App_Wubuntu/python_envs/`
- **Playwright**: Uses existing Oracle ecosystem Playwright installation
- **Library**: Built on `notebooklm-py` by teng-lin (unofficial Python API)
- **MCP Framework**: FastMCP v2

## 📁 Project Structure

```
mcp-NotebookLLM/
├── src/mcp_notebooklm/     # Main package
├── config/                 # Configuration files
├── scripts/                # Installation scripts
├── tests/                  # Test suite
└── logs/                   # Log files
```

## ⚠️ Important Notes

- **Playwright browsers path** must be set before running the server
- **Authentication** is persistent via Chrome profile
- **No share links required** - notebooks are discovered automatically
- **Oracle ecosystem compatible** - respects existing Playwright configuration

## 🔧 Development

```bash
# Activate environment
source /mnt/windows/App_Wubuntu/python_envs/mcp-notebooklm/bin/activate

# Install in editable mode
pip install -e /home/fkomp/Bureau/oracle/tools/mcp-NotebookLLM

# Run tests
pytest tests/
```

## 📄 License

MIT License - See LICENSE file for details.
