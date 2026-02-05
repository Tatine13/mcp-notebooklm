"""Tests for MCP NotebookLM client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from mcp_notebooklm.client import NotebookLMClient
from mcp_notebooklm.config import Config
from mcp_notebooklm.exceptions import (
    AuthenticationError,
    NotebookNotFoundError,
    PlaywrightNotConfiguredError,
)


class TestConfig:
    """Test configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        assert config.base_dir == Path("/home/fkomp/Bureau/oracle/tools/mcp-NotebookLLM")
        assert config.python_env_dir == Path("/mnt/windows/App_Wubuntu/python_envs/mcp-notebooklm")
        assert config.notebooklm_timeout == 60
        assert config.notebooklm_headless == True


class TestNotebookLMClient:
    """Test NotebookLM client."""
    
    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return NotebookLMClient()
    
    @pytest.mark.asyncio
    async def test_initialize_without_playwright_path(self, client, monkeypatch):
        """Test initialization fails without PLAYWRIGHT_BROWSERS_PATH."""
        monkeypatch.delenv("PLAYWRIGHT_BROWSERS_PATH", raising=False)
        
        with pytest.raises(PlaywrightNotConfiguredError):
            await client.initialize()
    
    @pytest.mark.asyncio
    async def test_list_notebooks_not_authenticated(self, client):
        """Test list_notebooks fails when not authenticated."""
        with pytest.raises(AuthenticationError):
            await client.list_notebooks()
    
    def test_set_notebook(self, client):
        """Test setting current notebook."""
        notebook_id = "test-notebook-id"
        client.set_notebook(notebook_id)
        assert client.current_notebook_id == notebook_id
    
    def test_is_authenticated_initially_false(self, client):
        """Test client is not authenticated initially."""
        assert client.is_authenticated == False
