"""Configuration management for MCP NotebookLM."""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Configuration for MCP NotebookLM."""
    
    model_config = SettingsConfigDict(
        env_prefix="MCP_NOTEBOOKLM_",
        # DO NOT read .env files - they conflict with project .env files
        # env_file=".env",
        extra="ignore",  # Ignore unknown environment variables like GEMINI_API_KEYS
    )
    
    # Base paths
    base_dir: Path = Field(
        default=Path("/home/fkomp/Bureau/oracle/tools/mcp-NotebookLLM"),
        description="Base directory for the project"
    )
    
    # Python environment (decentralized - required)
    python_env_dir: Path = Field(
        default=Path("/mnt/windows/App_Wubuntu/python_envs/mcp-notebooklm"),
        description="Python virtual environment directory"
    )
    
    # Playwright configuration (from ecosystem)
    playwright_browsers_path: str = Field(
        default="/mnt/windows/App_Wubuntu/playraightNav/ms-playwright",
        description="Playwright browsers path (must be set in environment)"
    )
    
    # NotebookLM settings
    notebooklm_timeout: int = Field(default=60, description="Timeout for NotebookLM operations")
    notebooklm_headless: bool = Field(default=True, description="Run browser in headless mode")
    notebooklm_profile_dir: Path = Field(
        default=Path.home() / ".config" / "notebooklm-py",
        description="Profile directory for notebooklm-py"
    )
    
    # MCP settings
    mcp_transport: str = Field(default="stdio", description="MCP transport mode")
    mcp_log_level: str = Field(default="info", description="Log level")
    
    # Cache settings
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    
    @field_validator("playwright_browsers_path")
    @classmethod
    def validate_playwright_path(cls, v: str) -> str:
        """Validate that PLAYWRIGHT_BROWSERS_PATH is set."""
        env_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH")
        if env_path:
            return env_path
        return v
    
    @property
    def config_dir(self) -> Path:
        """Return configuration directory."""
        return self.base_dir / "config"
    
    @property
    def data_dir(self) -> Path:
        """Return data directory."""
        return self.base_dir / "data"
    
    @property
    def logs_dir(self) -> Path:
        """Return logs directory."""
        return self.base_dir / "logs"
    
    @property
    def notebooks_cache_file(self) -> Path:
        """Return notebooks cache file path."""
        return self.data_dir / "notebooks_cache.json"
    
    @property
    def python_bin(self) -> Path:
        """Return Python binary path."""
        return self.python_env_dir / "bin" / "python"
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.notebooklm_profile_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
