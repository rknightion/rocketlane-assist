"""Enhanced tasks cache service with disk persistence."""

import asyncio
import logging
from typing import Any

from ..core.cache import BaseCache, CacheConfig
from ..core.config import settings
from .project_cache_v2 import ProjectCacheService
from .rocketlane import RocketlaneClient

logger = logging.getLogger(__name__)


class TasksCacheV2(BaseCache[dict[str, Any]]):
    """Cache service for user's tasks with disk persistence."""

    def __init__(self):
        # Configure cache with 1 hour TTL for tasks
        config = CacheConfig(
            cache_dir="/app/config/cache",  # Use absolute path in container
            default_ttl=3600,  # 1 hour
            stale_fallback=True,
            enable_background_refresh=True
        )
        super().__init__(config, "tasks")
        self.client = None

    def _get_client(self) -> RocketlaneClient:
        """Get or create Rocketlane client"""
        if not self.client:
            self.client = RocketlaneClient()
        return self.client

    async def fetch_data(self) -> dict[str, Any]:
        """Fetch tasks data from Rocketlane API."""
        if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
            logger.error("Configuration incomplete for tasks cache")
            return {"tasks": [], "count": 0}

        logger.info(f"Fetching tasks for user {settings.rocketlane_user_id}")

        try:
            client = self._get_client()
            project_cache = ProjectCacheService()

            # Get all projects the user is a member of
            user_id_int = int(settings.rocketlane_user_id)
            user_projects = await project_cache.get_user_projects(user_id_int)
            logger.info(f"User is a member of {len(user_projects)} projects")

            # Fetch ALL tasks from ALL projects the user is a member of
            # This is needed for timesheets - users can log time on any task in their projects
            all_tasks = []

            for project in user_projects:
                project_id = project.get("projectId")
                if project_id:
                    try:
                        # Get all tasks for this project (not filtered by assignee)
                        project_tasks = await client.get_tasks_by_project(project_id)
                        all_tasks.extend(project_tasks)
                        logger.info(f"Fetched {len(project_tasks)} tasks for project {project_id}")
                    except Exception as e:
                        logger.warning(f"Failed to fetch tasks for project {project_id}: {e}")

            logger.info(f"Fetched total of {len(all_tasks)} tasks from {len(user_projects)} projects")

            # Build indexes for efficient lookups
            tasks_by_id = {}
            tasks_by_project = {}

            for task in all_tasks:
                task_id = task.get("taskId")
                if task_id:
                    tasks_by_id[str(task_id)] = task

                project_id = task.get("project", {}).get("projectId")
                if project_id:
                    project_id_str = str(project_id)
                    if project_id_str not in tasks_by_project:
                        tasks_by_project[project_id_str] = []
                    tasks_by_project[project_id_str].append(task)

            # Return the cache data structure
            return {
                "tasks": all_tasks,
                "count": len(all_tasks),
                "tasks_by_id": tasks_by_id,
                "tasks_by_project": tasks_by_project,
            }

        except Exception as e:
            logger.error(f"Failed to fetch tasks: {e}")
            raise

    async def get_all_tasks(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Get all tasks from cache."""
        # Get from cache using BaseCache pattern
        cache_data = await self.get(
            key="all_tasks",
            fetch_func=self.fetch_data,
            force_refresh=force_refresh
        )
        if cache_data:
            return cache_data.get("tasks", [])
        return []

    async def get_tasks_by_project(self, project_id: str, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Get tasks for a specific project."""
        cache_data = await self.get(
            key="all_tasks",
            fetch_func=self.fetch_data,
            force_refresh=force_refresh
        )
        if cache_data:
            return cache_data.get("tasks_by_project", {}).get(str(project_id), [])
        return []

    async def get_task_by_id(self, task_id: str, force_refresh: bool = False) -> dict[str, Any] | None:
        """Get a specific task by ID."""
        cache_data = await self.get(
            key="all_tasks",
            fetch_func=self.fetch_data,
            force_refresh=force_refresh
        )
        if cache_data:
            return cache_data.get("tasks_by_id", {}).get(str(task_id))
        return None

    async def warm_cache(self):
        """Pre-populate the cache (if not already cached)."""
        logger.info("Checking tasks cache...")
        try:
            # First try to get from existing cache
            cache_data = await self.get(
                key="all_tasks",
                fetch_func=self.fetch_data,
                force_refresh=False
            )
            if cache_data:
                task_count = len(cache_data.get("tasks_by_id", {}))
                logger.info(f"Tasks cache already warm with {task_count} tasks")
                return
            
            # Only fetch if cache is empty or expired
            logger.info("Warming tasks cache with fresh data...")
            await self.get(
                key="all_tasks",
                fetch_func=self.fetch_data,
                force_refresh=True
            )
            logger.info("Tasks cache warmed successfully")
        except Exception as e:
            logger.error(f"Failed to warm tasks cache: {e}")

    async def refresh_cache_periodically(self, interval: int = 300):
        """Periodically refresh the cache."""
        while True:
            try:
                await asyncio.sleep(interval)
                logger.info("Refreshing tasks cache...")
                await self.get(
                    key="all_tasks",
                    fetch_func=self.fetch_data,
                    force_refresh=True
                )
            except Exception as e:
                logger.error(f"Error refreshing tasks cache: {e}")


# Create a singleton instance
tasks_cache_v2 = TasksCacheV2()
