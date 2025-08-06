# Core Infrastructure

## Configuration Management
```python
from .config import settings

# Settings access pattern
api_key = settings.rocketlane_api_key
user_id = settings.rocketlane_user_id
llm_provider = settings.llm_provider
```

## LLM Provider Factory
```python
from .llm.provider import get_llm_provider

# Usage in services
llm = get_llm_provider(settings)
response = await llm.generate_completion(prompt)
```

## Caching Layer
```python
from .cache import cache_manager

# Cache pattern
@cache_manager.cached(ttl=300)
async def expensive_operation():
    return await fetch_data()
```

## Core Rules
- **Config access** only through `settings` instance
- **LLM provider** must use factory pattern
- **Caching** for expensive operations (300s TTL)
- **Logging** configured via `otel_config.py`
- **Telemetry** enabled in production