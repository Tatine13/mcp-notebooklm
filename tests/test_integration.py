"""Comprehensive integration tests for MCP NotebookLM."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime
from pathlib import Path

# Mock notebooklm-py before importing our modules
import sys
from unittest.mock import MagicMock

# Create a comprehensive mock for notebooklm module
mock_notebooklm = MagicMock()
mock_notebooklm.NotebookLMClient = MagicMock()
mock_notebooklm.notebooks = MagicMock()
mock_notebooklm.sources = MagicMock()
mock_notebooklm.chat = MagicMock()
mock_notebooklm.artifacts = MagicMock()

sys.modules['notebooklm'] = mock_notebooklm

from mcp_notebooklm.client import NotebookLMClient
from mcp_notebooklm.config import Config
from mcp_notebooklm.exceptions import (
    AuthenticationError,
    NotebookNotFoundError,
    PlaywrightNotConfiguredError,
)


class MockNotebook:
    """Mock notebook object."""
    def __init__(self, id, title, sources_count=0):
        self.id = id
        self.title = title
        self.sources_count = sources_count
        self.created_at = datetime.now().isoformat()


class MockSource:
    """Mock source object."""
    def __init__(self, id, name, type_="url", status="active"):
        self.id = id
        self.name = name
        self.type = type_
        self.status = status


class MockChatMessage:
    """Mock chat message."""
    def __init__(self, question, answer, citations=None):
        self.question = question
        self.answer = answer
        self.citations = citations or []
        self.timestamp = datetime.now().isoformat()


@pytest.fixture
def mock_notebooklm_client():
    """Create a fully mocked notebooklm-py client."""
    client = MagicMock()
    
    # Mock notebooks
    client.notebooks = MagicMock()
    client.notebooks.list = AsyncMock(return_value=[
        MockNotebook("nb-1", "Test Notebook 1", 5),
        MockNotebook("nb-2", "Test Notebook 2", 3),
    ])
    client.notebooks.create = AsyncMock(return_value=MockNotebook("nb-new", "New Notebook", 0))
    client.notebooks.delete = AsyncMock(return_value=None)
    client.notebooks.get = AsyncMock(return_value=MockNotebook("nb-1", "Test Notebook 1", 5))
    
    # Mock sources
    client.sources = MagicMock()
    client.sources.list = AsyncMock(return_value=[
        MockSource("src-1", "Example URL", "url"),
        MockSource("src-2", "Document.pdf", "file"),
    ])
    client.sources.add_url = AsyncMock(return_value=MockSource("src-new", "New URL", "url"))
    client.sources.upload_file = AsyncMock(return_value=MockSource("src-file", "uploaded.pdf", "file"))
    client.sources.delete = AsyncMock(return_value=None)
    
    # Mock chat
    client.chat = MagicMock()
    client.chat.ask = AsyncMock(return_value=MagicMock(
        answer="This is a test answer",
        citations=["Source 1", "Source 2"],
        sources=[{"title": "Doc 1", "url": "http://example.com"}]
    ))
    client.chat.get_history = AsyncMock(return_value=[
        MockChatMessage("What is AI?", "AI is artificial intelligence", ["Doc 1"]),
        MockChatMessage("How does it work?", "It uses machine learning", ["Doc 2"]),
    ])
    client.chat.clear = AsyncMock(return_value=None)
    
    # Mock artifacts
    client.artifacts = MagicMock()
    client.artifacts.generate_audio = AsyncMock(return_value=MagicMock(task_id="task-123"))
    client.artifacts.generate_video = AsyncMock(return_value=MagicMock(task_id="task-456"))
    client.artifacts.generate_quiz = AsyncMock(return_value=MagicMock(task_id="task-789"))
    client.artifacts.generate_flashcards = AsyncMock(return_value=MagicMock(task_id="task-abc"))
    client.artifacts.download_audio = AsyncMock(return_value=None)
    client.artifacts.download_video = AsyncMock(return_value=None)
    client.artifacts.download_quiz = AsyncMock(return_value=None)
    
    return client


@pytest.fixture
def client(mock_notebooklm_client, monkeypatch):
    """Create a NotebookLMClient with mocked dependencies."""
    # Set required env var
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", "/mnt/windows/App_Wubuntu/playraightNav/ms-playwright")
    
    # Create client
    wrapper = NotebookLMClient()
    wrapper._client = mock_notebooklm_client
    wrapper._authenticated = True
    
    return wrapper


class TestNotebookOperations:
    """Test notebook CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_list_notebooks(self, client):
        """Test listing notebooks."""
        notebooks = await client.list_notebooks()
        
        assert len(notebooks) == 2
        assert notebooks[0]["id"] == "nb-1"
        assert notebooks[0]["title"] == "Test Notebook 1"
        assert notebooks[0]["sources_count"] == 5
        assert "created_at" in notebooks[0]
    
    @pytest.mark.asyncio
    async def test_create_notebook(self, client):
        """Test creating a notebook."""
        result = await client.create_notebook("My New Notebook")
        
        assert result["id"] == "nb-new"
        assert result["title"] == "New Notebook"
        client._client.notebooks.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_notebook(self, client):
        """Test deleting a notebook."""
        result = await client.delete_notebook("nb-1")
        
        assert result is True
        client._client.notebooks.delete.assert_called_once_with("nb-1")
    
    @pytest.mark.asyncio
    async def test_get_notebook_info(self, client):
        """Test getting notebook info."""
        info = await client.get_notebook_info("nb-1")
        
        assert info["id"] == "nb-1"
        assert info["title"] == "Test Notebook 1"
        assert info["sources_count"] == 5


class TestSourceOperations:
    """Test source management."""
    
    @pytest.mark.asyncio
    async def test_list_sources(self, client):
        """Test listing sources."""
        client.set_notebook("nb-1")
        sources = await client._client.sources.list("nb-1")
        
        assert len(sources) == 2
        assert sources[0].id == "src-1"
        assert sources[0].name == "Example URL"
    
    @pytest.mark.asyncio
    async def test_add_url_source(self, client):
        """Test adding URL source."""
        client.set_notebook("nb-1")
        result = await client._client.sources.add_url("nb-1", "http://example.com", name="Example", wait=True)
        
        assert result.id == "src-new"
        assert result.name == "New URL"


class TestChatOperations:
    """Test chat functionality."""
    
    @pytest.mark.asyncio
    async def test_ask_question(self, client):
        """Test asking a question."""
        client.set_notebook("nb-1")
        result = await client.ask_question("What is AI?")
        
        assert "answer" in result
        assert result["answer"] == "This is a test answer"
        assert "citations" in result
        assert len(result["citations"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_chat_history(self, client):
        """Test getting chat history."""
        client.set_notebook("nb-1")
        history = await client.get_chat_history()
        
        assert len(history) == 2
        assert history[0]["question"] == "What is AI?"
        assert history[0]["answer"] == "AI is artificial intelligence"


class TestErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    async def test_not_authenticated(self, client):
        """Test operations fail when not authenticated."""
        client._authenticated = False
        client._client = None
        
        with pytest.raises(AuthenticationError):
            await client.list_notebooks()
    
    @pytest.mark.asyncio
    async def test_no_notebook_selected(self, client):
        """Test operations fail when no notebook selected."""
        client._current_notebook_id = None
        
        with pytest.raises(NotebookNotFoundError):
            await client.ask_question("Test question")


class TestConfiguration:
    """Test configuration management."""
    
    def test_config_paths(self):
        """Test configuration paths."""
        config = Config()
        
        assert config.base_dir.exists()
        assert config.python_env_dir.exists()
        assert config.playwright_browsers_path == "/mnt/windows/App_Wubuntu/playraightNav/ms-playwright"
    
    def test_config_directories(self):
        """Test directory creation."""
        config = Config()
        config.ensure_directories()
        
        assert config.config_dir.exists()
        assert config.data_dir.exists()
        assert config.logs_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
