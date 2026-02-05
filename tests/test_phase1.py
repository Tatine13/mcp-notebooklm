
import sys
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import pytest

# Mock notebooklm before importing client
sys.modules["notebooklm"] = MagicMock()
sys.modules["notebooklm.rpc"] = MagicMock()

# Mock fastmcp
mock_fastmcp = MagicMock()
mock_context = MagicMock()
sys.modules["fastmcp"] = mock_fastmcp
mock_fastmcp.Context = MagicMock

# Now import our modules
from mcp_notebooklm.client import NotebookLMClient
from mcp_notebooklm.tools import notebooks, sources, artifacts
from mcp_notebooklm import server

# Setup AsyncMock for client methods
@pytest.mark.asyncio
async def test_rename_notebook():
    # Setup
    ctx = MagicMock()
    client = AsyncMock()
    ctx.request_context.lifespan_context = client
    
    # Configure client mock
    client.rename_notebook.return_value = {"id": "nb1", "title": "New Title"}
    
    # Test
    result = await notebooks.rename_notebook(ctx, "nb1", "New Title")
    
    # Verify
    client.rename_notebook.assert_called_with("nb1", "New Title")
    assert result["title"] == "New Title"

@pytest.mark.asyncio
async def test_delete_notebook():
    # Setup
    ctx = MagicMock()
    client = AsyncMock()
    ctx.request_context.lifespan_context = client
    
    # Configure client mock
    client.delete_notebook.return_value = True
    
    # Test
    result = await notebooks.delete_notebook(ctx, "nb1")
    
    # Verify
    client.delete_notebook.assert_called_with("nb1")
    assert "✅" in result

@pytest.mark.asyncio
async def test_export_notebook():
    # Setup
    ctx = MagicMock()
    client = AsyncMock()
    ctx.request_context.lifespan_context = client
    
    mock_data = {
        "metadata": {"title": "Test"},
        "sources": [],
        "chat_history": []
    }
    client.export_notebook.return_value = mock_data
    
    # Test
    result = await notebooks.export_notebook(ctx, "nb1")
    
    # Verify
    client.export_notebook.assert_called_with("nb1")
    assert result == mock_data

@pytest.mark.asyncio
async def test_refresh_source():
    # Setup
    ctx = MagicMock()
    client = AsyncMock()
    ctx.request_context.lifespan_context = client
    client.refresh_source.return_value = True
    
    # Test
    result = await sources.refresh_source(ctx, "src1")
    
    # Verify
    client.refresh_source.assert_called_with("src1", None)
    assert "✅" in result

@pytest.mark.asyncio
async def test_rename_source():
    # Setup
    ctx = MagicMock()
    client = AsyncMock()
    ctx.request_context.lifespan_context = client
    client.rename_source.return_value = True
    
    # Test
    result = await sources.rename_source(ctx, "src1", "New Source Title")
    
    # Verify
    client.rename_source.assert_called_with("src1", "New Source Title", None)
    assert "✅" in result

@pytest.mark.asyncio
async def test_generate_slides():
    # Setup
    ctx = MagicMock()
    client = AsyncMock()
    ctx.request_context.lifespan_context = client
    
    # Note: generate_artifact logic in artifacts.py uses _get_client context manager
    # We need to mock that behavior.
    # In artifacts.py:
    # async with await client._get_client() as nl_client:
    #     status = await nl_client.artifacts.generate_slide_deck(...)
    
    # So client._get_client() returns an async context manager that yields nl_client
    nl_client = AsyncMock()
    client._get_client.return_value.__aenter__.return_value = nl_client
    
    # Mock current_notebook_id
    client.current_notebook_id = "nb1"
    
    # Mock return
    task_mock = MagicMock()
    task_mock.task_id = "task123"
    nl_client.artifacts.generate_slide_deck.return_value = task_mock
    
    # Test
    result = await artifacts.generate_slides(ctx, length="medium")
    
    # Verify
    assert result["task_id"] == "task123"
    assert result["status"] == "generating"

@pytest.mark.asyncio
async def test_server_tools_registration():
    # Test that tools are registered in server.py
    # We just import server and check mcp.tool calls?
    # Since we mocked fastmcp, we can check mcp.tool()
    
    # Re-import to ensure decorators ran
    import importlib
    importlib.reload(server)
    
    # server.mcp is the mock_fastmcp instance
    # mock_fastmcp.tool is a decorator.
    # We can check if it was called.
    assert server.mcp.tool.called
