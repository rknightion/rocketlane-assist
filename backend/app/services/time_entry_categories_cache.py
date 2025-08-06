"""Enhanced time entry categories cache service with disk persistence."""

import asyncio
from typing import Any, Dict, List, Optional
import logging

from ..core.cache import BaseCache, CacheConfig
from ..core.config import settings
from .rocketlane import RocketlaneClient

logger = logging.getLogger(__name__)


class TimeEntryCategoriesCache(BaseCache[List[Dict[str, Any]]]):
    """Cache service for time entry categories with disk persistence."""
    
    def __init__(self):
        # Configure cache with 24-hour TTL for categories (they rarely change)
        config = CacheConfig(
            cache_dir="/app/config/cache",  # Use absolute path in container
            default_ttl=86400,  # 24 hours
            stale_fallback=True,
            enable_background_refresh=True
        )
        super().__init__(config, "time_entry_categories")
        self.client = None
        
    def _get_client(self) -> RocketlaneClient:
        """Get or create Rocketlane client"""
        if not self.client:
            self.client = RocketlaneClient()
        return self.client
    
    async def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch time entry categories from Rocketlane API."""
        if not settings.rocketlane_api_key:
            logger.error("Rocketlane API key not configured")
            return []
            
        logger.info("Fetching time entry categories from Rocketlane")
        
        try:
            client = self._get_client()
            categories = await client.get_time_entry_categories()
            logger.info(f"Fetched {len(categories)} time entry categories")
            return categories
            
        except Exception as e:
            logger.error(f"Failed to fetch time entry categories: {e}")
            raise
    
    async def get_categories(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get time entry categories from cache."""
        # Get from cache using BaseCache pattern
        categories = await self.get(
            key="all_categories",
            fetch_func=self.fetch_data,
            force_refresh=force_refresh
        )
        return categories or []
    
    async def get_category_by_id(self, category_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Get a specific category by ID."""
        categories = await self.get_categories(force_refresh=force_refresh)
        for category in categories:
            if str(category.get("id")) == str(category_id) or str(category.get("categoryId")) == str(category_id):
                return category
        return None
    
    async def get_category_by_name(self, name: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Get a specific category by name."""
        categories = await self.get_categories(force_refresh=force_refresh)
        name_lower = name.lower()
        for category in categories:
            if category.get("name", "").lower() == name_lower or category.get("categoryName", "").lower() == name_lower:
                return category
        return None
    
    async def warm_cache(self):
        """Pre-populate the cache."""
        logger.info("Warming time entry categories cache...")
        try:
            await self.get(
                key="all_categories",
                fetch_func=self.fetch_data,
                force_refresh=True
            )
            logger.info("Time entry categories cache warmed successfully")
        except Exception as e:
            logger.error(f"Failed to warm time entry categories cache: {e}")
    
    async def refresh_cache_periodically(self, interval: int = 86400):
        """Periodically refresh the cache (default: 24 hours)."""
        while True:
            try:
                await asyncio.sleep(interval)
                logger.info("Refreshing time entry categories cache...")
                await self.get(
                    key="all_categories",
                    fetch_func=self.fetch_data,
                    force_refresh=True
                )
            except Exception as e:
                logger.error(f"Error refreshing time entry categories cache: {e}")


# Create a singleton instance
time_entry_categories_cache = TimeEntryCategoriesCache()