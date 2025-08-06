# API Routes Layer

## Testing Routes
```bash
curl -X GET http://localhost:8000/api/v1/projects/
curl -X GET http://localhost:8000/api/v1/config/
curl -X POST http://localhost:8000/api/v1/projects/proj_123/summarize
```

## User Filtering (Required)
```python
@router.get("/{project_id}/tasks")
async def get_project_tasks(project_id: str, status: str = None):
    user_id = settings.rocketlane_user_id  # From config
    tasks = await client.get_project_tasks(project_id, status, user_id)
    return tasks
```

**Key Points:**
- User ID from `settings.rocketlane_user_id`
- Tasks filtered by `assignees.cn={user_id}`
- No user ID = return all tasks
- User management via `/api/v1/users/`

## Route Patterns

### Pagination
```python
@router.get("/", response_model=PaginatedResponse)
async def list_items(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None)
):
    offset = (page - 1) * per_page
    items = await service.list_items(offset=offset, limit=per_page, search=search)
    total = await service.count_items(search=search)
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)
```

### File Upload
```python
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "text/csv"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    content = await file.read()
    return {"filename": file.filename, "size": len(content)}
```

## Route Rules
- **All routes** must validate user context (except `/users`, `/config`)
- **Pydantic models** for request/response validation
- **HTTPException** for errors with proper status codes
- **Custom exceptions** for domain-specific errors
- **OpenAPI examples** for complex endpoints
