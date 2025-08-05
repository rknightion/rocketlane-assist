from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from ...services.rocketlane import RocketlaneClient

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[dict[str, Any]])
async def get_users():
    """Get all available users from Rocketlane with pagination support"""
    try:
        client = RocketlaneClient()
        all_users = []
        page_token = None

        async with httpx.AsyncClient() as http_client:
            # Keep fetching until we have all users
            while True:
                params = {"pageSize": 100}
                if page_token:
                    params["pageToken"] = page_token

                response = await http_client.get(
                    f"{client.base_url}/users",
                    headers=client.headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                # Extract user information
                users = []
                if isinstance(data, list):
                    users = data
                elif isinstance(data, dict) and "data" in data:
                    users = data["data"]
                elif isinstance(data, dict) and "users" in data:
                    users = data["users"]

                all_users.extend(users)

                # Check if there are more pages
                pagination = data.get("pagination", {})
                if not pagination.get("hasMore", False):
                    break
                page_token = pagination.get("nextPageToken")
                if not page_token:
                    break

            # Transform and sort user data
            formatted_users = [
                {
                    "userId": user.get("userId"),
                    "emailId": user.get("email")
                    or user.get("emailId"),  # Handle both 'email' and 'emailId'
                    "firstName": user.get("firstName", ""),
                    "lastName": user.get("lastName", ""),
                    "fullName": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                    or user.get("email", "").split("@")[0],
                }
                for user in all_users
                if user.get("userId") and (user.get("email") or user.get("emailId"))
            ]

            # Sort users alphabetically by full name
            formatted_users.sort(key=lambda u: u["fullName"].lower())

            return formatted_users

    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch users from Rocketlane: {e!s}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
