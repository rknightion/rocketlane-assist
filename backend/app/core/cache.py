"""
Generic caching framework for filesystem-based caching with TTL support.
"""

import json
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, TypeVar, Generic
from functools import lru_cache
import hashlib
import asyncio
from contextlib import asynccontextmanager

from .logging import get_logger

T = TypeVar("T")

class CacheConfig:
    """Configuration for cache behavior"""
    def __init__(
        self,
        cache_dir: str = "./config/cache",
        default_ttl: int = 3600,  # 1 hour
        stale_fallback: bool = True,  # Use stale cache if API fails
        memory_cache_size: int = 128,  # LRU cache size
        enable_background_refresh: bool = True,
    ):
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self.stale_fallback = stale_fallback
        self.memory_cache_size = memory_cache_size
        self.enable_background_refresh = enable_background_refresh
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)


class CacheEntry(Generic[T]):
    """Represents a cached entry with metadata"""
    def __init__(self, data: T, ttl: int = 3600):
        self.data = data
        self.timestamp = time.time()
        self.ttl = ttl
        self.expires_at = self.timestamp + ttl
        
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() > self.expires_at
    
    def is_stale(self, stale_threshold: int = 1800) -> bool:
        """Check if cache entry is stale (half of TTL by default)"""
        age = time.time() - self.timestamp
        return age > (self.ttl - stale_threshold)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "data": self.data,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "expires_at": self.expires_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        """Create from dictionary"""
        entry = cls(data["data"], data["ttl"])
        entry.timestamp = data["timestamp"]
        entry.expires_at = data["expires_at"]
        return entry


class BaseCache(ABC, Generic[T]):
    """Abstract base class for caching implementations"""
    
    def __init__(self, config: CacheConfig, cache_name: str):
        self.config = config
        self.cache_name = cache_name
        self.logger = get_logger(f"cache.{cache_name}")
        self.cache_file = self.config.cache_dir / f"{cache_name}.json"
        self.lock_file = self.config.cache_dir / f"{cache_name}.lock"
        self._memory_cache: dict[str, CacheEntry[T]] = {}
        self._refresh_tasks: dict[str, asyncio.Task] = {}
        
    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        key_data = f"{args}{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @asynccontextmanager
    async def _file_lock(self, timeout: float = 5.0):
        """Async context manager for file locking"""
        start_time = time.time()
        lock_acquired = False
        
        try:
            while time.time() - start_time < timeout:
                try:
                    # Try to create lock file atomically
                    self.lock_file.touch(exist_ok=False)
                    lock_acquired = True
                    break
                except FileExistsError:
                    await asyncio.sleep(0.1)
            
            if not lock_acquired:
                self.logger.warning(f"Failed to acquire lock for {self.cache_name}")
            
            yield lock_acquired
            
        finally:
            if lock_acquired:
                try:
                    self.lock_file.unlink()
                except FileNotFoundError:
                    pass
    
    async def _read_cache_file(self) -> dict[str, CacheEntry[T]]:
        """Read cache from filesystem"""
        if not self.cache_file.exists():
            return {}
        
        async with self._file_lock():
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                    return {
                        key: CacheEntry.from_dict(entry)
                        for key, entry in data.items()
                    }
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                self.logger.error(f"Error reading cache file: {e}")
                return {}
    
    async def _write_cache_file(self, cache_data: dict[str, CacheEntry[T]]):
        """Write cache to filesystem"""
        async with self._file_lock() as locked:
            if not locked:
                self.logger.warning("Could not acquire lock for writing cache")
                return
            
            try:
                # Write to temp file first, then rename (atomic operation)
                temp_file = self.cache_file.with_suffix(".tmp")
                with open(temp_file, "w") as f:
                    json.dump(
                        {key: entry.to_dict() for key, entry in cache_data.items()},
                        f,
                        indent=2,
                        default=str
                    )
                temp_file.replace(self.cache_file)
            except Exception as e:
                self.logger.error(f"Error writing cache file: {e}")
    
    async def get(
        self,
        key: str,
        fetch_func: Optional[callable] = None,
        ttl: Optional[int] = None,
        force_refresh: bool = False
    ) -> Optional[T]:
        """
        Get item from cache or fetch if needed
        
        Args:
            key: Cache key
            fetch_func: Async function to fetch data if cache miss
            ttl: Override default TTL
            force_refresh: Force refresh even if cache is valid
        """
        ttl = ttl or self.config.default_ttl
        
        # Check memory cache first
        if not force_refresh and key in self._memory_cache:
            entry = self._memory_cache[key]
            if not entry.is_expired():
                self.logger.debug(f"Memory cache hit for {key}")
                
                # Check if stale and trigger background refresh
                if entry.is_stale() and self.config.enable_background_refresh and fetch_func:
                    asyncio.create_task(self._background_refresh(key, fetch_func, ttl))
                
                return entry.data
        
        # Check filesystem cache
        if not force_refresh:
            file_cache = await self._read_cache_file()
            if key in file_cache:
                entry = file_cache[key]
                if not entry.is_expired():
                    self.logger.debug(f"File cache hit for {key}")
                    self._memory_cache[key] = entry
                    
                    # Check if stale and trigger background refresh
                    if entry.is_stale() and self.config.enable_background_refresh and fetch_func:
                        asyncio.create_task(self._background_refresh(key, fetch_func, ttl))
                    
                    return entry.data
                elif self.config.stale_fallback:
                    # Keep stale entry as fallback
                    self._memory_cache[key] = entry
        
        # Cache miss or expired - fetch new data
        if fetch_func:
            try:
                self.logger.info(f"Cache miss for {key}, fetching fresh data")
                data = await fetch_func()
                await self.set(key, data, ttl)
                return data
            except Exception as e:
                import traceback
                self.logger.error(f"Error fetching data for {key}: {e}")
                self.logger.error(f"Full traceback:\n{traceback.format_exc()}")
                
                # Fall back to stale cache if available and configured
                if self.config.stale_fallback and key in self._memory_cache:
                    self.logger.warning(f"Using stale cache for {key} due to fetch error")
                    return self._memory_cache[key].data
                
                raise
        
        return None
    
    async def set(self, key: str, data: T, ttl: Optional[int] = None):
        """Set item in cache"""
        ttl = ttl or self.config.default_ttl
        entry = CacheEntry(data, ttl)
        
        # Update memory cache
        self._memory_cache[key] = entry
        
        # Update filesystem cache
        file_cache = await self._read_cache_file()
        file_cache[key] = entry
        await self._write_cache_file(file_cache)
        
        self.logger.debug(f"Cached {key} with TTL {ttl}s")
    
    async def invalidate(self, key: Optional[str] = None):
        """Invalidate cache entry or entire cache"""
        if key:
            # Invalidate specific key
            self._memory_cache.pop(key, None)
            file_cache = await self._read_cache_file()
            file_cache.pop(key, None)
            await self._write_cache_file(file_cache)
            self.logger.info(f"Invalidated cache key: {key}")
        else:
            # Invalidate entire cache
            self._memory_cache.clear()
            if self.cache_file.exists():
                self.cache_file.unlink()
            self.logger.info(f"Invalidated entire {self.cache_name} cache")
    
    async def _background_refresh(self, key: str, fetch_func: callable, ttl: int):
        """Refresh cache entry in background"""
        # Cancel any existing refresh task for this key
        if key in self._refresh_tasks:
            self._refresh_tasks[key].cancel()
        
        try:
            self.logger.debug(f"Starting background refresh for {key}")
            data = await fetch_func()
            await self.set(key, data, ttl)
            self.logger.debug(f"Background refresh completed for {key}")
        except Exception as e:
            self.logger.error(f"Background refresh failed for {key}: {e}")
        finally:
            self._refresh_tasks.pop(key, None)
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        file_cache = await self._read_cache_file()
        
        total_entries = len(file_cache)
        expired_entries = sum(1 for entry in file_cache.values() if entry.is_expired())
        stale_entries = sum(1 for entry in file_cache.values() if entry.is_stale() and not entry.is_expired())
        
        return {
            "cache_name": self.cache_name,
            "total_entries": total_entries,
            "memory_entries": len(self._memory_cache),
            "expired_entries": expired_entries,
            "stale_entries": stale_entries,
            "cache_file_size": self.cache_file.stat().st_size if self.cache_file.exists() else 0,
        }
    
    @abstractmethod
    async def warm_cache(self):
        """Warm the cache with initial data - implement in subclasses"""
        pass