"""API routes for timesheet management."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from ...core.config import settings
from ...services.rocketlane import RocketlaneClient
from ...services.time_entry_categories_cache import time_entry_categories_cache
from ...services.tasks_cache_v2 import tasks_cache_v2
from ...services.project_cache_v2 import ProjectCacheService

router = APIRouter(prefix="/timesheets", tags=["timesheets"])


class TimeEntryCreate(BaseModel):
    """Model for creating a time entry."""
    date: str  # YYYY-MM-DD format
    minutes: int
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    activity_name: Optional[str] = None
    notes: str = ""
    billable: bool = True
    category_id: Optional[str] = None


@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_time_entry_categories() -> List[Dict[str, Any]]:
    """Get all time entry categories from cache."""
    if not settings.rocketlane_api_key:
        raise HTTPException(
            status_code=403,
            detail="Rocketlane API key not configured. Please configure in Settings.",
        )
    
    try:
        categories = await time_entry_categories_cache.get_categories()
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=List[Dict[str, Any]])
async def get_timesheet_tasks(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
) -> List[Dict[str, Any]]:
    """Get all tasks available for time entry (all tasks from user's projects)."""
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure API key and select a user in Settings.",
        )
    
    try:
        # Get tasks from cache
        if project_id:
            tasks = await tasks_cache_v2.get_tasks_by_project(project_id)
        else:
            tasks = await tasks_cache_v2.get_all_tasks()
        
        # Format tasks for timesheet display
        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append({
                "taskId": task.get("taskId"),
                "taskName": task.get("taskName"),
                "project": task.get("project", {}),
                "status": task.get("status", {}),
                "priority": task.get("priority", {}),
                "type": task.get("type"),
                "dueDate": task.get("dueDate"),
                "assignees": task.get("assignees", []),
            })
        
        return formatted_tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects", response_model=List[Dict[str, Any]])
async def get_timesheet_projects() -> List[Dict[str, Any]]:
    """Get all projects the user is a member of for timesheet entry."""
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure API key and select a user in Settings.",
        )
    
    try:
        project_cache = ProjectCacheService()
        user_id = int(settings.rocketlane_user_id)
        projects = await project_cache.get_user_projects(user_id)
        
        # Format projects for timesheet display
        formatted_projects = []
        for project in projects:
            formatted_projects.append({
                "projectId": project.get("projectId"),
                "projectName": project.get("projectName"),
                "status": project.get("status", {}),
                "customer": project.get("customer", {}),
                "owner": project.get("owner", {}),
            })
        
        return formatted_projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entries", response_model=List[Dict[str, Any]])
async def get_time_entries(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
) -> List[Dict[str, Any]]:
    """Get time entries for the configured user."""
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure API key and select a user in Settings.",
        )
    
    # Default to current week if no dates provided
    if not date_from:
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        date_from = start_of_week.strftime("%Y-%m-%d")
    
    if not date_to:
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        date_to = end_of_week.strftime("%Y-%m-%d")
    
    try:
        client = RocketlaneClient()
        entries = await client.get_time_entries(
            user_id=settings.rocketlane_user_id,
            project_id=project_id,
            date_from=date_from,
            date_to=date_to,
        )
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entries", response_model=Dict[str, Any])
async def create_time_entry(entry: TimeEntryCreate) -> Dict[str, Any]:
    """Create a new time entry for the configured user."""
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure API key and select a user in Settings.",
        )
    
    # Validate that at least one source is provided
    if not entry.task_id and not entry.project_id and not entry.activity_name:
        raise HTTPException(
            status_code=400,
            detail="One of task_id, project_id, or activity_name must be provided",
        )
    
    # Validate minutes
    if entry.minutes <= 0:
        raise HTTPException(
            status_code=400,
            detail="Minutes must be greater than 0",
        )
    
    # Validate that total time for the day doesn't exceed 24 hours (1440 minutes)
    if entry.minutes > 1440:
        raise HTTPException(
            status_code=400,
            detail="Cannot log more than 24 hours (1440 minutes) in a single entry",
        )
    
    try:
        client = RocketlaneClient()
        result = await client.create_time_entry_v2(
            date=entry.date,
            minutes=entry.minutes,
            task_id=entry.task_id,
            project_id=entry.project_id,
            activity_name=entry.activity_name,
            notes=entry.notes,
            billable=entry.billable,
            category_id=entry.category_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/entries/{entry_id}", response_model=Dict[str, Any])
async def update_time_entry(
    entry_id: str,
    entry: TimeEntryCreate,
) -> Dict[str, Any]:
    """Update an existing time entry."""
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure API key and select a user in Settings.",
        )
    
    # For now, return not implemented
    # This would require implementing the update method in RocketlaneClient
    raise HTTPException(
        status_code=501,
        detail="Time entry update not yet implemented",
    )


@router.delete("/entries/{entry_id}")
async def delete_time_entry(entry_id: str) -> Dict[str, str]:
    """Delete a time entry."""
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure API key and select a user in Settings.",
        )
    
    # For now, return not implemented
    # This would require implementing the delete method in RocketlaneClient
    raise HTTPException(
        status_code=501,
        detail="Time entry deletion not yet implemented",
    )


@router.get("/summary", response_model=Dict[str, Any])
async def get_timesheet_summary(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
) -> Dict[str, Any]:
    """Get a summary of time entries for the specified period."""
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure API key and select a user in Settings.",
        )
    
    # Default to current week if no dates provided
    if not date_from:
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        date_from = start_of_week.strftime("%Y-%m-%d")
    
    if not date_to:
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        date_to = end_of_week.strftime("%Y-%m-%d")
    
    try:
        client = RocketlaneClient()
        entries = await client.get_time_entries(
            user_id=settings.rocketlane_user_id,
            date_from=date_from,
            date_to=date_to,
        )
        
        # Calculate summary statistics
        total_minutes = sum(entry.get("minutes", 0) or entry.get("durationInMinutes", 0) for entry in entries)
        total_hours = total_minutes / 60
        
        # Group by project
        by_project = {}
        for entry in entries:
            project = entry.get("project", {})
            project_id = project.get("projectId", "unknown")
            project_name = project.get("projectName", "Unknown Project")
            
            if project_id not in by_project:
                by_project[project_id] = {
                    "projectId": project_id,
                    "projectName": project_name,
                    "totalMinutes": 0,
                    "entries": 0,
                }
            
            by_project[project_id]["totalMinutes"] += entry.get("minutes", 0) or entry.get("durationInMinutes", 0)
            by_project[project_id]["entries"] += 1
        
        # Group by date
        by_date = {}
        for entry in entries:
            date = entry.get("date", entry.get("entryDate", "unknown"))
            
            if date not in by_date:
                by_date[date] = {
                    "date": date,
                    "totalMinutes": 0,
                    "entries": 0,
                }
            
            by_date[date]["totalMinutes"] += entry.get("minutes", 0) or entry.get("durationInMinutes", 0)
            by_date[date]["entries"] += 1
        
        return {
            "period": {
                "from": date_from,
                "to": date_to,
            },
            "totalHours": round(total_hours, 2),
            "totalMinutes": total_minutes,
            "entryCount": len(entries),
            "byProject": list(by_project.values()),
            "byDate": list(by_date.values()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))