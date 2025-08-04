from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ...core.config import settings
from ...services.rocketlane import RocketlaneClient
from ...services.summarization import SummarizationService
from ...services.project_cache import ProjectCacheService
from ..dependencies import verify_api_keys

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[dict[str, Any]])
async def get_projects(_: None = Depends(verify_api_keys)):
    """Get all projects from Rocketlane, filtered by user membership if configured"""
    try:
        client = RocketlaneClient()
        projects = await client.get_projects()
        
        # If a user is configured, filter projects based on membership
        if settings.rocketlane_user_id:
            cache_service = ProjectCacheService()
            user_id = int(settings.rocketlane_user_id)
            
            # Get filtered projects where user is a member
            filtered_projects = cache_service.get_user_projects(user_id, projects)
            
            print(f"User {user_id} has access to {len(filtered_projects)} out of {len(projects)} projects")
            
            return filtered_projects
        
        # If no user configured, return all projects
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
async def get_project(project_id: str, _: None = Depends(verify_api_keys)):
    """Get a specific project"""
    try:
        client = RocketlaneClient()
        project = await client.get_project(project_id)
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/tasks")
async def get_project_tasks(
    project_id: str, status: str | None = None, _: None = Depends(verify_api_keys)
):
    """Get tasks for a specific project"""
    try:
        client = RocketlaneClient()
        # Use the configured user ID to filter tasks
        user_id = settings.rocketlane_user_id if settings.rocketlane_user_id else None
        tasks = await client.get_project_tasks(project_id, status, user_id)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/summarize")
async def summarize_project_tasks(project_id: str, _: None = Depends(verify_api_keys)):
    """Summarize outstanding tasks for a project"""
    try:
        service = SummarizationService()
        summary = await service.summarize_project_tasks(project_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/refresh")
async def refresh_project_cache(_: None = Depends(verify_api_keys)):
    """Force refresh of the project membership cache"""
    try:
        cache_service = ProjectCacheService()
        cache_service.clear_cache()
        
        # Fetch fresh project data
        client = RocketlaneClient()
        projects = await client.get_projects()
        
        # Update cache
        cache_service.update_project_cache(projects)
        
        return {
            "status": "success",
            "message": f"Cache refreshed with {len(projects)} projects",
            "projects_cached": len(projects)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
