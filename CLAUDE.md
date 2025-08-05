# Rocketlane Assist - AI-Powered Project Management Assistant

## IMPORTANT: Configuration and File Management Rules

**NEVER CREATE MULTIPLE VERSIONS OF CONFIGURATION FILES**
- ONE Dockerfile at the root - use multi-stage builds with target names
- ONE docker-compose.yml - use environment variables for different modes
- NO .env files - all defaults are in docker-compose.yml environment section
- Configuration is managed via the web UI and stored in config/settings.json

**Debug Mode:**
- Enable debug logging: `DEBUG_MODE=true docker compose up`
- Do NOT create separate debug files or scripts
- All configuration variations should use environment variables

**File Structure Rules:**
- Never create: Dockerfile.dev, docker-compose.dev.yml, docker-compose.debug.yml
- Never create multiple .env files or .env variants
- Never create debug.sh or similar wrapper scripts
- Keep configuration simple and use environment variables for variations

## Project Overview

Rocketlane Assist is an AI-powered tool that integrates with Rocketlane (a professional service engagement planning and tracking platform) to help consultants and project managers work more efficiently through AI-driven task summarization and project insights.

**Important Note:** Rocketlane API keys are global rather than user-scoped. The application requires users to specify which user account they want to filter by during onboarding and configuration. All API queries will filter tasks and projects based on the selected user ID.

**User ID Enforcement:** The application enforces user selection through:
- Backend middleware that blocks all API calls (except /users and /config) without a configured user ID
- Frontend warnings and error messages when user is not selected
- Automatic filtering of tasks to show only those assigned to the selected user
- Clear error messages (HTTP 403) when operations are attempted without user context

**Key Features:**
- Task summarization using OpenAI or Anthropic APIs
- Multi-LLM provider support with easy switching
- Web-based interface for project management
- User-specific task filtering (tasks assigned to selected user)
- Configurable settings through UI
- Docker-based deployment

## Quick Start Commands

**IMPORTANT: Run these from the project root directory**

```bash
# Production mode
docker compose up -d                      # Run entire stack
docker compose down                       # Stop all services

# Debug mode (with verbose logging)
DEBUG_MODE=true docker compose up         # Run with debug logging
DEBUG_MODE=true docker compose up -d      # Run in background with debug logging

# Development workflow (without Docker)
cd backend && uv sync && uv run uvicorn app.main:app --reload  # Backend dev
cd frontend && npm install && npm run dev                      # Frontend dev

# Health checks
curl http://localhost:8000/health         # Backend health
curl http://localhost:3000               # Frontend access
curl http://localhost:8000/docs          # API documentation

# View logs
docker compose logs -f backend            # Backend logs
docker compose logs -f frontend           # Frontend logs
```

## Architecture Overview

### Technology Stack
- **Backend**: FastAPI (Python) with async support
- **Frontend**: React + TypeScript with Vite
- **Package Management**: `uv` (Python), `npm` (Node.js)
- **Deployment**: Docker + docker-compose
- **LLM Integration**: OpenAI and Anthropic APIs
- **External API**: Rocketlane project management platform

### Directory Structure
```
rocketlane-assist/
├── backend/                  # Python FastAPI application
│   ├── app/                 # Application source code
│   │   ├── api/            # REST API routes and endpoints
│   │   ├── core/           # Core functionality (config, LLM providers)
│   │   ├── services/       # Business logic and external integrations
│   │   └── prompts/        # AI prompt templates
│   ├── .env.example        # Environment configuration template
│   └── pyproject.toml      # Python dependencies and tooling
├── frontend/               # React TypeScript application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/         # Route-level page components
│   │   ├── services/      # API client and HTTP layer
│   │   ├── hooks/         # Custom React hooks
│   │   └── stores/        # Global state management (Zustand)
│   └── package.json       # Node.js dependencies and scripts
├── docker-compose.yml      # Container orchestration
└── TODOs.txt              # Future feature roadmap
```

## Configuration Management

**Initial Setup:**

1. Start the application: `docker compose up -d`
2. Navigate to http://localhost:3000/settings
3. Configure your API keys through the web UI:
   - Choose LLM Provider (OpenAI or Anthropic)
   - Enter the appropriate API key
   - Enter your Rocketlane API key
   - Select a user from the dropdown (required)

**Environment Variables (Optional):**
You can override defaults when starting the application:
```bash
# Examples:
OPENAI_API_KEY=sk-... docker compose up -d
DEBUG_MODE=true docker compose up
LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-... docker compose up -d
```

All configuration is persisted in `config/settings.json` and can be updated via the web UI.

**Configuration Access:**
- UI Settings: http://localhost:3000/settings
- API Config: `GET /api/v1/config/`
- Environment variables override UI settings

## Development Workflow

### Code Style Guidelines

**Backend (Python):**
- Use **double quotes** for strings
- **100 character line limit**
- **Type hints** for all functions
- **async/await** for I/O operations
- **Pydantic models** for data validation
- Run: `uv run ruff check . --fix && uv run ruff format .`

**Frontend (TypeScript):**
- Use **ES modules** (import/export)
- **Destructure imports** when possible
- **Functional components** with hooks
- **TypeScript** for all new code
- **2-space indentation**
- Run: `npm run lint`

### Testing and Quality

```bash
# Backend testing
cd backend
uv run pytest                        # Run tests
uv run mypy .                        # Type checking
uv run ruff check .                  # Linting

# Frontend testing
cd frontend
npm run lint                         # ESLint checking
npm run build                       # Production build test
```

## API Reference

**Base URLs:**
- Backend API: http://localhost:8000
- Frontend UI: http://localhost:3000
- API Docs: http://localhost:8000/docs

**Key Endpoints:**
```bash
# Project Management
GET    /api/v1/projects/                    # List all projects
GET    /api/v1/projects/{project_id}        # Get project details
GET    /api/v1/projects/{project_id}/tasks  # Get project tasks
POST   /api/v1/projects/{project_id}/summarize  # Generate AI summary

# Configuration
GET    /api/v1/config/                      # Get current settings
PUT    /api/v1/config/                      # Update settings

# Health & Status
GET    /health                              # Backend health check
GET    /                                    # API root information
```

## Adding New Features

### Backend API Endpoint
1. **Create route**: `backend/app/api/routes/new_feature.py`
2. **Add business logic**: `backend/app/services/new_feature_service.py`
3. **Update router**: Include in `backend/app/api/__init__.py`
4. **Add Pydantic models** for request/response validation

### Frontend Component
1. **Create component**: `frontend/src/components/NewFeature.tsx`
2. **Add API functions**: `frontend/src/services/api.ts`
3. **Update routing**: Add route in `frontend/src/App.tsx`
4. **Add navigation** if needed

### LLM Provider Integration
1. **Create provider class**: `backend/app/core/llm/new_provider.py`
2. **Inherit from** `BaseLLMProvider`
3. **Update factory**: `backend/app/core/llm/provider.py`
4. **Add configuration**: `backend/app/core/config.py`

## Troubleshooting

### Common Issues

**Backend Won't Start:**
- Check `.env` file exists in `backend/` directory
- Verify API keys are valid and properly formatted
- Run `uv sync` to ensure dependencies are installed
- Check port 8000 isn't already in use

**Frontend Can't Connect to Backend:**
- Verify backend is running on port 8000
- Check CORS settings in `backend/app/core/config.py`
- Confirm `VITE_API_URL` environment variable (if set)

**LLM API Errors:**
- Verify API keys are active and have sufficient credits
- Check model names are correct (case-sensitive)
- Ensure rate limits aren't exceeded

**Docker Issues:**
- Run `docker compose down && docker compose up -d` to restart
- Check logs: `docker compose logs -f backend` or `docker compose logs -f frontend`
- Verify `.env` file is in backend directory

### Debugging Commands

```bash
# Check configuration
curl http://localhost:8000/api/v1/config/

# Test Rocketlane connectivity
curl http://localhost:8000/api/v1/projects/

# View application logs
docker compose logs -f backend
docker compose logs -f frontend

# Backend development with debug logging
cd backend && uv run uvicorn app.main:app --reload --log-level debug
```

## Deployment

### Production Deployment
```bash
# Build and run production containers
docker compose -f docker-compose.yml up -d

# Health verification
curl http://your-domain/health
curl http://your-domain/api/v1/config/
```

### Environment-Specific Configurations
- **Development**: Use `docker-compose.dev.yml` for hot reload
- **Production**: Use `docker-compose.yml` for optimized builds
- **Security**: Ensure `.env` files are never committed to git

## Project Roadmap

**Current Status:** MVP with core functionality complete
**Next Priorities:** (See `TODOs.txt` for full roadmap)
- Authentication and user management
- Enhanced AI features (risk assessment, timeline generation)
- Google Calendar integration
- Mobile responsiveness improvements

## Security Notes

**IMPORTANT Security Practices:**
- **Never commit** `.env` files or API keys to version control
- **Use `.env.example`** as template for environment setup
- **Rotate API keys** regularly
- **Limit API key permissions** to minimum required scope
- **Monitor API usage** to detect unusual activity

## Rocketlane API Integration

**API Documentation References:**
- **Quick Start Guide**: Use Context7 MCP with project ID `developer_rocketlane` for basic API information
- **Detailed Reference**: Use Context7 MCP with project ID `developer_rocketlane-v1.3` for comprehensive API documentation

**Key API Endpoints Used:**
- `GET /users` - Fetch all users for user selection dropdown
- `GET /projects` - List all projects
- `GET /projects/{project_id}` - Get project details
- `GET /tasks` - Get tasks with filtering support:
  - Filter by project: `filters=project.eq={project_id}`
  - Filter by status: `filters=status.eq={status_value}`
  - Filter by assignee: `filters=assignees.cn={user_id}`
  - Multiple filters: Combine with commas

**User Filtering Implementation:**
The application filters tasks based on the selected user ID:
1. User selects their account during onboarding or in settings
2. User ID is stored in configuration (`ROCKETLANE_USER_ID`)
3. All task queries include `assignees.cn={user_id}` filter
4. Time entry operations automatically use the configured user ID
5. Future features (timesheet generation, calendar sync) will use this user context

**Operations That Require User Context:**
- Viewing/summarizing tasks (filtered by assignee)
- Creating time entries (uses configured user ID)
- Future: Timesheet generation (for the selected user)
- Future: Calendar synchronization (user's calendar events)
- Future: Task recommendations (based on user's workload)

## Contributing

**Before Making Changes:**
1. Read the appropriate directory's `CLAUDE.md` file for specific guidelines
2. Follow established code style and patterns
3. Update tests when adding new functionality
4. Run linting and type checking before committing
5. Test both backend and frontend integration

**Documentation:**
- Update relevant `CLAUDE.md` files when changing patterns
- Add API documentation for new endpoints
- Update `TODOs.txt` when completing or adding features
