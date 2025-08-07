"""API routes for cached tasks operations."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ...core.config import settings
from ...services.tasks_cache_v2 import tasks_cache_v2

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=list[dict[str, Any]])
async def get_tasks(
    project_id: str | None = Query(None, description="Filter by project ID"),
    force_refresh: bool = Query(False, description="Force refresh cache"),
) -> list[dict[str, Any]]:
    """Get cached tasks with optional filtering."""
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure Rocketlane API key and select a user in Settings.",
        )

    try:
        if project_id:
            tasks = await tasks_cache_v2.get_tasks_by_project(project_id, force_refresh=force_refresh)
        else:
            tasks = await tasks_cache_v2.get_all_tasks(force_refresh=force_refresh)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=dict[str, Any])
async def get_task_statistics() -> dict[str, Any]:
    """Get statistics about cached tasks."""
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure Rocketlane API key and select a user in Settings.",
        )

    try:
        all_tasks = await tasks_cache_v2.get_all_tasks()

        # Calculate statistics
        stats = {
            "total_tasks": len(all_tasks),
            "by_project": {},
            "by_status": {},
            "by_priority": {},
        }

        for task in all_tasks:
            # Group by project
            project = task.get("project", {})
            project_id = project.get("projectId", "unknown")
            project_name = project.get("projectName", "Unknown Project")
            if project_id not in stats["by_project"]:
                stats["by_project"][project_id] = {
                    "name": project_name,
                    "count": 0
                }
            stats["by_project"][project_id]["count"] += 1

            # Group by status
            status = task.get("status", {}).get("label", "Unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            # Group by priority
            priority = task.get("priority", {}).get("label", "No Priority") if task.get("priority") else "No Priority"
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache-status", response_model=dict[str, Any])
async def get_cache_status() -> dict[str, Any]:
    """Get current cache status information."""
    try:
        cache_stats = await tasks_cache_v2.get_stats()
        return cache_stats
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/{task_id}", response_model=dict[str, Any])
async def get_task(task_id: str) -> dict[str, Any]:
    """Get a specific task by ID from cache."""
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure Rocketlane API key and select a user in Settings.",
        )

    try:
        task = await tasks_cache_v2.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
