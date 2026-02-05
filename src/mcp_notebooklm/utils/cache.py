"""Caching utilities for MCP NotebookLM."""

import json
import time
from typing import Any, Optional, Dict
from pathlib import Path
from dataclasses import dataclass
from loguru import logger

from ..config import config


@dataclass
class CacheEntry:
    """Cache entry with timestamp and TTL."""
    data: Any
    timestamp: float
    ttl: int
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.timestamp > self.ttl
    
    @property
    def age(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.timestamp


class Cache:
    """Simple file-based cache for notebook data."""
    
    def __init__(self, cache_file: Optional[Path] = None, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            cache_file: Path to cache file (default: notebooks_cache.json)
            default_ttl: Default TTL in seconds (default: 5 minutes)
        """
        self.cache_file = cache_file or config.notebooks_cache_file
        self.default_ttl = default_ttl
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._load_from_disk()
    
    def _load_from_disk(self):
        """Load cache from disk file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                
                # Convert to CacheEntry objects
                for key, entry_data in data.items():
                    self._memory_cache[key] = CacheEntry(
                        data=entry_data.get('data'),
                        timestamp=entry_data.get('timestamp', 0),
                        ttl=entry_data.get('ttl', self.default_ttl)
                    )
                
                logger.debug(f"Loaded {len(self._memory_cache)} entries from cache")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
                self._memory_cache = {}
    
    def _save_to_disk(self):
        """Save cache to disk file."""
        try:
            # Filter out expired entries before saving
            valid_entries = {
                key: {
                    'data': entry.data,
                    'timestamp': entry.timestamp,
                    'ttl': entry.ttl
                }
                for key, entry in self._memory_cache.items()
                if not entry.is_expired
            }
            
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(valid_entries, f, indent=2)
            
            logger.debug(f"Saved {len(valid_entries)} entries to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        entry = self._memory_cache.get(key)
        
        if entry is None:
            return None
        
        if entry.is_expired:
            logger.debug(f"Cache entry expired: {key}")
            del self._memory_cache[key]
            return None
        
        logger.debug(f"Cache hit: {key} (age: {entry.age:.1f}s)")
        return entry.data
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if not specified)
        """
        ttl = ttl or self.default_ttl
        
        self._memory_cache[key] = CacheEntry(
            data=value,
            timestamp=time.time(),
            ttl=ttl
        )
        
        logger.debug(f"Cache set: {key} (ttl: {ttl}s)")
        self._save_to_disk()
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key existed and was deleted
        """
        if key in self._memory_cache:
            del self._memory_cache[key]
            self._save_to_disk()
            logger.debug(f"Cache deleted: {key}")
            return True
        return False
    
    def clear(self):
        """Clear all cache entries."""
        self._memory_cache.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """Remove all expired entries from cache."""
        expired_keys = [
            key for key, entry in self._memory_cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del self._memory_cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            self._save_to_disk()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = len(self._memory_cache)
        expired = sum(1 for entry in self._memory_cache.values() if entry.is_expired)
        valid = total - expired
        
        avg_age = 0
        if valid > 0:
            ages = [
                entry.age for entry in self._memory_cache.values()
                if not entry.is_expired
            ]
            avg_age = sum(ages) / len(ages)
        
        return {
            "total_entries": total,
            "valid_entries": valid,
            "expired_entries": expired,
            "average_age_seconds": round(avg_age, 1),
            "cache_file": str(self.cache_file),
            "default_ttl": self.default_ttl,
        }


# Global cache instance
_cache_instance: Optional[Cache] = None


def get_cache() -> Cache:
    """Get the global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = Cache()
    return _cache_instance


def cache_notebooks_list(func):
    """
    Decorator to cache notebook list results.
    
    Uses cache key 'notebooks_list' with 5 minute TTL.
    """
    async def wrapper(*args, **kwargs):
        cache = get_cache()
        
        # Check cache
        cached = cache.get('notebooks_list')
        if cached is not None:
            return cached
        
        # Fetch fresh data
        result = await func(*args, **kwargs)
        
        # Cache result
        cache.set('notebooks_list', result, ttl=300)
        
        return result
    
    return wrapper


def invalidate_notebooks_cache():
    """Invalidate the notebooks list cache."""
    cache = get_cache()
    cache.delete('notebooks_list')
    logger.info("Notebooks cache invalidated")
