"""
Dynamic configuration system that uses JSON file storage.
Maintains backward compatibility with existing code.
"""

from .config_manager import get_settings as get_dynamic_settings


class Settings:
    """Wrapper class that provides dynamic settings access"""

    def __getattribute__(self, name):
        # Get the actual settings from config manager
        config = get_dynamic_settings()

        # Handle special methods
        if name in ["active_llm_api_key", "model_config_dict"]:
            return object.__getattribute__(self, name)

        # Return attribute from dynamic config
        if hasattr(config, name):
            return getattr(config, name)

        return object.__getattribute__(self, name)

    @property
    def active_llm_api_key(self) -> str:
        """Get the API key for the currently selected LLM provider"""
        config = get_dynamic_settings()
        if config.llm_provider == "openai":
            return config.openai_api_key
        else:
            return config.anthropic_api_key

    def model_config_dict(self) -> dict:
        """Get configuration as dictionary for frontend"""
        config = get_dynamic_settings()
        return {
            "llm_provider": config.llm_provider,
            "llm_model": config.llm_model,
            "rocketlane_api_base_url": config.rocketlane_api_base_url,
            "rocketlane_user_id": config.rocketlane_user_id,
        }


# Global settings instance that dynamically reads from config manager
settings = Settings()
