from pydantic_settings import BaseSettings
from typing import List, Literal
import json


class Settings(BaseSettings):
    # LLM Provider Configuration
    llm_provider: Literal["openai", "anthropic"] = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4"
    
    # Rocketlane API Configuration
    rocketlane_api_key: str = ""
    rocketlane_api_base_url: str = "https://api.rocketlane.com/api/1.0"
    
    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    @property
    def active_llm_api_key(self) -> str:
        """Get the API key for the currently selected LLM provider"""
        if self.llm_provider == "openai":
            return self.openai_api_key
        else:
            return self.anthropic_api_key
    
    def model_config_dict(self) -> dict:
        """Get configuration as dictionary for frontend"""
        return {
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "rocketlane_api_base_url": self.rocketlane_api_base_url,
        }


settings = Settings()