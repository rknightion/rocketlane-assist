"""Time entries cache service with disk persistence."""

import logging
from typing import Any

from ..core.cache import BaseCache, CacheConfig
from ..core.config import settings
from .rocketlane import RocketlaneClient

logger = logging.getLogger(__name__)


class TimeEntriesCache(BaseCache[list[dict[str, Any]]]):
    """Cache service for time entries with disk persistence."""

    def __init__(self):
        # Configure cache with 15 minute TTL for time entries
        config = CacheConfig(
            cache_dir="/app/config/cache",  # Use absolute path in container
            default_ttl=900,  # 15 minutes
            stale_fallback=True,
            enable_background_refresh=True
        )
        super().__init__(config, "time_entries")
        self.client = None

    def _get_client(self) -> RocketlaneClient:
        """Get or create Rocketlane client"""
        if not self.client:
            self.client = RocketlaneClient()
        return self.client

    async def fetch_entries_for_period(
        self,
        date_from: str,
        date_to: str,
        project_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Fetch time entries from Rocketlane API for a specific period."""
        if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
            logger.error("Configuration incomplete for time entries cache")
            return []

        logger.info(f"Fetching time entries for user {settings.rocketlane_user_id} from {date_from} to {date_to}")

        try:
            client = self._get_client()
            entries = await client.get_time_entries(
                user_id=settings.rocketlane_user_id,
                project_id=project_id,
                date_from=date_from,
                date_to=date_to,
            )
            logger.info(f"Fetched {len(entries)} time entries")
            return entries

        except Exception as e:
            logger.error(f"Failed to fetch time entries: {e}")
            raise

    async def get_entries(
        self,
        date_from: str,
        date_to: str,
        project_id: str | None = None,
        force_refresh: bool = False
    ) -> list[dict[str, Any]]:
        """Get time entries from cache."""
        # Create a cache key based on the query parameters
        cache_key = f"{date_from}_{date_to}"
        if project_id:
            cache_key += f"_{project_id}"
        cache_key += f"_user_{settings.rocketlane_user_id}"

        # Get from cache using BaseCache pattern
        entries = await self.get(
            key=cache_key,
            fetch_func=lambda: self.fetch_entries_for_period(date_from, date_to, project_id),
            force_refresh=force_refresh
        )
        return entries or []

    async def invalidate_period(self, date_from: str, date_to: str, project_id: str | None = None):
        """Invalidate cache for a specific period after adding/updating an entry."""
        cache_key = f"{date_from}_{date_to}"
        if project_id:
            cache_key += f"_{project_id}"
        cache_key += f"_user_{settings.rocketlane_user_id}"

        # Also invalidate the general cache without project filter
        general_key = f"{date_from}_{date_to}_user_{settings.rocketlane_user_id}"

        await self.invalidate(cache_key)
        if project_id:  # Only invalidate general key if we had a project filter
            await self.invalidate(general_key)

        logger.info(f"Invalidated time entries cache for period {date_from} to {date_to}")

    async def warm_cache(self, date_from: str, date_to: str):
        """Pre-populate the cache for a specific period (if not already cached)."""
        logger.info(f"Checking time entries cache for {date_from} to {date_to}...")
        try:
            # First try to get from existing cache
            entries = await self.get_entries(date_from, date_to, force_refresh=False)
            if entries:
                logger.info(f"Time entries cache already warm with {len(entries)} entries")
                return
            
            # Only fetch if cache is empty or expired
            logger.info(f"Warming time entries cache with fresh data for {date_from} to {date_to}...")
            await self.get_entries(date_from, date_to, force_refresh=True)
            logger.info("Time entries cache warmed successfully")
        except Exception as e:
            logger.error(f"Failed to warm time entries cache: {e}")


# Create a singleton instance
time_entries_cache = TimeEntriesCache()
