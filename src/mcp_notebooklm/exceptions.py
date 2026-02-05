"""Custom exceptions for MCP NotebookLM."""


class MCPNotebookLMError(Exception):
    """Base exception for MCP NotebookLM."""
    pass


class AuthenticationError(MCPNotebookLMError):
    """Raised when authentication fails."""
    pass


class NotebookNotFoundError(MCPNotebookLMError):
    """Raised when a notebook is not found."""
    pass


class SourceNotFoundError(MCPNotebookLMError):
    """Raised when a source is not found."""
    pass


class GenerationError(MCPNotebookLMError):
    """Raised when content generation fails."""
    pass


class PlaywrightNotConfiguredError(MCPNotebookLMError):
    """Raised when PLAYWRIGHT_BROWSERS_PATH is not set."""
    pass


class TimeoutError(MCPNotebookLMError):
    """Raised when an operation times out."""
    pass


class RateLimitError(MCPNotebookLMError):
    """Raised when rate limit is exceeded."""
    pass
