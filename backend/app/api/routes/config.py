from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...core.config_manager import get_config_manager

router = APIRouter(prefix="/config", tags=["configuration"])


class ConfigUpdate(BaseModel):
    llm_provider: Literal["openai", "anthropic"]
    llm_model: str
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    rocketlane_api_key: str | None = None
    rocketlane_user_id: str | None = None


@router.get("/")
async def get_config():
    """Get current configuration (excluding sensitive data)"""
    config = get_config_manager().get_config()
    return {
        "llm_provider": config.llm_provider,
        "llm_model": config.llm_model,
        "has_openai_key": bool(config.openai_api_key),
        "has_anthropic_key": bool(config.anthropic_api_key),
        "has_rocketlane_key": bool(config.rocketlane_api_key),
        "rocketlane_user_id": config.rocketlane_user_id,
    }


@router.put("/")
async def update_config(config: ConfigUpdate):
    """Update configuration dynamically without restart"""
    try:
        # Build update dict with only non-None values
        updates = {}

        # Always update these fields
        updates["llm_provider"] = config.llm_provider
        updates["llm_model"] = config.llm_model

        # Update optional fields only if provided
        if config.openai_api_key is not None:
            updates["openai_api_key"] = config.openai_api_key
        if config.anthropic_api_key is not None:
            updates["anthropic_api_key"] = config.anthropic_api_key
        if config.rocketlane_api_key is not None:
            updates["rocketlane_api_key"] = config.rocketlane_api_key
        if config.rocketlane_user_id is not None:
            updates["rocketlane_user_id"] = config.rocketlane_user_id

        # Test Rocketlane API key if provided
        if config.rocketlane_api_key:
            from ...services.rocketlane import RocketlaneClient

            try:
                # Try to fetch projects to validate the API key
                client = RocketlaneClient(api_key=config.rocketlane_api_key)
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.get(
                        f"{client.base_url}/projects",
                        headers=client.headers,
                        params={"pageSize": 1},
                    )
                    response.raise_for_status()
            except Exception as e:
                # If API key is invalid, clear it
                updates["rocketlane_api_key"] = ""
                raise HTTPException(status_code=400, detail=f"Invalid Rocketlane API key: {e!s}")

        # Update configuration
        config_manager = get_config_manager()
        updated_config = config_manager.update_config(updates)

        return {
            "status": "success",
            "message": "Configuration updated successfully. Changes are effective immediately.",
            "config": {
                "llm_provider": updated_config.llm_provider,
                "llm_model": updated_config.llm_model,
                "has_openai_key": bool(updated_config.openai_api_key),
                "has_anthropic_key": bool(updated_config.anthropic_api_key),
                "has_rocketlane_key": bool(updated_config.rocketlane_api_key),
                "rocketlane_user_id": updated_config.rocketlane_user_id,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
