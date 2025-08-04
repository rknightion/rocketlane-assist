from typing import Any

import httpx

from ..core.config import settings


class RocketlaneClient:
    """Client for interacting with Rocketlane API"""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.rocketlane_api_key
        self.base_url = base_url or settings.rocketlane_api_base_url
        self.headers = {
            "api-key": self.api_key,
            "accept": "application/json",
            "Content-Type": "application/json",
        }

    async def get_projects(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get list of all projects"""
        # Note: Projects cannot be filtered by user in Rocketlane API
        # We'll get all projects and the frontend should filter based on user's tasks
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/projects", headers=self.headers, params={"pageSize": limit}
            )
            response.raise_for_status()
            data = response.json()
            # Handle both possible response structures
            if isinstance(data, list):
                return data
            return data.get("projects", [])

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
            # Handle both possible response structures
            if isinstance(data, list):
                return data
            return data.get("tasks", [])

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
            # Handle both possible response structures
            if isinstance(data, list):
                return data
            return data.get("timeEntries", [])
