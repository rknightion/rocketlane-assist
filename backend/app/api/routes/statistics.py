"""Statistics routes for user dashboard."""

from typing import Any

from fastapi import APIRouter, HTTPException

from ...core.config import settings
from ...services.user_statistics_cache import user_statistics_cache

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/", response_model=dict[str, Any])
async def get_user_statistics() -> dict[str, Any]:
    """Get statistics for the configured user from cache."""
    if not settings.rocketlane_api_key:
        raise HTTPException(status_code=500, detail="Rocketlane API key not configured")

    if not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=403,
            detail="User not selected. Please configure a user ID in settings."
        )

    try:
        # Get statistics from cache (will be fetched async if needed)
        stats = await user_statistics_cache.get_statistics()

        if stats.get("error"):
            raise HTTPException(status_code=500, detail=stats.get("error"))

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {e!s}")
