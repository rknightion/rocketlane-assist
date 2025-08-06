# Backend - FastAPI Python

## Package Management
```bash
uv add package-name                    # Add dependency
uv add --dev package-name              # Add dev dependency  
uv sync                               # Install/sync all
uv tree                               # Show tree
```

## Development
```bash
uv run uvicorn app.main:app --reload --port 8001    # Alt port
uv run uvicorn app.main:app --reload --log-level debug  # Debug
uv run ruff check . --fix && uv run ruff format .   # Format
uv run mypy . && uv run pytest -v                   # Check & test
```

## FastAPI Patterns
**Required:**
- Double quotes, 100 char limit
- Type hints, async/await for I/O
- Pydantic models for validation

```python
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

class TaskResponse(BaseModel):
    id: str
    title: str
    status: str

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(project_id: str) -> List[TaskResponse]:
    """Get tasks for project."""
    try:
        return await service.get_tasks(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Testing
```bash
uv run pytest tests/test_api.py -v           # Specific tests
uv run pytest --cov=app --cov-report=html   # Coverage
uv run pytest -k "async" --asyncio-mode=auto # Async tests
```

```python
@pytest.mark.asyncio
async def test_service():
    with patch('httpx.AsyncClient') as mock:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"id": "123"}
        mock.return_value.get.return_value = mock_response
        
        result = await service.get_data("123")
        assert result["id"] == "123"
```

## Project-Specific Rules
- **User filtering required** - all task endpoints must filter by `assignees.cn={user_id}`
- **Dependency injection** - use typed dependencies from `app.api.dependencies`
- **LLM providers** - access via `get_llm_provider(settings)` factory
- **Error handling** - use HTTPException with proper status codes
