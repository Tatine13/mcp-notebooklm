#!/bin/bash

# Installation script for MCP NotebookLM

set -e

echo "🚀 Installing MCP NotebookLM..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Define paths
VENV_DIR="/mnt/windows/App_Wubuntu/python_envs/mcp-notebooklm"
PROJECT_DIR="/home/fkomp/Bureau/oracle/tools/mcp-NotebookLLM"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -e "$PROJECT_DIR"

# Check PLAYWRIGHT_BROWSERS_PATH
if [ -z "$PLAYWRIGHT_BROWSERS_PATH" ]; then
    echo "⚠️  Warning: PLAYWRIGHT_BROWSERS_PATH is not set!"
    echo "   Add this to your ~/.bashrc:"
    echo '   export PLAYWRIGHT_BROWSERS_PATH="/mnt/windows/App_Wubuntu/playraightNav/ms-playwright"'
fi

# Create necessary directories
mkdir -p "$PROJECT_DIR/data"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/config"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Ensure PLAYWRIGHT_BROWSERS_PATH is set in your environment"
echo "2. Run authentication: notebooklm login"
echo "3. Start using the MCP server"
echo ""
echo "MCP Configuration:"
echo '{'
echo '  "mcpServers": {'
echo '    "notebooklm": {'
echo '      "command": "/mnt/windows/App_Wubuntu/python_envs/mcp-notebooklm/bin/python",'
echo '      "args": ['
echo '        "-m",'
echo '        "mcp_notebooklm"'
echo '      ]'
echo '    }'
echo '  }'
echo '}'
