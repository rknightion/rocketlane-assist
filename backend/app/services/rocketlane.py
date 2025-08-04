import httpx
from typing import List, Dict, Any, Optional
from ..core.config import settings


class RocketlaneClient:
    """Client for interacting with Rocketlane API"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or settings.rocketlane_api_key
        self.base_url = base_url or settings.rocketlane_api_base_url
        self.headers = {
            "api-key": self.api_key,
            "accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def get_projects(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of all projects"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/projects",
                headers=self.headers,
                params={"pageSize": limit}
            )
            response.raise_for_status()
            data = response.json()
            # Handle both possible response structures
            if isinstance(data, list):
                return data
            return data.get("projects", [])
    
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get details of a specific project"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_tasks(
        self, 
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get tasks, optionally filtered by project and status"""
        params = {"pageSize": limit}
        
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
                "done": 3
            }
            status_value = status_map.get(status.lower(), status)
            filters.append(f"status.eq={status_value}")
        
        if filters:
            params["filters"] = ",".join(filters)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tasks",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            # Handle both possible response structures
            if isinstance(data, list):
                return data
            return data.get("tasks", [])
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get details of a specific task"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tasks/{task_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_project_tasks(
        self, 
        project_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all tasks for a specific project"""
        return await self.get_tasks(project_id=project_id, status=status)