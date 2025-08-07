import asyncio
import json
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
        self.max_retries = 3
        self.initial_retry_delay = 1.0  # seconds

        # Validate configuration
        if not self.api_key:
            self.logger.error("Rocketlane API key is not configured")
            raise ValueError("Rocketlane API key is required")

        self.logger.debug(f"RocketlaneClient initialized with base_url: {self.base_url}")

    async def _handle_rate_limiting(self, response: httpx.Response, attempt: int = 0) -> bool:
        """Handle rate limiting with exponential backoff.
        
        Returns True if request should be retried, False otherwise.
        """
        if response.status_code == 429:
            if attempt >= self.max_retries:
                self.logger.error(f"Max retries ({self.max_retries}) exceeded for rate limiting")
                return False

            # Check for Retry-After header
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                wait_time = int(retry_after)
            else:
                # Exponential backoff
                wait_time = self.initial_retry_delay * (2 ** attempt)

            self.logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry (attempt {attempt + 1}/{self.max_retries})")
            await asyncio.sleep(wait_time)
            return True

        return False

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

                    response = await client.get(url, headers=self.headers, params=params)

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

        # According to Rocketlane API docs, filters should be individual query parameters
        # not a single "filters" parameter. Format: field.operation=value
        if project_id:
            params["project.eq"] = project_id

        if user_id:
            params["assignees.cn"] = user_id

        # Note: Status filtering seems to cause issues when combined with other filters
        # We'll handle status filtering in the response if needed

        url = f"{self.base_url}/tasks"
        log_request_details(self.logger, "GET", url, self.headers, params)

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)

            log_response_details(self.logger, response.status_code, response.text[:500] if response.text else "")

            response.raise_for_status()
            data = response.json()

            # Extract tasks from response
            tasks = []
            if isinstance(data, list):
                tasks = data
            elif "data" in data:
                tasks = data["data"]
            elif "tasks" in data:
                tasks = data["tasks"]

            # Apply status filtering on the response if needed
            if status and tasks:
                status_map = {
                    "todo": 1,
                    "to_do": 1,
                    "not_done": 1,
                    "in_progress": 2,
                    "completed": 3,
                    "done": 3,
                }
                status_value = status_map.get(status.lower(), status)

                # Filter tasks by status value
                filtered_tasks = []
                for task in tasks:
                    task_status = task.get("status")
                    if task_status:
                        # Check if status is a dict with value or direct value
                        if isinstance(task_status, dict):
                            if task_status.get("value") == status_value:
                                filtered_tasks.append(task)
                        elif task_status == status_value:
                            filtered_tasks.append(task)
                return filtered_tasks

            # Apply user filtering on the response if needed (when project_id is also specified)
            if user_id and project_id and tasks:
                filtered_tasks = []
                for task in tasks:
                    assignees = task.get("assignees", [])
                    # Check if user is in assignees list
                    if any(str(assignee.get("userId")) == str(user_id) for assignee in assignees if isinstance(assignee, dict)):
                        filtered_tasks.append(task)
                return filtered_tasks

            return tasks

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
        self.logger.info(f"Getting tasks for project {project_id}, status={status}, user_id={user_id}")
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

        # According to Rocketlane API docs, filters should be individual query parameters
        # not a single "filters" parameter. Format: field.operation=value
        if user_id:
            params["user.eq"] = user_id
        if project_id:
            params["project.eq"] = project_id
        if date_from:
            params["date.ge"] = date_from
        if date_to:
            params["date.le"] = date_to

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

    async def get_user(self, user_id: str) -> dict[str, Any]:
        """Get a specific user by ID"""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/users/{user_id}"
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_users(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get users from Rocketlane with specified limit"""
        params = {"pageSize": limit}

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/users"
                log_request_details(self.logger, "GET", url, self.headers, params)

                response = await client.get(url, headers=self.headers, params=params)

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
                    return data
                elif "data" in data:
                    return data["data"]
                elif "users" in data:
                    return data["users"]

                return []

        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error fetching users: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching users: {e}")
            raise

    async def get_time_entry_categories(self) -> list[dict[str, Any]]:
        """Get all time entry categories."""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/time-entries/categories"
                log_request_details(self.logger, "GET", url, self.headers, {})

                attempt = 0
                while attempt <= self.max_retries:
                    response = await client.get(url, headers=self.headers)

                    # Handle rate limiting
                    if await self._handle_rate_limiting(response, attempt):
                        attempt += 1
                        continue

                    log_response_details(self.logger, response.status_code, response.text[:500] if response.text else "")
                    response.raise_for_status()

                    data = response.json()

                    # Handle different response structures
                    if isinstance(data, list):
                        return data
                    elif "data" in data:
                        return data["data"]
                    elif "categories" in data:
                        return data["categories"]
                    return []

                # If we get here, max retries exceeded
                raise httpx.HTTPError("Max retries exceeded for time entry categories")

        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error fetching time entry categories: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching time entry categories: {e}")
            raise

    async def get_tasks_by_project(self, project_id: str) -> list[dict[str, Any]]:
        """Get all tasks for a specific project (for timesheets)."""
        try:
            params = {
                "projectId.eq": project_id,
                "pageSize": 500  # Get more tasks per page
            }

            all_tasks = []
            page_token = None

            async with httpx.AsyncClient() as client:
                while True:
                    if page_token:
                        params["pageToken"] = page_token

                    url = f"{self.base_url}/tasks"
                    log_request_details(self.logger, "GET", url, self.headers, params)

                    attempt = 0
                    while attempt <= self.max_retries:
                        response = await client.get(url, headers=self.headers, params=params)

                        # Handle rate limiting
                        if await self._handle_rate_limiting(response, attempt):
                            attempt += 1
                            continue

                        break

                    log_response_details(self.logger, response.status_code, response.text[:500] if response.text else "")
                    response.raise_for_status()

                    data = response.json()

                    # Extract tasks from response
                    if isinstance(data, list):
                        all_tasks.extend(data)
                        break  # No pagination
                    elif "data" in data:
                        all_tasks.extend(data["data"])

                        # Check for pagination
                        pagination = data.get("pagination", {})
                        if not pagination.get("hasMore", False):
                            break
                        page_token = pagination.get("nextPageToken")

                        if not page_token:
                            break
                    elif "tasks" in data:
                        all_tasks.extend(data["tasks"])
                        break
                    else:
                        break

            self.logger.info(f"Fetched {len(all_tasks)} tasks for project {project_id}")
            return all_tasks

        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error fetching tasks for project {project_id}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching tasks for project {project_id}: {e}")
            raise

    async def create_time_entry_v2(
        self,
        date: str,
        minutes: int,
        task_id: str | None = None,
        project_id: str | None = None,
        activity_name: str | None = None,
        notes: str = "",
        billable: bool = True,
        category_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a time entry following Rocketlane API v1.0 specification.
        
        Requires `date`, `minutes`, and both `project` and `task` for proper time tracking.
        """
        if not settings.rocketlane_user_id:
            raise ValueError("User ID must be configured for creating time entries")

        # Build payload according to API spec
        payload = {
            "date": date,
            "minutes": minutes,
            "billable": billable,
        }

        # Rocketlane requires both project AND task for time entries
        if task_id and project_id:
            payload["task"] = {"taskId": task_id}
            payload["project"] = {"projectId": project_id}
        elif activity_name:
            # For ad-hoc activities without specific task
            payload["activityName"] = activity_name
            if project_id:
                payload["project"] = {"projectId": project_id}
        else:
            raise ValueError("Both task_id and project_id must be provided, or use activity_name for ad-hoc entries")

        # Add optional fields
        if notes:
            payload["notes"] = notes

        if category_id:
            payload["category"] = {"categoryId": category_id}

        # Add user ID (required since our API key is global, not user-scoped)
        payload["user"] = {"userId": int(settings.rocketlane_user_id)}

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/time-entries"
                log_request_details(self.logger, "POST", url, self.headers, payload)
                self.logger.info(f"Creating time entry with payload: {json.dumps(payload, indent=2)}")

                attempt = 0
                while attempt <= self.max_retries:
                    response = await client.post(url, headers=self.headers, json=payload)

                    # Handle rate limiting
                    if await self._handle_rate_limiting(response, attempt):
                        attempt += 1
                        continue

                    break

                log_response_details(self.logger, response.status_code, response.text[:500] if response.text else "")
                if response.status_code == 400:
                    self.logger.error(f"400 Bad Request. Response body: {response.text}")
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error creating time entry: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating time entry: {e}")
            raise

    async def update_time_entry(
        self,
        entry_id: str,
        date: str,
        minutes: int,
        task_id: str | None = None,
        project_id: str | None = None,
        activity_name: str | None = None,
        notes: str | None = None,
        billable: bool = True,
        category_id: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing time entry."""
        # Build the payload
        payload = {
            "date": date,
            "minutes": minutes,
            "billable": billable,
        }

        # Add task/project or activity name
        if task_id and project_id:
            payload["task"] = {"taskId": task_id}
            payload["project"] = {"projectId": project_id}
        elif activity_name:
            payload["activityName"] = activity_name
            if project_id:
                payload["project"] = {"projectId": project_id}

        # Add optional fields
        if notes is not None:
            payload["notes"] = notes

        if category_id:
            payload["category"] = {"categoryId": category_id}

        # Add user ID
        payload["user"] = {"userId": int(settings.rocketlane_user_id)}

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/time-entries/{entry_id}"
                log_request_details(self.logger, "PUT", url, self.headers, payload)

                attempt = 0
                while attempt <= self.max_retries:
                    response = await client.put(url, headers=self.headers, json=payload)

                    # Handle rate limiting
                    if await self._handle_rate_limiting(response, attempt):
                        attempt += 1
                        continue

                    break

                log_response_details(self.logger, response.status_code, response.text[:500] if response.text else "")
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error updating time entry: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error updating time entry: {e}")
            raise

    async def delete_time_entry(self, entry_id: str) -> None:
        """Delete a time entry."""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/time-entries/{entry_id}"
                log_request_details(self.logger, "DELETE", url, self.headers, {})

                attempt = 0
                while attempt <= self.max_retries:
                    response = await client.delete(url, headers=self.headers)

                    # Handle rate limiting
                    if await self._handle_rate_limiting(response, attempt):
                        attempt += 1
                        continue

                    break

                log_response_details(self.logger, response.status_code, response.text[:500] if response.text else "")
                response.raise_for_status()

        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error deleting time entry: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error deleting time entry: {e}")
            raise
