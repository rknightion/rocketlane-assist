# Rocketlane Assist - AI Project Management Tool

## Critical Configuration Rules
- **ONE Dockerfile** - multi-stage builds only
- **ONE docker-compose.yml** - use env vars for modes  
- **NO .env files** - defaults in docker-compose.yml
- **Web UI config** - stored in config/settings.json
- **Debug mode**: `DEBUG_MODE=true docker compose up`

## Project Context
AI-powered Rocketlane integration for task summarization and project insights.

**User Filtering Required:**
- Rocketlane API keys are global (not user-scoped)
- Must select user during onboarding
- All operations filter by configured user ID
- No user = HTTP 403 errors

**Tech Stack:**
- Backend: FastAPI + Python + async
- Frontend: React + TypeScript + Vite  
- Package: `uv` (Python), `npm` (Node)
- Deploy: Docker + docker-compose
- AI: OpenAI/Anthropic APIs

## Essential Commands
```bash
# Production
docker compose up -d                    # Start stack  
docker compose down                     # Stop stack
DEBUG_MODE=true docker compose up       # Debug mode

# Development  
cd backend && uv sync && uv run uvicorn app.main:app --reload
cd frontend && npm install && npm run dev

# Health checks
curl http://localhost:8000/health       # Backend
curl http://localhost:3000             # Frontend  
curl http://localhost:8000/docs        # API docs
```

## Architecture
```
backend/app/
├── api/           # REST endpoints
├── core/          # Config, LLM providers  
├── services/      # Business logic
└── prompts/       # AI templates

frontend/src/
├── components/    # UI components
├── pages/         # Route components
├── services/      # API layer
├── hooks/         # Custom hooks
└── stores/        # State (Zustand)
```

## Setup & Configuration
1. Start: `docker compose up -d`
2. Navigate: http://localhost:3000/settings  
3. Configure:
   - LLM Provider (OpenAI/Anthropic) + API key
   - Rocketlane API key
   - **Select user** (required for filtering)

**Config stored in:** `config/settings.json`

## Code Standards
**Python:**
- Double quotes, 100 char limit, type hints
- async/await for I/O, Pydantic models
- `uv run ruff check . --fix && uv run ruff format .`

**TypeScript:**  
- ES modules, destructure imports, functional components
- 2-space indent, TypeScript mandatory
- `npm run lint`

## Key Endpoints
```bash
GET /api/v1/projects/                    # List projects
GET /api/v1/projects/{id}/tasks          # Get tasks
POST /api/v1/projects/{id}/summarize     # AI summary
GET /api/v1/config/                      # Settings
```

## Security Rules
- **NEVER commit** API keys to git
- **Rotate keys** regularly  
- **Monitor API usage** for unusual activity

## Rocketlane API Notes
- **Docs**: Use Context7 MCP with `developer_rocketlane-v1.3` as the library
- **Task filters**: `assignees.cn={user_id}`, `project.eq={id}`, `status.eq={value}`
- **User context required** for all task operations

## Contributing
1. Read directory-specific `CLAUDE.md` files
2. Follow code standards above
3. Run linting before commit
4. Update tests and documentation
