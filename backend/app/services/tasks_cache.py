"""Tasks cache service for efficient task data management."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from ..core.cache import BaseCache, CacheConfig
from ..core.config import settings
from .project_cache_v2 import ProjectCacheService
from .rocketlane import RocketlaneClient

logger = logging.getLogger(__name__)


class TasksCache(BaseCache[dict[str, Any]]):
    """Cache service for user's tasks with efficient retrieval and filtering."""

    def __init__(self):
        # Configure cache with 5 minute TTL for tasks
        config = CacheConfig(
            cache_dir="/app/config/cache",  # Use absolute path in container
            default_ttl=300,  # 5 minutes
            stale_fallback=True,
            enable_background_refresh=True
        )
        super().__init__(config, "tasks")
        self.cache: dict[str, Any] = {}
        self.tasks_by_id: dict[str, dict[str, Any]] = {}
        self.tasks_by_project: dict[str, list[dict[str, Any]]] = {}
        self.last_update: datetime | None = None
        self.is_updating = False
        self.cache_ttl = timedelta(minutes=5)  # Cache validity period
        self.client = None

    def _get_client(self) -> RocketlaneClient:
        """Get or create Rocketlane client"""
        if not self.client:
            self.client = RocketlaneClient()
        return self.client

    def is_cache_fresh(self) -> bool:
        """Check if cache is still fresh."""
        if not self.last_update:
            return False
        return datetime.now(UTC) - self.last_update < self.cache_ttl

    async def get_tasks(
        self,
        project_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        force_refresh: bool = False
    ) -> list[dict[str, Any]]:
        """Get tasks from cache with optional filtering."""
        if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
            logger.error("Configuration incomplete for tasks cache")
            return []

        # Refresh cache if needed
        if force_refresh or not self.is_cache_fresh():
            if not self.is_updating:
                asyncio.create_task(self._update_cache())

            # If no cache available, wait for initial load
            if not self.cache:
                await self._update_cache()

        # Get all tasks from cache
        all_tasks = self.cache.get("tasks", [])

        # Apply filters
        filtered_tasks = all_tasks

        if project_id:
            filtered_tasks = [
                task for task in filtered_tasks
                if task.get("project", {}).get("projectId") == project_id
            ]

        if status:
            status_lower = status.lower()
            filtered_tasks = [
                task for task in filtered_tasks
                if task.get("status", {}).get("label", "").lower() == status_lower
            ]

        if priority:
            priority_lower = priority.lower()
            filtered_tasks = [
                task for task in filtered_tasks
                if (task.get("priority", {}).get("label", "No Priority").lower() == priority_lower)
            ]

        return filtered_tasks

    async def get_task_by_id(self, task_id: str) -> dict[str, Any] | None:
        """Get a specific task by ID from cache."""
        # Ensure cache is populated
        if not self.cache and not self.is_updating:
            await self._update_cache()

        return self.tasks_by_id.get(task_id)

    async def get_project_tasks(self, project_id: str) -> list[dict[str, Any]]:
        """Get all tasks for a specific project from cache."""
        # Ensure cache is populated
        if not self.cache and not self.is_updating:
            await self._update_cache()

        return self.tasks_by_project.get(project_id, [])

    async def search_tasks(self, query: str) -> list[dict[str, Any]]:
        """Search tasks by name or description."""
        # Ensure cache is populated
        if not self.cache and not self.is_updating:
            await self._update_cache()

        query_lower = query.lower()
        all_tasks = self.cache.get("tasks", [])

        return [
            task for task in all_tasks
            if (query_lower in task.get("taskName", "").lower() or
                query_lower in task.get("description", "").lower())
        ]

    async def get_task_statistics(self) -> dict[str, Any]:
        """Get statistics about cached tasks."""
        # Ensure cache is populated
        if not self.cache and not self.is_updating:
            await self._update_cache()

        all_tasks = self.cache.get("tasks", [])

        # Calculate statistics
        stats = {
            "total_tasks": len(all_tasks),
            "by_status": {},
            "by_priority": {},
            "by_type": {},
            "overdue_count": 0,
            "at_risk_count": 0,
            "due_this_week": 0,
        }

        today = datetime.now(UTC).date()
        week_end = today + timedelta(days=7)

        for task in all_tasks:
            # Status distribution
            status = task.get("status", {}).get("label", "Unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            # Priority distribution (for active tasks only)
            if status.lower() not in ["completed", "done", "closed"]:
                priority = task.get("priority", {}).get("label", "No Priority") if task.get("priority") else "No Priority"
                stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1

                # Check if at risk
                if task.get("atRisk", False):
                    stats["at_risk_count"] += 1

                # Check due dates
                due_date_str = task.get("dueDate")
                if due_date_str:
                    try:
                        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                        if due_date < today:
                            stats["overdue_count"] += 1
                        elif due_date <= week_end:
                            stats["due_this_week"] += 1
                    except:
                        pass

            # Type distribution
            task_type = task.get("type", "TASK")
            stats["by_type"][task_type] = stats["by_type"].get(task_type, 0) + 1

        return stats

    async def _update_cache(self):
        """Update the cache with fresh data from Rocketlane."""
        if self.is_updating:
            return

        self.is_updating = True
        logger.info(f"Updating tasks cache for user {settings.rocketlane_user_id}")

        try:
            client = RocketlaneClient(settings.rocketlane_api_key, settings.rocketlane_api_base_url)
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
                        logger.debug(f"Fetched {len(project_tasks)} tasks from project {project_id}")
                    except Exception as e:
                        logger.warning(f"Failed to fetch tasks for project {project_id}: {e}")

            logger.info(f"Fetched total of {len(all_tasks)} tasks from {len(user_projects)} projects")

            # Build indexes for efficient lookups
            tasks_by_id = {}
            tasks_by_project = {}

            for task in all_tasks:
                task_id = task.get("taskId")
                if task_id:
                    tasks_by_id[task_id] = task

                project_id = task.get("project", {}).get("projectId")
                if project_id:
                    if project_id not in tasks_by_project:
                        tasks_by_project[project_id] = []
                    tasks_by_project[project_id].append(task)

            # Update cache
            self.cache = {
                "tasks": all_tasks,
                "count": len(all_tasks),
                "last_updated": datetime.now(UTC).isoformat(),
            }
            self.tasks_by_id = tasks_by_id
            self.tasks_by_project = tasks_by_project
            self.last_update = datetime.now(UTC)

            logger.info(f"Tasks cache updated successfully with {len(all_tasks)} tasks")

        except Exception as e:
            logger.error(f"Failed to update tasks cache: {e}")
            # Keep existing cache on error
        finally:
            self.is_updating = False

    async def refresh_cache_periodically(self, interval: int = 300):
        """Refresh cache periodically in the background."""
        while True:
            try:
                await asyncio.sleep(interval)  # Default 5 minutes
                if not self.is_cache_fresh():
                    await self._update_cache()
            except Exception as e:
                logger.error(f"Error in periodic cache refresh: {e}")

    def get_cache_status(self) -> dict[str, Any]:
        """Get current cache status information."""
        status = "error"
        if self.is_updating:
            status = "updating"
        elif self.is_cache_fresh():
            status = "fresh"
        elif self.cache:
            status = "stale"

        return {
            "status": status,
            "last_updated": self.last_update.isoformat() if self.last_update else None,
            "task_count": len(self.cache.get("tasks", [])),
            "project_count": len(self.tasks_by_project),
            "ttl_seconds": self.cache_ttl.total_seconds(),
        }


# Global cache instance
tasks_cache = TasksCache()
