"""Tests for MCP NotebookLM tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from mcp_notebooklm.tools import notebooks


class TestNotebooksTools:
    """Test notebook tools."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock client."""
        client = MagicMock()
        client.list_notebooks = AsyncMock(return_value=[
            {
                "id": "nb-1",
                "title": "Test Notebook",
                "sources_count": 5,
                "created_at": "2026-01-01T00:00:00"
            }
        ])
        return client


class TestSourcesTools:
    """Test source tools."""
    
    pass  # TODO: Add source tests


class TestChatTools:
    """Test chat tools."""
    
    pass  # TODO: Add chat tests
