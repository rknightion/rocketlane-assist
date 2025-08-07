"""API routes for timesheet management."""

import base64
import json
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from ...core.config import settings
from ...core.llm import get_llm_provider
from ...services.project_cache_v2 import ProjectCacheService
from ...services.rocketlane import RocketlaneClient
from ...services.tasks_cache_v2 import tasks_cache_v2
from ...services.time_entries_cache import time_entries_cache
from ...services.time_entry_categories_cache import time_entry_categories_cache

router = APIRouter(prefix="/timesheets", tags=["timesheets"])


class TimeEntryCreate(BaseModel):
    """Model for creating a time entry."""
    date: str  # YYYY-MM-DD format
    minutes: int
    task_id: str | None = None
    project_id: str | None = None
    activity_name: str | None = None
    notes: str = ""
    billable: bool = True
    category_id: str | None = None


@router.get("/categories", response_model=list[dict[str, Any]])
async def get_time_entry_categories() -> list[dict[str, Any]]:
    """Get all time entry categories from cache."""
    if not settings.rocketlane_api_key:
        raise HTTPException(
            status_code=403,
            detail="Rocketlane API key not configured. Please configure in Settings.",
        )

    try:
        categories = await time_entry_categories_cache.get_categories()
        # Transform to match frontend expectations
        formatted_categories = []
        for category in categories:
            formatted_categories.append({
                "id": str(category.get("categoryId")),
                "name": category.get("categoryName"),
            })
        return formatted_categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=list[dict[str, Any]])
async def get_timesheet_tasks(
    project_id: str | None = Query(None, description="Filter by project ID"),
) -> list[dict[str, Any]]:
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


@router.get("/projects", response_model=list[dict[str, Any]])
async def get_timesheet_projects() -> list[dict[str, Any]]:
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


@router.get("/entries", response_model=list[dict[str, Any]])
async def get_time_entries(
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    project_id: str | None = Query(None, description="Filter by project ID"),
) -> list[dict[str, Any]]:
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
        # Get entries from cache
        entries = await time_entries_cache.get_entries(
            date_from=date_from,
            date_to=date_to,
            project_id=project_id,
            force_refresh=False
        )
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entries", response_model=dict[str, Any])
async def create_time_entry(
    entry: TimeEntryCreate,
    date_from: str | None = Query(None, description="Start date for cache invalidation"),
    date_to: str | None = Query(None, description="End date for cache invalidation"),
) -> dict[str, Any]:
    """Create a new time entry for the configured user."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Creating time entry with data: {entry.model_dump()}")
    
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure API key and select a user in Settings.",
        )

    # Validate that at least one source is provided
    if not entry.task_id and not entry.project_id and not entry.activity_name:
        logger.error(f"Validation failed - no task_id, project_id, or activity_name provided. Entry data: {entry.model_dump()}")
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

        # Invalidate cache - use provided dates or calculate week
        if date_from and date_to:
            # Use the provided date range (consistent with delete endpoint)
            await time_entries_cache.invalidate_period(
                date_from=date_from,
                date_to=date_to,
                project_id=entry.project_id
            )
        else:
            # Fall back to calculating the week containing this entry
            entry_date = datetime.strptime(entry.date, "%Y-%m-%d")
            start_of_week = entry_date - timedelta(days=entry_date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            await time_entries_cache.invalidate_period(
                date_from=start_of_week.strftime("%Y-%m-%d"),
                date_to=end_of_week.strftime("%Y-%m-%d"),
                project_id=entry.project_id
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/entries/{entry_id}", response_model=dict[str, Any])
async def update_time_entry(
    entry_id: str,
    entry: TimeEntryCreate,
    date_from: str | None = Query(None, description="Start date for cache invalidation"),
    date_to: str | None = Query(None, description="End date for cache invalidation"),
) -> dict[str, Any]:
    """Update an existing time entry."""
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure API key and select a user in Settings.",
        )

    # Validate input
    if entry.minutes <= 0:
        raise HTTPException(
            status_code=400,
            detail="Minutes must be greater than 0",
        )

    if entry.minutes > 1440:
        raise HTTPException(
            status_code=400,
            detail="Cannot log more than 24 hours (1440 minutes) in a single entry",
        )

    try:
        client = RocketlaneClient()
        result = await client.update_time_entry(
            entry_id=entry_id,
            date=entry.date,
            minutes=entry.minutes,
            task_id=entry.task_id,
            project_id=entry.project_id,
            activity_name=entry.activity_name,
            notes=entry.notes,
            billable=entry.billable,
            category_id=entry.category_id,
        )

        # Invalidate cache - use provided dates or calculate week
        if date_from and date_to:
            # Use the provided date range (consistent with delete endpoint)
            await time_entries_cache.invalidate_period(
                date_from=date_from,
                date_to=date_to,
                project_id=entry.project_id
            )
        else:
            # Fall back to calculating the week containing this entry
            entry_date = datetime.strptime(entry.date, "%Y-%m-%d")
            start_of_week = entry_date - timedelta(days=entry_date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            await time_entries_cache.invalidate_period(
                date_from=start_of_week.strftime("%Y-%m-%d"),
                date_to=end_of_week.strftime("%Y-%m-%d"),
                project_id=entry.project_id
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/entries/{entry_id}")
async def delete_time_entry(
    entry_id: str,
    date_from: str | None = Query(None, description="Start date for cache invalidation"),
    date_to: str | None = Query(None, description="End date for cache invalidation"),
) -> dict[str, str]:
    """Delete a time entry."""
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure API key and select a user in Settings.",
        )

    try:
        client = RocketlaneClient()
        await client.delete_time_entry(entry_id)

        # Invalidate cache if dates provided
        if date_from and date_to:
            await time_entries_cache.invalidate_period(
                date_from=date_from,
                date_to=date_to,
            )

        return {"status": "success", "message": "Time entry deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entries/refresh")
async def refresh_time_entries(
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    project_id: str | None = Query(None, description="Filter by project ID"),
) -> dict[str, str]:
    """Force refresh time entries cache for the specified period."""
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
        # Force refresh the cache
        await time_entries_cache.get_entries(
            date_from=date_from,
            date_to=date_to,
            project_id=project_id,
            force_refresh=True
        )
        return {"status": "success", "message": "Time entries cache refreshed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=dict[str, Any])
async def get_timesheet_summary(
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
) -> dict[str, Any]:
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
        # Get entries from cache
        entries = await time_entries_cache.get_entries(
            date_from=date_from,
            date_to=date_to,
            force_refresh=False
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


class TranscriptionRequest(BaseModel):
    """Model for audio transcription request."""
    audio_data: str  # Base64 encoded audio data
    language: str | None = "en"


class ProcessedTimeEntry(BaseModel):
    """Model for a processed time entry from transcription."""
    date: str
    minutes: int
    task_id: str | None = None
    project_id: str | None = None
    activity_name: str | None = None
    notes: str = ""
    billable: bool = True
    category_id: str | None = None
    confidence: float  # Confidence score 0-1
    project_name: str | None = None  # For display
    task_name: str | None = None  # For display
    category_name: str | None = None  # For display
    warnings: list[str] = []  # Any warnings or missing fields


class TranscriptionProcessingRequest(BaseModel):
    """Model for processing transcription into time entries."""
    transcription: str
    date: str  # The date to apply entries to
    
    
class TranscriptionProcessingResponse(BaseModel):
    """Response with processed time entries."""
    entries: list[ProcessedTimeEntry]
    total_minutes: int
    raw_response: str | None = None  # For debugging


@router.post("/transcribe", response_model=dict[str, str])
async def transcribe_audio(request: TranscriptionRequest) -> dict[str, str]:
    """Transcribe audio using OpenAI's Whisper API."""
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=403,
            detail="OpenAI API key not configured. Speech-to-text requires OpenAI.",
        )
    
    try:
        # Decode base64 audio data
        audio_bytes = base64.b64decode(request.audio_data)
        
        # Get LLM provider (must be OpenAI for transcription)
        llm_provider = get_llm_provider(settings)
        
        # Check if provider supports transcription
        if not hasattr(llm_provider, "transcribe_audio"):
            raise HTTPException(
                status_code=400,
                detail="Current LLM provider does not support speech-to-text. Please configure OpenAI.",
            )
        
        # Transcribe the audio
        transcription = await llm_provider.transcribe_audio(
            audio_bytes, 
            language=request.language
        )
        
        return {"transcription": transcription}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-transcription", response_model=TranscriptionProcessingResponse)
async def process_transcription(
    request: TranscriptionProcessingRequest
) -> TranscriptionProcessingResponse:
    """Process transcription text into structured time entries using LLM."""
    if not settings.rocketlane_api_key or not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="Configuration incomplete. Please configure API key and select a user in Settings.",
        )
    
    try:
        # Get available projects, tasks, and categories for context
        project_cache = ProjectCacheService()
        user_id = int(settings.rocketlane_user_id)
        
        # Fetch all necessary data in parallel
        projects = await project_cache.get_user_projects(user_id)
        tasks = await tasks_cache_v2.get_all_tasks()
        categories = await time_entry_categories_cache.get_categories()
        
        # Build context for LLM
        projects_context = []
        for project in projects:
            project_tasks = [t for t in tasks if str(t.get("project", {}).get("projectId")) == str(project.get("projectId"))]
            projects_context.append({
                "id": str(project.get("projectId")),
                "name": project.get("projectName"),
                "tasks": [
                    {
                        "id": str(task.get("taskId")),
                        "name": task.get("taskName"),
                    }
                    for task in project_tasks
                ]
            })
        
        categories_context = [
            {
                "id": str(cat.get("categoryId")),
                "name": cat.get("categoryName"),
            }
            for cat in categories
        ]
        
        # Build prompt for LLM
        system_prompt = """You are a time entry assistant for Grafana Labs Professional Services team members.
Your task is to parse spoken time entry descriptions and convert them into structured JSON time entries.

Context:
- This tool is used by Professional Services consultants
- Default to billable=true unless explicitly stated as non-billable or internal
- TSM means Technical Services Manager
- Common categories: Implementation, Admin, Training, Support, Planning, Documentation
- Be smart about matching project names - users often abbreviate or use partial names
- Each entry should have a confidence score between 0 and 1

Output Format:
Return ONLY valid JSON with an array of time entries. Each entry must have:
{
  "minutes": number (required),
  "project_id": string or null,
  "task_id": string or null,
  "category_id": string or null,
  "notes": string,
  "billable": boolean,
  "confidence": number (0-1),
  "warnings": [array of warning strings if any fields couldn't be determined]
}

Rules:
1. If a project is mentioned, find the best match from the available projects
2. If a task is mentioned, match it to the appropriate project's tasks
3. Choose the most appropriate category based on the work described
4. Convert time descriptions to minutes (e.g., "2 hours" = 120, "30 minutes" = 30)
5. Include a warning if any required information is missing or unclear
6. Set confidence based on how well the description matches available options"""

        user_prompt = f"""Available Projects and Tasks:
{json.dumps(projects_context, indent=2)}

Available Categories:
{json.dumps(categories_context, indent=2)}

User's spoken time entry for {request.date}:
"{request.transcription}"

Parse this into time entries. Return ONLY the JSON array."""

        # Get LLM provider and process
        llm_provider = get_llm_provider(settings)
        response = await llm_provider.generate_completion(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for more consistent parsing
            max_tokens=2000,
        )
        
        # Parse LLM response
        try:
            # Clean up response if needed (remove markdown code blocks)
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response.split("\n", 1)[1]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response.rsplit("\n", 1)[0]
            cleaned_response = cleaned_response.strip()
            
            parsed_entries = json.loads(cleaned_response)
            if not isinstance(parsed_entries, list):
                parsed_entries = [parsed_entries]
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse LLM response as JSON: {str(e)}. Response: {response[:500]}",
            )
        
        # Build response with enriched data
        processed_entries = []
        total_minutes = 0
        
        for entry in parsed_entries:
            # Find project and task names for display
            project_name = None
            task_name = None
            category_name = None
            
            if entry.get("project_id"):
                project = next((p for p in projects if str(p.get("projectId")) == str(entry["project_id"])), None)
                if project:
                    project_name = project.get("projectName")
            
            if entry.get("task_id"):
                task = next((t for t in tasks if str(t.get("taskId")) == str(entry["task_id"])), None)
                if task:
                    task_name = task.get("taskName")
            
            if entry.get("category_id"):
                category = next((c for c in categories if str(c.get("categoryId")) == str(entry["category_id"])), None)
                if category:
                    category_name = category.get("categoryName")
            
            processed_entry = ProcessedTimeEntry(
                date=request.date,
                minutes=entry.get("minutes", 0),
                task_id=entry.get("task_id"),
                project_id=entry.get("project_id"),
                activity_name=entry.get("activity_name"),
                notes=entry.get("notes", ""),
                billable=entry.get("billable", True),
                category_id=entry.get("category_id"),
                confidence=entry.get("confidence", 0.5),
                project_name=project_name,
                task_name=task_name,
                category_name=category_name,
                warnings=entry.get("warnings", []),
            )
            
            processed_entries.append(processed_entry)
            total_minutes += processed_entry.minutes
        
        return TranscriptionProcessingResponse(
            entries=processed_entries,
            total_minutes=total_minutes,
            raw_response=response,  # Include for debugging
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
