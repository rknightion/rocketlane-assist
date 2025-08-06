"""API endpoints for testing connections"""

from fastapi import APIRouter, HTTPException

from ...core.config import settings
from ...core.llm.provider import get_llm_provider
from ...core.logging import get_logger
from ...services.rocketlane import RocketlaneClient

router = APIRouter(prefix="/test", tags=["test"])
logger = get_logger(__name__)


@router.get("/rocketlane")
async def test_rocketlane_connection():
    """Test Rocketlane API connection with minimal data fetch"""
    try:
        logger.info("Testing Rocketlane connection")
        client = RocketlaneClient()

        # Fetch just 1 user to verify the API key works
        users = await client.get_users(limit=1)

        return {
            "status": "success",
            "message": "Rocketlane API connection successful",
            "test_data": f"Found {len(users)} user(s)",
        }
    except ValueError as e:
        logger.error(f"Rocketlane API key error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Rocketlane connection test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {e!s}")


@router.get("/llm")
async def test_llm_connection():
    """Test LLM API connection with a simple prompt"""
    try:
        logger.info(f"Testing {settings.llm_provider} connection")

        # Check if API key is configured
        if settings.llm_provider == "openai" and not settings.openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key not configured")
        if settings.llm_provider == "anthropic" and not settings.anthropic_api_key:
            raise HTTPException(status_code=400, detail="Anthropic API key not configured")

        # Get LLM provider and test with a simple prompt
        llm = get_llm_provider()
        test_prompt = "Respond with 'OK' if you can read this."

        response = await llm.generate_completion(test_prompt)

        return {
            "status": "success",
            "message": f"{settings.llm_provider} API connection successful",
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "test_response": response[:50] + "..." if len(response) > 50 else response,
        }
    except Exception as e:
        logger.error(f"LLM connection test failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM connection test failed: {e!s}")
