from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ...core.logging import get_logger
from ...services.user_cache import UserCacheService

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger(__name__)

# Initialize cache service
user_cache = UserCacheService()


@router.get("/", response_model=list[dict[str, Any]])
async def get_users(
    force_refresh: bool = Query(False, description="Force refresh from API")
):
    """Get all available users from cache or Rocketlane API with pagination support"""
    try:
        logger.info(f"Fetching users (force_refresh={force_refresh})")
        
        # Get users from cache or API
        users = await user_cache.get_all_users(force_refresh=force_refresh)
        
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
            for user in users
            if user.get("userId") and (user.get("email") or user.get("emailId"))
        ]

        # Sort users alphabetically by full name
        formatted_users.sort(key=lambda u: u["fullName"].lower())
        
        logger.info(f"Successfully formatted {len(formatted_users)} users")
        return formatted_users

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching users: {e}", exc_info=True)
        
        # Try to serve from stale cache if available
        try:
            users = await user_cache.get_all_users(force_refresh=False)
            if users:
                # Transform and sort user data
                formatted_users = [
                    {
                        "userId": user.get("userId"),
                        "emailId": user.get("email")
                        or user.get("emailId"),
                        "firstName": user.get("firstName", ""),
                        "lastName": user.get("lastName", ""),
                        "fullName": f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                        or user.get("email", "").split("@")[0],
                    }
                    for user in users
                    if user.get("userId") and (user.get("email") or user.get("emailId"))
                ]
                formatted_users.sort(key=lambda u: u["fullName"].lower())
                
                logger.warning(f"Serving {len(formatted_users)} users from cache due to API error")
                return formatted_users
        except:
            pass
        
        raise HTTPException(status_code=502, detail="Unable to fetch users. Please try again later.")


@router.get("/cache/stats")
async def get_cache_stats():
    """Get user cache statistics"""
    try:
        stats = await user_cache.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/refresh")
async def refresh_user_cache():
    """Force refresh of the user cache"""
    try:
        logger.info("Force refreshing user cache")
        users = await user_cache.get_all_users(force_refresh=True)
        
        return {
            "status": "success",
            "message": f"Cache refreshed with {len(users)} users",
            "users_cached": len(users),
        }
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache")
async def invalidate_cache():
    """Invalidate the entire user cache"""
    try:
        await user_cache.invalidate()
        return {
            "status": "success",
            "message": "User cache invalidated"
        }
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))