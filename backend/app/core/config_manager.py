"""
Configuration manager for persistent JSON-based configuration.
This allows dynamic configuration updates without requiring app restarts.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AppConfig(BaseModel):
    """Application configuration model"""

    # LLM Configuration
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Rocketlane Configuration
    rocketlane_api_key: str = ""
    rocketlane_user_id: str = ""
    rocketlane_api_base_url: str = "https://api.rocketlane.com/api/1.0"

    # Application Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]


class ConfigManager:
    """Manages application configuration with file persistence"""

    def __init__(self, config_path: Optional[str] = None):
        # Default to /config/settings.json in container, or local config/settings.json
        self.config_path = Path(config_path or os.getenv("CONFIG_PATH", "/config/settings.json"))
        self._config: Optional[AppConfig] = None
        self._is_writable = True
        
        # Try to create parent directory
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            print(f"Warning: Cannot create config directory {self.config_path.parent}: {e}")
            print("Configuration will be stored in memory only")
            self._is_writable = False
        
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self._config = AppConfig(**data)
            except Exception as e:
                print(f"Error loading config from {self.config_path}: {e}")
                self._config = self._create_default_config()
        else:
            self._config = self._create_default_config()
            self._save_config()

    def _create_default_config(self) -> AppConfig:
        """Create default configuration from environment variables"""
        return AppConfig(
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            rocketlane_api_key=os.getenv("ROCKETLANE_API_KEY", ""),
            rocketlane_user_id=os.getenv("ROCKETLANE_USER_ID", ""),
            rocketlane_api_base_url=os.getenv("ROCKETLANE_API_BASE_URL", "https://api.rocketlane.com/api/1.0"),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
        )

    def _save_config(self) -> None:
        """Save configuration to file"""
        if not self._is_writable:
            print("Configuration is read-only, changes are stored in memory only")
            return
            
        try:
            # Test write permissions first
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self._config.model_dump(), f, indent=2)
        except (OSError, PermissionError) as e:
            print(f"Warning: Cannot save config to {self.config_path}: {e}")
            print("Configuration changes are stored in memory only")
            self._is_writable = False
        except Exception as e:
            print(f"Error saving config to {self.config_path}: {e}")

    def get_config(self) -> AppConfig:
        """Get current configuration"""
        if self._config is None:
            self._load_config()
        return self._config

    def update_config(self, updates: Dict[str, Any]) -> AppConfig:
        """Update configuration and save to file"""
        if self._config is None:
            self._load_config()

        # Update only provided fields
        config_dict = self._config.model_dump()
        config_dict.update(updates)
        self._config = AppConfig(**config_dict)

        # Save to file
        self._save_config()

        return self._config

    def reload_config(self) -> AppConfig:
        """Reload configuration from file"""
        self._load_config()
        return self._config


# Global configuration manager instance
_config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager"""
    return _config_manager


def get_settings() -> AppConfig:
    """Get current application settings"""
    return _config_manager.get_config()