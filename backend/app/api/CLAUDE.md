# API Routes Layer

## Route Testing Commands
```bash
# Test specific endpoints
curl -X GET http://localhost:8000/api/v1/projects/
curl -X GET http://localhost:8000/api/v1/config/
curl -X GET http://localhost:8000/api/v1/users/
curl -X POST http://localhost:8000/api/v1/projects/proj_123/summarize

# Test with authentication (if added)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/projects/
```

## User Filtering Implementation

The API automatically filters tasks based on the configured user ID:

```python
# In project routes
@router.get("/{project_id}/tasks")
async def get_project_tasks(project_id: str, status: str = None):
    user_id = settings.rocketlane_user_id  # From configuration
    tasks = await client.get_project_tasks(project_id, status, user_id)
    return tasks
```

**Key Points:**
- User ID is read from `settings.rocketlane_user_id`
- If user ID is set, tasks are filtered by `assignees.cn={user_id}`
- If user ID is empty/None, all tasks are returned
- User selection is managed through `/api/v1/users/` endpoint

## Route-Specific Patterns

### Pagination for Large Datasets
```python
from fastapi import Query
from typing import List

@router.get("/", response_model=PaginatedResponse)
async def list_items(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search filter")
) -> PaginatedResponse:
    """List items with pagination and search."""
    offset = (page - 1) * per_page

    items = await service.list_items(
        offset=offset,
        limit=per_page,
        search=search
    )
    total = await service.count_items(search=search)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        has_next=(page * per_page) < total,
        has_prev=page > 1
    )
```

### File Upload Endpoints
```python
from fastapi import UploadFile, File

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(..., description="File to upload"),
    metadata: Optional[str] = Form(None)
):
    """Handle file uploads with metadata."""
    if file.content_type not in ["image/jpeg", "image/png", "text/csv"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type"
        )

    # Process file
    content = await file.read()
    result = await process_uploaded_file(content, file.filename)

    return {"filename": file.filename, "size": len(content), "result": result}
```

### Advanced Route Patterns
```python
# Conditional responses based on headers
from fastapi import Header

@router.get("/data")
async def get_data(
    accept: str = Header(default="application/json"),
    format: Optional[str] = Query(None)
):
    """Return data in different formats based on Accept header or query param."""
    data = await service.get_data()

    if format == "csv" or "text/csv" in accept:
        return StreamingResponse(
            generate_csv(data),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=data.csv"}
        )

    return data  # Default JSON response

# Bulk operations
@router.post("/bulk-update")
async def bulk_update(
    operations: List[BulkOperation],
    dry_run: bool = Query(False, description="Preview changes without applying")
):
    """Perform bulk operations on multiple resources."""
    if dry_run:
        return {"preview": await service.preview_bulk_operations(operations)}

    results = await service.execute_bulk_operations(operations)
    return {"processed": len(results), "results": results}

# WebSocket endpoints for real-time features
from fastapi import WebSocket

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Real-time updates via WebSocket."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Process and broadcast
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        await cleanup_client(client_id)
```

## Route-Specific Error Handling
```python
# Custom exception types for specific domains
class ProjectNotFoundError(Exception):
    def __init__(self, project_id: str):
        self.project_id = project_id
        super().__init__(f"Project {project_id} not found")

# Route-specific exception handler
@router.exception_handler(ProjectNotFoundError)
async def project_not_found_handler(request: Request, exc: ProjectNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error": "project_not_found",
            "message": str(exc),
            "project_id": exc.project_id
        }
    )
```

## OpenAPI Customization for Routes
```python
# Custom response examples
@router.post(
    "/analyze",
    responses={
        200: {
            "description": "Analysis completed",
            "content": {
                "application/json": {
                    "example": {
                        "analysis_id": "analysis_123",
                        "status": "completed",
                        "insights": ["High task velocity", "On track for deadline"]
                    }
                }
            }
        },
        422: {
            "description": "Analysis failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Insufficient data for analysis",
                        "required_tasks": 5,
                        "current_tasks": 2
                    }
                }
            }
        }
    }
)
async def analyze_project(project_id: str):
    """Analyze project health and provide insights."""
    pass
```
