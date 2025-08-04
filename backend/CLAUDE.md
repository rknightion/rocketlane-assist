# Backend Development

## Backend-Specific Commands

```bash
# uv Package Management
uv add package-name                    # Add runtime dependency
uv add --dev package-name              # Add development dependency
uv remove package-name                 # Remove dependency
uv tree                               # Show dependency tree
uv sync                               # Install/sync all dependencies

# Development Server Options
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8001  # Alternative port
uv run uvicorn app.main:app --reload --log-level debug             # Debug logging

# Code Quality Tools
uv run ruff check . --fix             # Auto-fix linting issues
uv run ruff format .                  # Format all Python code
uv run mypy .                         # Type checking
uv run pytest -v                     # Verbose test output
uv run pytest --cov=app              # Test coverage report
```

## Python/FastAPI Code Patterns

**Strict Style Requirements:**
- **Double quotes** for strings (ruff configured)
- **100 character line limit**
- **Type hints** mandatory for all functions
- **async/await** for all I/O operations
- **Pydantic models** for data validation

### FastAPI Endpoint Pattern
```python
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

class TaskResponse(BaseModel):
    id: str
    title: str
    status: str

router = APIRouter()

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(project_id: str) -> List[TaskResponse]:
    """Get all tasks for a project."""
    try:
        # Business logic here
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Backend-Specific Testing

```bash
# Run specific test files
uv run pytest tests/test_api.py
uv run pytest tests/test_services.py -v

# Test with coverage
uv run pytest --cov=app --cov-report=html

# Test async functions
uv run pytest -k "async" --asyncio-mode=auto
```

### Test Pattern for Services
```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.example_service import ExampleService

@pytest.mark.asyncio
async def test_service_method():
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"id": "123"}
        mock_client.return_value.get.return_value = mock_response

        service = ExampleService()
        result = await service.get_data("123")
        assert result["id"] == "123"
```

## Python-Specific Patterns

### Async Context Managers
```python
class ServiceClient:
    async def __aenter__(self):
        self.client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

# Usage
async with ServiceClient() as client:
    data = await client.get_data()
```

### Error Handling
```python
from fastapi import HTTPException

def handle_service_error(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"External service error: {e}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return wrapper
```
