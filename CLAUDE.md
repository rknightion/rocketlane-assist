# Claude Code Context for Rocketlane Assist

## Project Overview

Rocketlane Assist is an AI-powered tool that integrates Rocketlane (a professional service engagement planning and tracking tool) with large language models to help consultants and project managers work more efficiently.

## Architecture

### Backend (FastAPI + Python)
- **Location**: `/backend`
- **Framework**: FastAPI with async support
- **Package Manager**: `uv` for Python dependency management
- **Key Components**:
  - LLM Provider abstraction supporting OpenAI and Anthropic
  - Rocketlane API client for fetching projects and tasks
  - Prompt template system for maintainable AI interactions
  - Configuration management via environment variables

### Frontend (React + TypeScript)
- **Location**: `/frontend`
- **Framework**: React with TypeScript, built with Vite
- **Key Features**:
  - Project listing and detail views
  - Task summarization interface
  - Settings management for API configuration
  - Responsive design with light/dark mode support

## Key Files and Directories

### Backend Structure
```
backend/
├── app/
│   ├── api/          # API routes and endpoints
│   ├── core/         # Core functionality (config, LLM providers)
│   ├── services/     # Business logic (Rocketlane client, summarization)
│   └── prompts/      # AI prompt templates
├── .env              # Configuration file (API keys, settings)
└── pyproject.toml    # Python project configuration
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/   # Reusable React components
│   ├── pages/        # Page components (ProjectList, Settings, etc.)
│   ├── services/     # API client and service layer
│   └── App.tsx       # Main application component
└── package.json      # Node.js project configuration
```

## Development Commands

### Backend
```bash
cd backend
uv sync                           # Install dependencies
uv run uvicorn app.main:app --reload  # Run development server
```

### Frontend
```bash
cd frontend
npm install                       # Install dependencies
npm run dev                       # Run development server
npm run build                     # Build for production
```

### Docker
```bash
docker compose up -d              # Run entire stack
docker compose down               # Stop all services
docker compose logs -f backend    # View backend logs
```

## Configuration

The application uses environment variables for configuration. Key settings:

- `LLM_PROVIDER`: Choose between "openai" or "anthropic"
- `LLM_MODEL`: Model to use (e.g., "gpt-4", "claude-3-opus-20240229")
- `OPENAI_API_KEY`: OpenAI API key (required if using OpenAI)
- `ANTHROPIC_API_KEY`: Anthropic API key (required if using Anthropic)
- `ROCKETLANE_API_KEY`: Rocketlane API key (always required)

## Testing

When testing features:
1. Ensure all API keys are configured in `.env`
2. Check that the Rocketlane API key has proper permissions
3. Verify the selected LLM provider and model are available

## Common Tasks

### Adding a New LLM Provider
1. Create a new provider class in `backend/app/core/llm/`
2. Implement the `BaseLLMProvider` interface
3. Update the provider factory in `provider.py`
4. Add configuration options to `config.py`

### Adding a New Feature
1. Create API endpoint in `backend/app/api/routes/`
2. Implement business logic in `backend/app/services/`
3. Add prompt templates if needed in `backend/app/prompts/templates/`
4. Create frontend components and update API client
5. Update the UI to expose the new functionality

### Updating Prompts
Prompts are stored separately from code in `backend/app/prompts/templates/`. Each feature has its own prompt file for easy maintenance and updates.

## Deployment Considerations

- The application is designed to run in Docker containers
- Frontend is served by nginx with API proxy configuration
- Backend runs with uvicorn in production mode
- All sensitive configuration is handled through environment variables
- Health check endpoints are available at `/health` (backend) and `/` (frontend)

## Future Extensions

The architecture supports adding:
- Additional LLM providers (e.g., Cohere, Hugging Face)
- New Rocketlane integrations (timesheet management, calendar sync)
- Enhanced prompt engineering capabilities
- Multi-tenant support with user authentication
- Caching layer for improved performance

## Debugging Tips

1. Check backend logs for API errors: `docker compose logs backend`
2. Verify API keys are properly set: `GET /api/v1/config/`
3. Test Rocketlane connectivity: `GET /api/v1/projects/`
4. Frontend console for client-side errors
5. Use FastAPI's automatic docs at `/docs` for API testing