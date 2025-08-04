from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ...services.rocketlane import RocketlaneClient
from ...services.summarization import SummarizationService
from ..dependencies import verify_api_keys

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=List[Dict[str, Any]])
async def get_projects(_: None = Depends(verify_api_keys)):
    """Get all projects from Rocketlane"""
    try:
        client = RocketlaneClient()
        projects = await client.get_projects()
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
    project_id: str, 
    status: str = None,
    _: None = Depends(verify_api_keys)
):
    """Get tasks for a specific project"""
    try:
        client = RocketlaneClient()
        tasks = await client.get_project_tasks(project_id, status)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/summarize")
async def summarize_project_tasks(
    project_id: str,
    _: None = Depends(verify_api_keys)
):
    """Summarize outstanding tasks for a project"""
    try:
        service = SummarizationService()
        summary = await service.summarize_project_tasks(project_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))