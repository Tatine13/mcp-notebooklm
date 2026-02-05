"""Utility functions for MCP NotebookLM."""

import os
import re
from pathlib import Path
from typing import Optional
from loguru import logger

from ..config import config
from ..exceptions import PlaywrightNotConfiguredError


def validate_playwright_config() -> bool:
    """
    Validate that Playwright is properly configured.
    
    Returns:
        True if configured correctly
        
    Raises:
        PlaywrightNotConfiguredError: If PLAYWRIGHT_BROWSERS_PATH is not set
    """
    browsers_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH")
    
    if not browsers_path:
        raise PlaywrightNotConfiguredError(
            f"PLAYWRIGHT_BROWSERS_PATH environment variable is not set.\n"
            f"Expected: {config.playwright_browsers_path}\n"
            f"Add this to your ~/.bashrc:\n"
            f'export PLAYWRIGHT_BROWSERS_PATH="{config.playwright_browsers_path}"'
        )
    
    if not Path(browsers_path).exists():
        logger.warning(f"Playwright browsers path does not exist: {browsers_path}")
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:200 - len(ext)] + ext
    
    return sanitized.strip()


def format_notebook_info(notebook: dict) -> str:
    """
    Format notebook info for display.
    
    Args:
        notebook: Notebook dict with id, title, sources_count, etc.
        
    Returns:
        Formatted string
    """
    lines = [
        f"📓 {notebook.get('title', 'Untitled')}",
        f"   ID: {notebook.get('id', 'unknown')}",
    ]
    
    if 'sources_count' in notebook:
        lines.append(f"   Sources: {notebook['sources_count']}")
    
    if 'created_at' in notebook:
        lines.append(f"   Created: {notebook['created_at']}")
    
    return '\n'.join(lines)


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def parse_notebook_id(url_or_id: str) -> str:
    """
    Extract notebook ID from URL or return ID as-is.
    
    Args:
        url_or_id: Notebook URL or ID
        
    Returns:
        Notebook ID
    """
    # Check if it's a URL
    if url_or_id.startswith('http'):
        # Extract UUID from URL
        import re
        match = re.search(r'notebook/([a-f0-9-]{36})', url_or_id)
        if match:
            return match.group(1)
    
    # Assume it's already an ID
    return url_or_id


def get_environment_info() -> dict:
    """
    Get information about the current environment.
    
    Returns:
        Dict with environment details
    """
    return {
        "playwright_browsers_path": os.getenv("PLAYWRIGHT_BROWSERS_PATH"),
        "python_env": str(config.python_env_dir),
        "base_dir": str(config.base_dir),
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "notebooklm_timeout": config.notebooklm_timeout,
        "notebooklm_headless": config.notebooklm_headless,
    }


def check_health() -> dict:
    """
    Perform health checks on the system.
    
    Returns:
        Dict with health status
    """
    checks = {
        "playwright_configured": False,
        "python_env_exists": False,
        "base_dir_exists": False,
        "config_dir_exists": False,
        "data_dir_exists": False,
        "logs_dir_exists": False,
    }
    
    # Check Playwright
    try:
        validate_playwright_config()
        checks["playwright_configured"] = True
    except PlaywrightNotConfiguredError:
        pass
    
    # Check directories
    checks["python_env_exists"] = config.python_env_dir.exists()
    checks["base_dir_exists"] = config.base_dir.exists()
    checks["config_dir_exists"] = config.config_dir.exists()
    checks["data_dir_exists"] = config.data_dir.exists()
    checks["logs_dir_exists"] = config.logs_dir.exists()
    
    # Overall status
    all_ok = all(checks.values())
    
    return {
        "status": "healthy" if all_ok else "degraded",
        "checks": checks,
        "all_healthy": all_ok,
    }
