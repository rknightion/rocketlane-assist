"""
User caching service with retry logic and resilient fetching.
"""

import asyncio
from typing import Any, Optional
import httpx

from ..core.cache import BaseCache, CacheConfig
from ..core.config import settings
from ..core.logging import get_logger
from .rocketlane import RocketlaneClient


class UserCacheService(BaseCache[list[dict[str, Any]]]):
    """Cache service for Rocketlane users"""
    
    def __init__(self):
        # Configure cache with longer TTL for users (2 hours - users change less frequently)
        config = CacheConfig(
            cache_dir="/app/config/cache",  # Use absolute path in container
            default_ttl=7200,  # 2 hours
            stale_fallback=True,
            enable_background_refresh=True
        )
        super().__init__(config, "users")
        self.client = None
        self.fetch_timeout = 15.0  # Timeout for user fetches
        
    def _get_client(self) -> RocketlaneClient:
        """Get or create Rocketlane client"""
        if not self.client:
            self.client = RocketlaneClient()
        return self.client
    
    async def _fetch_users_with_retry(self) -> list[dict[str, Any]]:
        """Fetch all users with retry logic"""
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                return await self._fetch_users_impl()
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 10)  # Exponential backoff
                else:
                    self.logger.error(f"All {max_retries} attempts failed")
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error fetching users: {e}")
                raise
    
    async def _fetch_users_impl(self) -> list[dict[str, Any]]:
        """Implementation of user fetching logic"""
        client = self._get_client()
        
        # Create a custom httpx client with timeout
        async with httpx.AsyncClient(timeout=httpx.Timeout(self.fetch_timeout)) as http_client:
            try:
                params = {"pageSize": 200}  # Users are typically fewer than projects
                url = f"{client.base_url}/users"
                
                self.logger.info("Fetching users from Rocketlane API")
                
                response = await http_client.get(
                    url,
                    headers=client.headers,
                    params=params
                )
                
                # Check for specific error conditions
                if response.status_code == 401:
                    raise ValueError("Invalid Rocketlane API key")
                elif response.status_code == 403:
                    raise ValueError("Access forbidden - check API key permissions")
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    raise httpx.NetworkError("Rate limited")
                
                response.raise_for_status()
                data = response.json()
                
                # Handle different response structures
                if isinstance(data, list):
                    users = data
                elif "data" in data:
                    users = data["data"]
                elif "users" in data:
                    users = data["users"]
                else:
                    users = []
                
                self.logger.info(f"Successfully fetched {len(users)} users")
                return users
                
            except httpx.TimeoutException as e:
                self.logger.error(f"Timeout fetching users: {e}")
                raise
            except Exception as e:
                self.logger.error(f"Error fetching users: {e}")
                raise
    
    async def get_all_users(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Get all users from cache or API"""
        return await self.get(
            key="all_users",
            fetch_func=self._fetch_users_with_retry,
            force_refresh=force_refresh
        ) or []
    
    async def get_user_by_id(
        self,
        user_id: int,
        force_refresh: bool = False
    ) -> Optional[dict[str, Any]]:
        """Get a specific user by ID"""
        users = await self.get_all_users(force_refresh)
        for user in users:
            if user.get("userId") == user_id:
                return user
        return None
    
    async def get_user_by_email(
        self,
        email: str,
        force_refresh: bool = False
    ) -> Optional[dict[str, Any]]:
        """Get a specific user by email"""
        users = await self.get_all_users(force_refresh)
        for user in users:
            if user.get("emailId", "").lower() == email.lower():
                return user
        return None
    
    async def warm_cache(self):
        """Pre-warm the cache with user data"""
        try:
            self.logger.info("Warming user cache...")
            users = await self.get_all_users(force_refresh=True)
            self.logger.info(f"Cache warmed with {len(users)} users")
            return True
        except Exception as e:
            self.logger.error(f"Failed to warm user cache: {e}")
            return False
    
    async def refresh_cache_periodically(self, interval: int = 3600):
        """Refresh cache periodically in background (default: 1 hour)"""
        while True:
            try:
                await asyncio.sleep(interval)
                self.logger.info("Starting periodic user cache refresh...")
                await self.get_all_users(force_refresh=True)
            except Exception as e:
                self.logger.error(f"Periodic user cache refresh failed: {e}")