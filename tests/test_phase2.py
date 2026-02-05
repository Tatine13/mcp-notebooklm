
import sys
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
from pathlib import Path

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

@pytest.mark.asyncio
async def test_generate_infographic():
    # Setup
    ctx = MagicMock()
    client = AsyncMock()
    ctx.request_context.lifespan_context = client
    
    # Mock return
    task_mock = MagicMock()
    task_mock.id = "task_infographic"
    client.generate_infographic.return_value = {
        "task_id": "task_infographic",
        "status": "started",
        "type": "infographic"
    }
    
    # Test
    result = await artifacts.generate_infographic(ctx)
    
    # Verify
    client.generate_infographic.assert_called_once()
    assert result["task_id"] == "task_infographic"

@pytest.mark.asyncio
async def test_generate_mind_map():
    # Setup
    ctx = MagicMock()
    client = AsyncMock()
    ctx.request_context.lifespan_context = client
    
    client.generate_mind_map.return_value = {
        "task_id": "task_mm",
        "status": "started",
        "type": "mind_map"
    }
    
    # Test
    result = await artifacts.generate_mind_map(ctx)
    
    # Verify
    client.generate_mind_map.assert_called_once()
    assert result["task_id"] == "task_mm"

@pytest.mark.asyncio
async def test_generate_report():
    # Setup
    ctx = MagicMock()
    client = AsyncMock()
    # Fix: Ensure current_notebook_id is explicitly a value, not a Mock object or None
    client.current_notebook_id = "nb1"
    ctx.request_context.lifespan_context = client
    
    client.generate_report.return_value = {
        "task_id": "task_rep",
        "status": "started", 
        "type": "report"
    }
    
    # Test
    result = await artifacts.generate_report(ctx, instructions="Topic")
    
    # Verify
    client.generate_report.assert_called_with("Topic", "nb1")
    assert result["task_id"] == "task_rep"

@pytest.mark.asyncio
async def test_download_all_sources():
    # Setup
    ctx = MagicMock()
    client = AsyncMock()
    ctx.request_context.lifespan_context = client
    
    client.current_notebook_id = "nb1"
    
    # Mock download_sources returning list of files
    client.download_sources.return_value = ["/path/source1.txt", "/path/source2.txt"]
    
    # Test
    result = await sources.download_all_sources(ctx, "/output/path")
    
    # Verify
    client.download_sources.assert_called_with("/output/path", "nb1")
    assert "✅" in result
    assert "2 sources" in result

@pytest.mark.asyncio
async def test_download_all_sources_empty():
    # Setup
    ctx = MagicMock()
    client = AsyncMock()
    ctx.request_context.lifespan_context = client
    client.current_notebook_id = "nb1"
    
    client.download_sources.return_value = []
    
    # Test
    result = await sources.download_all_sources(ctx, "/output/path")
    
    # Verify
    assert "⚠️ No sources downloaded" in result

@pytest.mark.asyncio
async def test_server_tools_registration_phase2():
    # Verifying server tools are registered
    import importlib
    importlib.reload(server)
    assert server.mcp.tool.called
