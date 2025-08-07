"""
Enhanced project caching service with retry logic and resilient fetching.
"""

import asyncio
from typing import Any

import httpx

from ..core.cache import BaseCache, CacheConfig
from .rocketlane import RocketlaneClient


class ProjectCacheService(BaseCache[list[dict[str, Any]]]):
    """Cache service for Rocketlane projects"""

    def __init__(self):
        # Configure cache with longer TTL for projects (1 day)
        config = CacheConfig(
            cache_dir="/app/config/cache",  # Use absolute path in container
            default_ttl=86400,  # 1 day
            stale_fallback=True,
            enable_background_refresh=True
        )
        super().__init__(config, "projects")
        self.client = None
        self.fetch_timeout = 30.0  # Increased timeout for bulk fetches

    def _get_client(self) -> RocketlaneClient:
        """Get or create Rocketlane client"""
        if not self.client:
            self.client = RocketlaneClient()
        return self.client

    async def _fetch_projects_with_retry(self) -> list[dict[str, Any]]:
        """Fetch all projects with retry logic and proper pagination handling"""
        max_retries = 3
        retry_delay = 2.0

        for attempt in range(max_retries):
            try:
                return await self._fetch_projects_impl()
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 10)  # Exponential backoff
                else:
                    self.logger.error(f"All {max_retries} attempts failed")
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error fetching projects: {e}")
                raise

    async def _fetch_projects_impl(self) -> list[dict[str, Any]]:
        """Implementation of project fetching logic"""
        client = self._get_client()
        all_projects = []
        page_token = None
        page_count = 0
        max_pages = 20  # Safety limit

        # Create a custom httpx client with longer timeout
        async with httpx.AsyncClient(timeout=httpx.Timeout(self.fetch_timeout)) as http_client:
            while page_count < max_pages:
                try:
                    params = {"pageSize": 100}
                    if page_token:
                        params["pageToken"] = page_token

                    url = f"{client.base_url}/projects"
                    self.logger.info(f"Fetching projects page {page_count + 1} (token: {page_token})")

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
                        continue

                    response.raise_for_status()
                    data = response.json()

                    # Handle different response structures
                    if isinstance(data, list):
                        all_projects.extend(data)
                        break  # No pagination
                    elif "data" in data:
                        all_projects.extend(data["data"])

                        # Check for pagination
                        pagination = data.get("pagination", {})
                        if not pagination.get("hasMore", False):
                            break
                        page_token = pagination.get("nextPageToken")

                        if not page_token:
                            break
                    elif "projects" in data:
                        all_projects.extend(data["projects"])
                        break  # Assume no pagination
                    else:
                        self.logger.warning(f"Unexpected response structure: {data.keys()}")
                        break

                    page_count += 1

                    # Small delay between pages to avoid rate limiting
                    if page_token:
                        await asyncio.sleep(0.5)

                except httpx.TimeoutException as e:
                    self.logger.error(f"Timeout fetching projects page {page_count + 1}: {e}")
                    if page_count > 0:
                        # We have some data, return what we have
                        self.logger.warning(f"Returning partial results: {len(all_projects)} projects")
                        return all_projects
                    raise
                except Exception as e:
                    self.logger.error(f"Error fetching projects page {page_count + 1}: {e}")
                    if page_count > 0:
                        # We have some data, return what we have
                        self.logger.warning(f"Returning partial results: {len(all_projects)} projects")
                        return all_projects
                    raise

        self.logger.info(f"Successfully fetched {len(all_projects)} projects in {page_count} pages")
        return all_projects

    async def get_all_projects(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Get all projects from cache or API"""
        return await self.get(
            key="all_projects",
            fetch_func=self._fetch_projects_with_retry,
            force_refresh=force_refresh
        ) or []

    async def get_user_projects(
        self,
        user_id: int,
        force_refresh: bool = False
    ) -> list[dict[str, Any]]:
        """Get projects where user is a member"""
        # Get all projects
        all_projects = await self.get_all_projects(force_refresh)

        # Filter projects where user is a team member
        user_projects = []
        for project in all_projects:
            # Check teamMembers field (this is what the API returns)
            team_members = project.get("teamMembers", {})
            if team_members:
                member_list = team_members.get("members", [])
                # Check if user is in the members list
                if any(member.get("userId") == user_id for member in member_list):
                    user_projects.append(project)

        self.logger.info(f"User {user_id} is a member of {len(user_projects)} out of {len(all_projects)} projects")
        return user_projects

    async def warm_cache(self):
        """Pre-warm the cache with project data (if not already cached)"""
        try:
            self.logger.info("Checking project cache...")
            # First try to get from existing cache (don't force refresh)
            projects = await self.get_all_projects(force_refresh=False)
            if projects:
                self.logger.info(f"Project cache already warm with {len(projects)} projects")
                return True
            
            # Only fetch if cache is empty or expired
            self.logger.info("Warming project cache with fresh data...")
            projects = await self.get_all_projects(force_refresh=True)
            self.logger.info(f"Cache warmed with {len(projects)} projects")
            return True
        except Exception as e:
            import traceback
            self.logger.error(f"Failed to warm cache: {e}")
            self.logger.error(f"Full traceback:\n{traceback.format_exc()}")
            return False

    async def refresh_cache_periodically(self, interval: int = 1800):
        """Refresh cache periodically in background (default: 30 minutes)"""
        while True:
            try:
                await asyncio.sleep(interval)
                self.logger.info("Starting periodic cache refresh...")
                await self.get_all_projects(force_refresh=True)
            except Exception as e:
                self.logger.error(f"Periodic cache refresh failed: {e}")

    def get_project_by_id(
        self,
        project_id: str,
        projects: list[dict[str, Any]] | None = None
    ) -> dict[str, Any] | None:
        """Get a specific project by ID from cached list"""
        if projects is None:
            # This is a sync method, caller should provide projects
            return None

        for project in projects:
            if str(project.get("projectId")) == str(project_id):
                return project
        return None

    async def get_project_details(
        self,
        project_id: str,
        force_refresh: bool = False
    ) -> dict[str, Any] | None:
        """Get detailed project information"""
        # First try to get from cached list
        all_projects = await self.get_all_projects(force_refresh)
        project = self.get_project_by_id(project_id, all_projects)

        if project:
            return project

        # If not found in cache, fetch directly (might be a new project)
        try:
            client = self._get_client()
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as http_client:
                response = await http_client.get(
                    f"{client.base_url}/projects/{project_id}",
                    headers=client.headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching project {project_id}: {e}")
            return None
