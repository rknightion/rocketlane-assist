"""Project membership cache service for efficient filtering"""

import json
import os
from datetime import datetime, timedelta
from typing import Any

from ..core.config_manager import get_config_manager


class ProjectCacheService:
    """Service for caching project membership data"""

    def __init__(self):
        self.config_manager = get_config_manager()
        self.cache_dir = os.path.dirname(self.config_manager.config_path)
        self.cache_file = os.path.join(self.cache_dir, "project_cache.json")
        self.cache_ttl = timedelta(hours=1)  # Cache for 1 hour

    def _load_cache(self) -> dict[str, Any]:
        """Load cache from file"""
        if not os.path.exists(self.cache_file):
            return {"projects": {}, "last_updated": None}

        try:
            with open(self.cache_file) as f:
                return json.load(f)
        except Exception:
            return {"projects": {}, "last_updated": None}

    def _save_cache(self, cache_data: dict[str, Any]) -> None:
        """Save cache to file"""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save project cache: {e}")

    def is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        cache_data = self._load_cache()
        if not cache_data["last_updated"]:
            return False

        last_updated = datetime.fromisoformat(cache_data["last_updated"])
        return datetime.now() - last_updated < self.cache_ttl

    def get_project_members(self, project_id: int) -> dict[str, list[int]] | None:
        """Get cached project members"""
        if not self.is_cache_valid():
            return None

        cache_data = self._load_cache()
        return cache_data["projects"].get(str(project_id))

    def update_project_cache(self, projects: list[dict[str, Any]]) -> None:
        """Update the project cache with membership data"""
        cache_data: dict[str, Any] = {
            "projects": {},
            "last_updated": datetime.now().isoformat(),
        }

        for project in projects:
            project_id = str(project.get("projectId"))

            # Extract all types of members from the project
            members: dict[str, list[str]] = {
                "team_members": [],
                "solution_architects": [],
                "all_members": [],
            }

            # Team members
            team_members = project.get("teamMembers", {}).get("members", [])
            for member in team_members:
                user_id = member.get("userId")
                if user_id:
                    members["team_members"].append(user_id)
                    members["all_members"].append(user_id)

            # Solution Architects (check various possible fields)
            # Check for solutionArchitects field
            solution_architects = project.get("solutionArchitects", [])
            if isinstance(solution_architects, list):
                for sa in solution_architects:
                    if isinstance(sa, dict):
                        user_id = sa.get("userId")
                        if user_id:
                            members["solution_architects"].append(user_id)
                            if user_id not in members["all_members"]:
                                members["all_members"].append(user_id)
                    elif isinstance(sa, int):
                        sa_str = str(sa)
                        members["solution_architects"].append(sa_str)
                        if sa_str not in members["all_members"]:
                            members["all_members"].append(sa_str)

            # Check for solutionArchitect field (singular)
            solution_architect = project.get("solutionArchitect")
            if solution_architect:
                if isinstance(solution_architect, dict):
                    user_id = solution_architect.get("userId")
                    if user_id and user_id not in members["solution_architects"]:
                        members["solution_architects"].append(user_id)
                        if user_id not in members["all_members"]:
                            members["all_members"].append(user_id)
                elif isinstance(solution_architect, int):
                    sa_str = str(solution_architect)
                    if sa_str not in members["solution_architects"]:
                        members["solution_architects"].append(sa_str)
                        if sa_str not in members["all_members"]:
                            members["all_members"].append(sa_str)

            # Check for other possible member fields
            # Project owner
            owner = project.get("owner")
            if owner:
                if isinstance(owner, dict):
                    user_id = owner.get("userId")
                    if user_id and user_id not in members["all_members"]:
                        members["all_members"].append(user_id)
                elif isinstance(owner, int):
                    owner_str = str(owner)
                    if owner_str not in members["all_members"]:
                        members["all_members"].append(owner_str)

            # Created by
            created_by = project.get("createdBy")
            if created_by:
                if isinstance(created_by, dict):
                    user_id = created_by.get("userId")
                    if user_id and user_id not in members["all_members"]:
                        members["all_members"].append(user_id)
                elif isinstance(created_by, int):
                    created_by_str = str(created_by)
                    if created_by_str not in members["all_members"]:
                        members["all_members"].append(created_by_str)

            cache_data["projects"][project_id] = members

        self._save_cache(cache_data)

    def get_user_projects(
        self, user_id: int, projects: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Get projects where user is a member (any role)"""
        # First, update cache if needed
        if not self.is_cache_valid():
            self.update_project_cache(projects)

        cache_data = self._load_cache()
        user_projects = []

        for project in projects:
            project_id = str(project.get("projectId"))
            project_members = cache_data["projects"].get(project_id, {})

            # Check if user is in any member list
            if user_id in project_members.get("all_members", []):
                user_projects.append(project)

        return user_projects

    def clear_cache(self) -> None:
        """Clear the cache file"""
        if os.path.exists(self.cache_file):
            try:
                os.remove(self.cache_file)
            except Exception as e:
                print(f"Failed to clear project cache: {e}")
