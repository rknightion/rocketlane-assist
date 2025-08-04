from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
import os
from ...core.config import settings

router = APIRouter(prefix="/config", tags=["configuration"])


class ConfigUpdate(BaseModel):
    llm_provider: Literal["openai", "anthropic"]
    llm_model: str
    openai_api_key: str = None
    anthropic_api_key: str = None
    rocketlane_api_key: str = None


@router.get("/")
async def get_config():
    """Get current configuration (excluding sensitive data)"""
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "has_openai_key": bool(settings.openai_api_key),
        "has_anthropic_key": bool(settings.anthropic_api_key),
        "has_rocketlane_key": bool(settings.rocketlane_api_key),
    }


@router.put("/")
async def update_config(config: ConfigUpdate):
    """Update configuration and restart if needed"""
    try:
        # Update .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        
        # Read existing .env
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        key, value = line.strip().split("=", 1)
                        env_vars[key] = value
        
        # Update values
        env_vars["LLM_PROVIDER"] = config.llm_provider
        env_vars["LLM_MODEL"] = config.llm_model
        
        if config.openai_api_key:
            env_vars["OPENAI_API_KEY"] = config.openai_api_key
        if config.anthropic_api_key:
            env_vars["ANTHROPIC_API_KEY"] = config.anthropic_api_key
        if config.rocketlane_api_key:
            env_vars["ROCKETLANE_API_KEY"] = config.rocketlane_api_key
        
        # Write back to .env
        with open(env_path, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        # Note: In production, you'd want to trigger a graceful restart here
        # For now, we'll return a message indicating restart is needed
        return {
            "status": "success",
            "message": "Configuration updated. Please restart the application for changes to take effect."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))