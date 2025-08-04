# FastAPI Application Core

## App-Specific Patterns

### Dependency Injection for Services
```python
# dependencies.py
from typing import Annotated
from fastapi import Depends

from .core.config import settings
from .services.rocketlane import RocketlaneService
from .services.summarization import SummarizationService

async def get_rocketlane_service() -> RocketlaneService:
    """Provide Rocketlane service instance."""
    return RocketlaneService(
        api_key=settings.rocketlane_api_key,
        base_url=settings.rocketlane_api_base_url
    )

async def get_summarization_service() -> SummarizationService:
    """Provide AI summarization service."""
    return SummarizationService(settings)

# Type aliases for cleaner route signatures
RocketlaneServiceDep = Annotated[RocketlaneService, Depends(get_rocketlane_service)]
SummarizationServiceDep = Annotated[SummarizationService, Depends(get_summarization_service)]
```

### Service Layer Integration
```python
# In route handlers
@router.get("/projects/{project_id}/summary")
async def get_project_summary(
    project_id: str,
    rocketlane: RocketlaneServiceDep,
    summarizer: SummarizationServiceDep
):
    """Generate AI summary for project tasks."""
    tasks = await rocketlane.get_project_tasks(project_id)
    summary = await summarizer.summarize_tasks(tasks)
    return {"summary": summary, "task_count": len(tasks)}
```

## LLM Provider Integration Pattern
```python
# Using LLM providers in services
from ..core.llm.provider import get_llm_provider

class SummarizationService:
    def __init__(self, settings):
        self.settings = settings
        self.llm = get_llm_provider(settings)

    async def summarize_tasks(self, tasks: List[Dict]) -> str:
        """Generate AI summary of project tasks."""
        prompt = self._build_prompt(tasks)
        return await self.llm.generate_completion(prompt)

    def _build_prompt(self, tasks: List[Dict]) -> str:
        # Use prompt templates from prompts/templates/
        pass
```

## Prompt Template System
```python
# prompts/templates/task_summary.py
from typing import List, Dict

TASK_SUMMARY_TEMPLATE = """
Analyze these project tasks and provide a concise summary:

Tasks ({task_count}):
{task_list}

Provide:
1. Overall status
2. Key risks
3. Next actions
"""

def build_task_summary_prompt(tasks: List[Dict]) -> str:
    task_list = "\n".join([
        f"- {task['title']} ({task['status']})"
        for task in tasks
    ])

    return TASK_SUMMARY_TEMPLATE.format(
        task_count=len(tasks),
        task_list=task_list
    )
```

## Application-Level Error Handling
```python
# main.py - Global exception handlers
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "validation_error"}
    )

@app.exception_handler(httpx.HTTPError)
async def http_error_handler(request: Request, exc: httpx.HTTPError):
    return JSONResponse(
        status_code=502,
        content={"detail": "External service error", "type": "service_error"}
    )
```
