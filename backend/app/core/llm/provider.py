from ..config import settings
from .anthropic_provider import AnthropicProvider
from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider


class LLMProvider:
    """Factory for creating LLM providers"""

    @staticmethod
    def create(provider_type: str | None = None) -> BaseLLMProvider:
        """Create an LLM provider based on configuration"""
        provider_type = provider_type or settings.llm_provider

        if provider_type == "openai":
            return OpenAIProvider(api_key=settings.openai_api_key, model=settings.llm_model)
        elif provider_type == "anthropic":
            return AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.llm_model)
        else:
            raise ValueError(f"Unknown LLM provider: {provider_type}")


def get_llm_provider() -> BaseLLMProvider:
    """Get the configured LLM provider instance"""
    return LLMProvider.create()
