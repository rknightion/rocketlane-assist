from fastapi import HTTPException, status
from ..core.config import settings


async def verify_api_keys():
    """Verify that required API keys are configured"""
    if not settings.rocketlane_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rocketlane API key not configured"
        )
    
    if settings.llm_provider == "openai" and not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key not configured"
        )
    
    if settings.llm_provider == "anthropic" and not settings.anthropic_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Anthropic API key not configured"
        )