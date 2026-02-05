"""
MCP NotebookLM Server

MCP server for Google NotebookLM with automatic notebook discovery.
Based on notebooklm-py library by teng-lin.
"""

__version__ = "1.0.0"
__author__ = "Esprit Artificiel"
__license__ = "MIT"

from .server import mcp, main
from .client import NotebookLMClient
from .config import Config, config
from .exceptions import (
    MCPNotebookLMError,
    AuthenticationError,
    NotebookNotFoundError,
    PlaywrightNotConfiguredError,
)

__all__ = [
    "mcp",
    "main",
    "NotebookLMClient", 
    "Config",
    "config",
    "MCPNotebookLMError",
    "AuthenticationError",
    "NotebookNotFoundError",
    "PlaywrightNotConfiguredError",
    "__version__",
]
