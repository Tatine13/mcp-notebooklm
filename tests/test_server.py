"""Tests for MCP NotebookLM server."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_notebooklm.server import mcp


class TestMCPTools:
    """Test MCP tools."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock context."""
        context = MagicMock()
        context.request_context.lifespan_context = MagicMock()
        return context
    
    @pytest.mark.asyncio
    async def test_check_auth_authenticated(self, mock_context):
        """Test check_auth when authenticated."""
        mock_client = MagicMock()
        mock_client.is_authenticated = True
        mock_client.current_notebook_id = "test-id"
        mock_context.request_context.lifespan_context = mock_client
        
        # Import here to avoid circular imports
        from mcp_notebooklm.server import check_auth
        result = await check_auth(mock_context)
        
        assert result["authenticated"] == True
        assert result["current_notebook"] == "test-id"
    
    @pytest.mark.asyncio
    async def test_check_auth_not_authenticated(self, mock_context):
        """Test check_auth when not authenticated."""
        mock_client = MagicMock()
        mock_client.is_authenticated = False
        mock_context.request_context.lifespan_context = mock_client
        
        from mcp_notebooklm.server import check_auth
        result = await check_auth(mock_context)
        
        assert result["authenticated"] == False


class TestServerInitialization:
    """Test server initialization."""
    
    def test_mcp_server_exists(self):
        """Test that MCP server is defined."""
        assert mcp is not None
        assert mcp.name == "mcp-notebooklm"
