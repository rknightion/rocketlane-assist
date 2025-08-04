from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from ...services.rocketlane import RocketlaneClient

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[dict[str, Any]])
async def get_users():
    """Get all available users from Rocketlane"""
    try:
        client = RocketlaneClient()

        # Get all users from Rocketlane
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{client.base_url}/users",
                headers=client.headers,
                params={"pageSize": 200},  # Get up to 200 users
            )
            response.raise_for_status()
            data = response.json()

            # Extract user information
            users = []
            if isinstance(data, list):
                users = data
            elif isinstance(data, dict) and "users" in data:
                users = data["users"]

            # Return simplified user data
            return [
                {
                    "userId": user.get("userId"),
                    "emailId": user.get("emailId"),
                    "firstName": user.get("firstName", ""),
                    "lastName": user.get("lastName", ""),
                    "fullName": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip(),
                }
                for user in users
                if user.get("userId") and user.get("emailId")
            ]

    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch users from Rocketlane: {e!s}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
