# Business Logic Services  

## Service Base Pattern
```python
import httpx
from typing import List, Dict, Optional

class BaseService:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
```

## Rocketlane Service
- **User filtering mandatory** - all task queries include `assignees.cn={user_id}`
- **Rate limiting** - respects Rocketlane API limits
- **Error handling** - converts HTTP errors to domain exceptions

## Summarization Service  
- **LLM provider** via factory from core
- **Prompt templates** from `../prompts/templates/`
- **Token management** - tracks usage and costs

## Cache Services
- **Project cache** - 5min TTL, user-specific
- **Task cache** - 2min TTL, invalidated on updates
- **User cache** - 1hr TTL, rarely changes

## Service Rules
- **Async context managers** for HTTP clients
- **User context required** for all data operations
- **Caching** for external API calls
- **Structured logging** with correlation IDs