# App Core - FastAPI Application Layer

## Dependency Injection Pattern
```python
from typing import Annotated
from fastapi import Depends

# Type aliases for cleaner signatures  
RocketlaneServiceDep = Annotated[RocketlaneService, Depends(get_rocketlane_service)]
SummarizationServiceDep = Annotated[SummarizationService, Depends(get_summarization_service)]

@router.get("/projects/{project_id}/summary")
async def get_summary(
    project_id: str,
    rocketlane: RocketlaneServiceDep,
    summarizer: SummarizationServiceDep
):
    tasks = await rocketlane.get_project_tasks(project_id)
    summary = await summarizer.summarize_tasks(tasks)
    return {"summary": summary, "task_count": len(tasks)}
```

## LLM Integration
```python
from ..core.llm.provider import get_llm_provider

class SummarizationService:
    def __init__(self, settings):
        self.llm = get_llm_provider(settings)

    async def summarize_tasks(self, tasks: List[Dict]) -> str:
        prompt = self._build_prompt(tasks)
        return await self.llm.generate_completion(prompt)
```

## Error Handling
```python
# Global exception handlers in main.py
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(httpx.HTTPError)  
async def http_error_handler(request: Request, exc: httpx.HTTPError):
    return JSONResponse(status_code=502, content={"detail": "External service error"})
```

## App Rules
- **All services** must use dependency injection via `dependencies.py`
- **LLM access** only through `get_llm_provider()` factory
- **User filtering** enforced at service layer
- **Global error handlers** for consistent API responses
