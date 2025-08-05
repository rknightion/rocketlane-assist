from typing import Any

import httpx

from ..core.config import settings
from ..core.logging import get_logger, log_request_details, log_response_details


class RocketlaneClient:
    """Client for interacting with Rocketlane API"""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.logger = get_logger(__name__)
        self.api_key = api_key or settings.rocketlane_api_key
        self.base_url = base_url or settings.rocketlane_api_base_url
        self.headers = {
            "api-key": self.api_key,
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        
        # Validate configuration
        if not self.api_key:
            self.logger.error("Rocketlane API key is not configured")
            raise ValueError("Rocketlane API key is required")
        
        self.logger.debug(f"RocketlaneClient initialized with base_url: {self.base_url}")

    async def get_projects(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get all projects with pagination support"""
        all_projects = []
        page_token = None
        
        try:
            async with httpx.AsyncClient() as client:
                while True:
                    params = {"pageSize": limit}
                    if page_token:
                        params["pageToken"] = page_token
                    
                    url = f"{self.base_url}/projects"
                    log_request_details(self.logger, "GET", url, self.headers, params)
                    
                    response = await client.get(
                        url, 
                        headers=self.headers,
                        params=params
                    )
                    
                    log_response_details(self.logger, response.status_code, response.text)
                    
                    # Check for specific error conditions
                    if response.status_code == 401:
                        self.logger.error("Authentication failed - check API key")
                        raise ValueError("Invalid Rocketlane API key")
                    elif response.status_code == 403:
                        self.logger.error("Access forbidden - check API permissions")
                        raise ValueError("Access forbidden - check API key permissions")
                    
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
                        
                        # Safety check
                        if not page_token:
                            break
                    elif "projects" in data:
                        all_projects.extend(data["projects"])
                        break  # Assume no pagination
                    else:
                        break
                    
            self.logger.info(f"Successfully fetched {len(all_projects)} projects")
            return all_projects
            
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error fetching projects: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching projects: {e}")
            raise

    async def get_project(self, project_id: str) -> dict[str, Any]:
        """Get details of a specific project"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}", headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_tasks(
        self,
        project_id: str | None = None,
        status: str | None = None,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get tasks, optionally filtered by project, status, and assigned user"""
        params: dict[str, Any] = {"pageSize": limit}

        # Build filters for search API
        filters = []
        if project_id:
            filters.append(f"project.eq={project_id}")
        if status:
            # Status can be: "todo", "in_progress", "completed", etc.
            # Map common status strings to numeric values based on event payload examples
            status_map = {
                "todo": 1,
                "to_do": 1,
                "not_done": 1,
                "in_progress": 2,
                "completed": 3,
                "done": 3,
            }
            status_value = status_map.get(status.lower(), status)
            filters.append(f"status.eq={status_value}")
        if user_id:
            filters.append(f"assignees.cn={user_id}")

        if filters:
            params["filters"] = ",".join(filters)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tasks", headers=self.headers, params=params
            )
            response.raise_for_status()
            data = response.json()
            # Handle different response structures
            if isinstance(data, list):
                return data
            elif "data" in data:
                return data["data"]
            elif "tasks" in data:
                return data["tasks"]
            return []

    async def get_task(self, task_id: str) -> dict[str, Any]:
        """Get details of a specific task"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/tasks/{task_id}", headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_project_tasks(
        self, project_id: str, status: str | None = None, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all tasks for a specific project"""
        return await self.get_tasks(project_id=project_id, status=status, user_id=user_id)

    async def create_time_entry(
        self,
        task_id: str,
        user_id: str,
        minutes: int,
        date: str,
        description: str = "",
        category_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a time entry for a task - requires user ID"""
        if not user_id:
            raise ValueError("User ID is required for creating time entries")

        payload = {
            "taskId": task_id,
            "userId": user_id,
            "minutes": minutes,
            "date": date,
            "description": description,
        }

        if category_id:
            payload["categoryId"] = category_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/time-entries", headers=self.headers, json=payload
            )
            response.raise_for_status()
            return response.json()

    async def get_time_entries(
        self,
        user_id: str | None = None,
        project_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get time entries with optional filtering"""
        params: dict[str, Any] = {"pageSize": limit}

        # Build filters
        filters = []
        if user_id:
            filters.append(f"user.eq={user_id}")
        if project_id:
            filters.append(f"project.eq={project_id}")
        if date_from:
            filters.append(f"date.ge={date_from}")
        if date_to:
            filters.append(f"date.le={date_to}")

        if filters:
            params["filters"] = ",".join(filters)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/time-entries/search", headers=self.headers, params=params
            )
            response.raise_for_status()
            data = response.json()
            # Handle different response structures
            if isinstance(data, list):
                return data
            elif "data" in data:
                return data["data"]
            elif "timeEntries" in data:
                return data["timeEntries"]
            return []
