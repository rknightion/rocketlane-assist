from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """Generate a completion from the LLM"""
        pass

    @abstractmethod
    async def generate_chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """Generate a chat completion from the LLM"""
        pass

    @abstractmethod
    async def stream_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[str]:
        """Stream a completion from the LLM"""
        pass

    async def transcribe_audio(self, audio_data: bytes, language: str | None = None) -> str:
        """Transcribe audio using provider's speech-to-text API
        
        Args:
            audio_data: Audio file bytes
            language: Optional language code
        
        Returns:
            Transcribed text
            
        Raises:
            NotImplementedError: If provider doesn't support speech-to-text
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support speech-to-text")
