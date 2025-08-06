"""Enhanced user statistics cache service with disk persistence."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import logging

from ..core.cache import BaseCache, CacheConfig
from ..core.config import settings
from .rocketlane import RocketlaneClient
from .project_cache_v2 import ProjectCacheService

logger = logging.getLogger(__name__)


class UserStatisticsCache(BaseCache[Dict[str, Any]]):
    """Cache service for user-specific statistics with disk persistence."""
    
    def __init__(self):
        # Configure cache with 5-minute TTL for statistics
        config = CacheConfig(
            cache_dir="/app/config/cache",  # Use absolute path in container
            default_ttl=300,  # 5 minutes
            stale_fallback=True,
            enable_background_refresh=True
        )
        super().__init__(config, "user_statistics")
        self.client = None
        
    def _get_client(self) -> RocketlaneClient:
        """Get or create Rocketlane client"""
        if not self.client:
            self.client = RocketlaneClient()
        return self.client
    
    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch user statistics from Rocketlane API."""
        if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
            logger.error("Configuration incomplete for user statistics")
            return {"error": "Configuration incomplete"}
            
        logger.info(f"Fetching statistics for user {settings.rocketlane_user_id}")
        
        try:
            client = self._get_client()
            
            # Fetch user info
            user = await client.get_user(settings.rocketlane_user_id)
            
            # Fetch only tasks assigned to the user (MUCH more efficient)
            all_tasks = await client.get_tasks(user_id=settings.rocketlane_user_id, limit=500)
            logger.info(f"Fetched {len(all_tasks)} tasks for user {settings.rocketlane_user_id}")
            
            # Debug logging for task analysis
            logger.debug(f"Sample task structure: {all_tasks[0] if all_tasks else 'No tasks'}")
            
            # Process tasks
            active_tasks = []
            completed_tasks = []
            overdue_tasks = []
            at_risk_tasks = []
            due_this_week = []
            user_projects = set()
            
            today = datetime.now(timezone.utc).date()
            week_end = today + timedelta(days=7)
            
            for task in all_tasks:
                # Collect project IDs
                project = task.get("project", {})
                if project.get("projectId"):
                    user_projects.add(project.get("projectId"))
                
                # Categorize by status
                status = task.get("status", {}).get("label", "").lower()
                logger.debug(f"Task {task.get('taskId')}: status={status}, atRisk={task.get('atRisk', False)}")
                
                if status in ["completed", "done", "closed"]:
                    completed_tasks.append(task)
                else:
                    active_tasks.append(task)
                    
                    # Check if at risk
                    if task.get("atRisk", False):
                        at_risk_tasks.append(task)
                    
                    # Check due dates
                    due_date_str = task.get("dueDate")
                    if due_date_str:
                        try:
                            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                            if due_date < today:
                                overdue_tasks.append(task)
                            elif due_date <= week_end:
                                due_this_week.append(task)
                        except:
                            pass
            
            # Calculate time logged this week
            start_of_week = today - timedelta(days=today.weekday())
            time_entries = await client.get_time_entries(
                user_id=settings.rocketlane_user_id,
                date_from=start_of_week.strftime("%Y-%m-%d"),
                date_to=today.strftime("%Y-%m-%d")
            )
            
            total_minutes_this_week = 0
            if time_entries:
                logger.debug(f"Time entries this week: {len(time_entries)}")
                for entry in time_entries:
                    # Handle different field names from API
                    minutes = entry.get("minutes", 0) or entry.get("durationInMinutes", 0)
                    total_minutes_this_week += minutes
                    logger.debug(f"Entry: {minutes} minutes on {entry.get('date', entry.get('entryDate'))}")
            
            hours_this_week = round(total_minutes_this_week / 60, 1)
            logger.info(f"Total time logged this week: {total_minutes_this_week} minutes ({hours_this_week} hours)")
            
            # Get project details
            user_project_count = len(user_projects)
            
            # Prefer using the project cache to get actual user projects
            try:
                project_cache = ProjectCacheService()
                user_id_int = int(settings.rocketlane_user_id)
                user_project_list = await project_cache.get_user_projects(user_id_int)
                user_project_count = len(user_project_list)
                logger.info(f"User is a member of {user_project_count} projects (from cache)")
            except Exception as e:
                logger.warning(f"Could not get projects from cache: {e}")
                # Use the count from tasks as fallback
            
            # Prepare response
            # Fix user data mapping based on actual API response
            first_name = user.get("firstName", "")
            last_name = user.get("lastName", "")
            
            statistics = {
                "user": {
                    "userId": user.get("userId"),
                    "fullName": f"{first_name} {last_name}".strip() or "Unknown User",
                    "emailId": user.get("email") or user.get("emailId", ""),
                },
                "statistics": {
                    "total_tasks": len(all_tasks),
                    "active_tasks": len(active_tasks),
                    "completed_tasks": len(completed_tasks),
                    "overdue_tasks": len(overdue_tasks),
                    "at_risk_tasks": len(at_risk_tasks),
                    "due_this_week": len(due_this_week),
                    "hours_logged_this_week": hours_this_week,
                    "projects_count": user_project_count,
                },
                "tasks": {
                    "active": active_tasks[:5],  # Return top 5 for display
                    "at_risk": at_risk_tasks[:5],
                    "due_this_week": due_this_week[:5],
                    "overdue": overdue_tasks[:5],
                },
            }
            
            logger.info(f"Statistics updated: {statistics['statistics']}")
            return statistics
            
        except Exception as e:
            logger.error(f"Failed to fetch user statistics: {e}")
            raise
    
    async def get_statistics(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get user statistics from cache."""
        # Get from cache using BaseCache pattern
        statistics = await self.get(
            key=f"user_{settings.rocketlane_user_id}_stats",
            fetch_func=self.fetch_data,
            force_refresh=force_refresh
        )
        
        if statistics:
            # Add cache metadata
            return {
                **statistics,
                "cache_status": "fresh" if not force_refresh else "refreshed",
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        
        return {
            "error": "Failed to fetch statistics",
            "cache_status": "error"
        }
    
    async def warm_cache(self):
        """Pre-populate the cache."""
        logger.info("Warming user statistics cache...")
        try:
            await self.get(
                key=f"user_{settings.rocketlane_user_id}_stats",
                fetch_func=self.fetch_data,
                force_refresh=True
            )
            logger.info("User statistics cache warmed successfully")
        except Exception as e:
            logger.error(f"Failed to warm user statistics cache: {e}")
    
    async def refresh_cache_periodically(self, interval: int = 300):
        """Periodically refresh the cache (default: 5 minutes)."""
        while True:
            try:
                await asyncio.sleep(interval)
                logger.info("Refreshing user statistics cache...")
                await self.get(
                    key=f"user_{settings.rocketlane_user_id}_stats",
                    fetch_func=self.fetch_data,
                    force_refresh=True
                )
            except Exception as e:
                logger.error(f"Error refreshing user statistics cache: {e}")


# Create a singleton instance
user_statistics_cache = UserStatisticsCache()