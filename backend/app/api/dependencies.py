from fastapi import HTTPException, Request, status

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


async def verify_api_keys():
    """Verify that required API keys are configured"""
    logger.debug(f"Verifying API keys - Rocketlane key present: {bool(settings.rocketlane_api_key)}")
    
    if not settings.rocketlane_api_key:
        logger.error("Rocketlane API key is not configured in settings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rocketlane API key not configured",
        )

    if settings.llm_provider == "openai" and not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key not configured",
        )

    if settings.llm_provider == "anthropic" and not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Anthropic API key not configured",
        )


async def verify_user_id_configured(request: Request):
    """Verify that user ID is configured for non-exempt endpoints"""
    # Exempt endpoints that don't require user ID
    exempt_paths = [
        "/api/v1/users",  # Need to get users without user ID
        "/api/v1/config",  # Configuration management
        "/health",
        "/docs",
        "/openapi.json",
        "/",
    ]

    # Check if current path is exempt
    path = request.url.path
    if any(path.startswith(exempt) for exempt in exempt_paths):
        return

    # For all other endpoints, require user ID
    if not settings.rocketlane_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID not configured. Please select a user in settings to continue. This application requires user context for all operations.",
        )
