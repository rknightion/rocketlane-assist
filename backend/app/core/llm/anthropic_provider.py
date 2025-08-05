from typing import TYPE_CHECKING, Any, cast

from anthropic import NOT_GIVEN, AsyncAnthropic

from .base import BaseLLMProvider

if TYPE_CHECKING:
    from anthropic.types import MessageParam


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider implementation"""

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        super().__init__(api_key, model)
        self.client = AsyncAnthropic(api_key=api_key)

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        typed_messages = cast("list[MessageParam]", messages)

        response = await self.client.messages.create(
            model=self.model,
            messages=typed_messages,
            system=system_prompt if system_prompt else NOT_GIVEN,
            temperature=temperature,
            max_tokens=max_tokens if max_tokens else 1024,
        )
        # Extract text from the response content
        content = response.content[0]
        return getattr(content, "text", "") if hasattr(content, "text") else str(content)

    async def generate_chat_completion(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        # Convert messages format if needed
        anthropic_messages: list[dict[str, Any]] = []
        system_message: str | None = None

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        typed_messages = cast("list[MessageParam]", anthropic_messages)

        response = await self.client.messages.create(
            model=self.model,
            messages=typed_messages,
            system=system_message if system_message else NOT_GIVEN,
            temperature=temperature,
            max_tokens=max_tokens if max_tokens else 1024,
        )
        # Extract text from the response content
        content = response.content[0]
        return getattr(content, "text", "") if hasattr(content, "text") else str(content)
