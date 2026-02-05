"""Profile management for multi-account support."""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from loguru import logger


# Default profile name
DEFAULT_PROFILE = "default"


def get_profiles_base_dir() -> Path:
    """Get the base directory for all profiles.
    
    Uses NOTEBOOKLM_HOME if set, otherwise ~/.config/notebooklm-py/
    """
    home = os.environ.get("NOTEBOOKLM_HOME")
    if home:
        base = Path(home)
    else:
        base = Path.home() / ".config" / "notebooklm-py"
    
    profiles_dir = base / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    return profiles_dir


def get_current_profile_file() -> Path:
    """Get the path to the current profile marker file."""
    base = get_profiles_base_dir().parent
    return base / "current_profile"


def get_profile_metadata_path(name: str) -> Path:
    """Get the path to the profile metadata file."""
    return get_profile_dir(name) / "info.json"


def get_profile_metadata(name: str) -> Dict[str, Any]:
    """Get metadata for a profile.
    
    Returns:
        Dict containing metadata (email, display_name, etc.)
    """
    meta_path = get_profile_metadata_path(name)
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text())
        except Exception as e:
            logger.warning(f"Failed to read metadata for {name}: {e}")
    return {}


def update_profile_metadata(name: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Update metadata for a profile.
    
    Args:
        name: Profile name
        metadata: Dict of keys to update (merges with existing)
        
    Returns:
        Updated metadata dict
    """
    current_meta = get_profile_metadata(name)
    current_meta.update(metadata)
    
    meta_path = get_profile_metadata_path(name)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(current_meta, indent=2))
    
    return current_meta


def list_profiles() -> List[dict]:
    """List all available profiles with metadata.
    
    Returns:
        List of dicts with 'name', 'active', 'path', and metadata keys
    """
    profiles_dir = get_profiles_base_dir()
    current = get_current_profile()
    
    profiles = []
    if profiles_dir.exists():
        for item in profiles_dir.iterdir():
            if item.is_dir():
                meta = get_profile_metadata(item.name)
                profile_info = {
                    "name": item.name,
                    "active": item.name == current,
                    "path": str(item),
                    "email": meta.get("email"),
                    "display_name": meta.get("display_name"),
                    "description": meta.get("description")
                }
                profiles.append(profile_info)
    
    return sorted(profiles, key=lambda x: x["name"])


def get_current_profile() -> str:
    """Get the name of the currently active profile.
    
    Returns:
        Profile name (defaults to 'default')
    """
    marker_file = get_current_profile_file()
    if marker_file.exists():
        try:
            return marker_file.read_text().strip() or DEFAULT_PROFILE
        except Exception:
            pass
    return DEFAULT_PROFILE


def set_current_profile(name: str) -> None:
    """Set the currently active profile.
    
    Args:
        name: Profile name to activate
    """
    marker_file = get_current_profile_file()
    marker_file.parent.mkdir(parents=True, exist_ok=True)
    marker_file.write_text(name)
    logger.info(f"Active profile set to: {name}")


def get_profile_dir(name: str) -> Path:
    """Get the directory for a specific profile.
    
    Args:
        name: Profile name
        
    Returns:
        Path to profile directory
    """
    return get_profiles_base_dir() / name


def get_profile_storage_path(name: str) -> Path:
    """Get the storage_state.json path for a profile.
    
    Args:
        name: Profile name
        
    Returns:
        Path to storage_state.json
    """
    return get_profile_dir(name) / "storage_state.json"


def get_profile_browser_dir(name: str) -> Path:
    """Get the browser profile directory for a profile.
    
    Args:
        name: Profile name
        
    Returns:
        Path to browser profile directory
    """
    return get_profile_dir(name) / "browser_profile"


def create_profile(name: str) -> Path:
    """Create a new profile directory.
    
    Args:
        name: Profile name
        
    Returns:
        Path to created profile directory
        
    Raises:
        ValueError: If profile already exists
    """
    profile_dir = get_profile_dir(name)
    if profile_dir.exists():
        raise ValueError(f"Profile '{name}' already exists")
    
    profile_dir.mkdir(parents=True, mode=0o700)
    get_profile_browser_dir(name).mkdir(parents=True, mode=0o700)
    
    logger.info(f"Created profile: {name} at {profile_dir}")
    return profile_dir


def delete_profile(name: str) -> bool:
    """Delete a profile.
    
    Args:
        name: Profile name
        
    Returns:
        True if deleted successfully
        
    Raises:
        ValueError: If trying to delete active profile or default
    """
    if name == DEFAULT_PROFILE:
        raise ValueError("Cannot delete the default profile")
    
    current = get_current_profile()
    if name == current:
        raise ValueError(f"Cannot delete the active profile '{name}'. Switch to another profile first.")
    
    profile_dir = get_profile_dir(name)
    if not profile_dir.exists():
        raise ValueError(f"Profile '{name}' does not exist")
    
    import shutil
    shutil.rmtree(profile_dir)
    logger.info(f"Deleted profile: {name}")
    return True


def profile_exists(name: str) -> bool:
    """Check if a profile exists.
    
    Args:
        name: Profile name
        
    Returns:
        True if profile directory exists
    """
    return get_profile_dir(name).exists()


def ensure_default_profile() -> None:
    """Ensure the default profile exists."""
    default_dir = get_profile_dir(DEFAULT_PROFILE)
    if not default_dir.exists():
        create_profile(DEFAULT_PROFILE)
        set_current_profile(DEFAULT_PROFILE)
