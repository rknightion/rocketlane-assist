from typing import List, Dict, Any, Optional
from anthropic import AsyncAnthropic
from .base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider implementation"""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        super().__init__(api_key, model)
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def generate_completion(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        messages = [{"role": "user", "content": prompt}]
        
        response = await self.client.messages.create(
            model=self.model,
            messages=messages,
            system=system_prompt if system_prompt else None,
            temperature=temperature,
            max_tokens=max_tokens if max_tokens else 1024
        )
        return response.content[0].text
    
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        # Convert messages format if needed
        anthropic_messages = []
        system_message = None
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        response = await self.client.messages.create(
            model=self.model,
            messages=anthropic_messages,
            system=system_message,
            temperature=temperature,
            max_tokens=max_tokens if max_tokens else 1024
        )
        return response.content[0].text