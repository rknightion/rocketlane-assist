import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from ...core.config import settings
from ...core.logging import get_logger
from ...services.project_cache_v2 import ProjectCacheService
from ...services.rocketlane import RocketlaneClient
from ...services.summarization import SummarizationService
from ..dependencies import verify_api_keys, verify_llm_api_key

router = APIRouter(prefix="/projects", tags=["projects"])
logger = get_logger(__name__)

# Initialize cache service
project_cache = ProjectCacheService()


@router.get("/", response_model=list[dict[str, Any]])
async def get_projects(
    force_refresh: bool = Query(False, description="Force refresh from API"),
    _: None = Depends(verify_api_keys)
):
    """Get all projects from cache or Rocketlane API, filtered by user membership if configured"""
    try:
        logger.info(f"Fetching projects (force_refresh={force_refresh})")

        # Get projects from cache or API
        if settings.rocketlane_user_id:
            # If user is configured, get filtered projects
            user_id = int(settings.rocketlane_user_id)
            projects = await project_cache.get_user_projects(user_id, force_refresh=force_refresh)
            logger.info(f"User {user_id} has access to {len(projects)} projects")
        else:
            # Get all projects
            projects = await project_cache.get_all_projects(force_refresh=force_refresh)
            logger.info(f"Returning all {len(projects)} projects")

        return projects

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching projects: {e}", exc_info=True)
        # Try to serve from stale cache if available
        try:
            if settings.rocketlane_user_id:
                user_id = int(settings.rocketlane_user_id)
                projects = await project_cache.get_user_projects(user_id, force_refresh=False)
            else:
                projects = await project_cache.get_all_projects(force_refresh=False)

            if projects:
                logger.warning(f"Serving {len(projects)} projects from cache due to API error")
                return projects
        except:
            pass

        raise HTTPException(status_code=502, detail="Unable to fetch projects. Please try again later.")


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    force_refresh: bool = Query(False, description="Force refresh from API"),
    _: None = Depends(verify_api_keys)
):
    """Get a specific project from cache or API"""
    try:
        logger.info(f"Fetching project {project_id} (force_refresh={force_refresh})")

        # Try to get from cache first
        project = await project_cache.get_project_details(project_id, force_refresh=force_refresh)

        if project:
            return project

        # If not in cache, fetch directly
        logger.info(f"Project {project_id} not in cache, fetching from API")
        client = RocketlaneClient()
        project = await client.get_project(project_id)

        # Add to cache for next time (trigger background refresh of all projects)
        if project:
            asyncio.create_task(project_cache.get_all_projects(force_refresh=True))

        return project
    except Exception as e:
        logger.error(f"Error fetching project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/tasks")
async def get_project_tasks(
    project_id: str, status: str | None = None, _: None = Depends(verify_api_keys)
):
    """Get tasks for a specific project"""
    try:
        logger.info(f"Fetching tasks for project {project_id} with status filter: {status}")
        client = RocketlaneClient()
        # Use the configured user ID to filter tasks
        user_id = settings.rocketlane_user_id if settings.rocketlane_user_id else None
        if user_id:
            logger.info(f"Filtering tasks for user ID: {user_id}")
        tasks = await client.get_project_tasks(project_id, status, user_id)
        logger.info(f"Retrieved {len(tasks)} tasks for project {project_id}")
        return tasks
    except Exception as e:
        logger.error(f"Error fetching tasks for project {project_id}: {e}", exc_info=True)
        # Provide more specific error message
        if "500" in str(e):
            raise HTTPException(
                status_code=502,
                detail="Unable to fetch tasks from Rocketlane API. The service may be experiencing issues."
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/summarize")
async def summarize_project_tasks(
    project_id: str, _: None = Depends(verify_api_keys), __: None = Depends(verify_llm_api_key)
):
    """Summarize outstanding tasks for a project"""
    try:
        service = SummarizationService()
        summary = await service.summarize_project_tasks(project_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/summarize/stream")
async def summarize_project_tasks_stream(
    project_id: str, _: None = Depends(verify_api_keys), __: None = Depends(verify_llm_api_key)
):
    """Stream summarization of outstanding tasks for a project"""
    try:
        service = SummarizationService()

        async def generate():
            # Send initial metadata
            metadata = await service.get_project_metadata(project_id)
            yield f"data: {json.dumps({'type': 'metadata', 'data': metadata})}\n\n"

            # Stream the summary
            async for chunk in service.summarize_project_tasks_stream(project_id):
                yield f"data: {json.dumps({'type': 'chunk', 'data': chunk})}\n\n"

            # Send completion signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable Nginx buffering
            }
        )
    except Exception as e:
        logger.error(f"Streaming summarization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/refresh")
async def refresh_project_cache(_: None = Depends(verify_api_keys)):
    """Force refresh of the project cache"""
    try:
        logger.info("Force refreshing project cache")
        projects = await project_cache.get_all_projects(force_refresh=True)

        return {
            "status": "success",
            "message": f"Cache refreshed with {len(projects)} projects",
            "projects_cached": len(projects),
        }
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats(_: None = Depends(verify_api_keys)):
    """Get cache statistics"""
    try:
        stats = await project_cache.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache")
async def invalidate_cache(_: None = Depends(verify_api_keys)):
    """Invalidate the entire project cache"""
    try:
        await project_cache.invalidate()
        return {
            "status": "success",
            "message": "Project cache invalidated"
        }
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
