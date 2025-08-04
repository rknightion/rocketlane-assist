# Rocketlane Assist

An AI-powered assistant for Rocketlane project management that helps teams summarize tasks and manage projects more efficiently.

## Features

- **Task Summarization**: Generate AI-powered summaries of outstanding project tasks
- **Multi-LLM Support**: Works with both OpenAI and Anthropic APIs
- **Web-based Interface**: Easy-to-use React frontend for managing projects
- **Configurable**: Update settings through the web interface without code changes
- **Docker Support**: Easy deployment with Docker and docker-compose

## Prerequisites

- Docker and Docker Compose (for production deployment)
- Python 3.13+ with `uv` (for development)
- Node.js 20+ (for frontend development)
- API keys for:
  - Rocketlane API
  - OpenAI API and/or Anthropic API

## Quick Start

The fastest way to get started:

```bash
git clone <repository-url>
cd rocketlane-assist
./quickstart.sh
```

This will guide you through the setup process and start the application.

### Manual Setup with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd rocketlane-assist
```

2. Configure your API keys:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

3. Run with Docker Compose:
```bash
docker compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Development Setup

### Backend

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies with uv:
```bash
uv sync
```

3. Run the development server:
```bash
uv run uvicorn app.main:app --reload
```

### Frontend

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

## Configuration

Configure the application through the web interface at `/settings` or by editing the `.env` file:

- `LLM_PROVIDER`: Choose between `openai` or `anthropic`
- `LLM_MODEL`: Specify the model to use (e.g., `gpt-4`, `claude-3-opus-20240229`)
- `OPENAI_API_KEY`: Your OpenAI API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `ROCKETLANE_API_KEY`: Your Rocketlane API key

## API Documentation

The backend API documentation is available at http://localhost:8000/docs when running the application.

### Key Endpoints

- `GET /api/v1/projects/` - List all projects
- `GET /api/v1/projects/{project_id}` - Get project details
- `GET /api/v1/projects/{project_id}/tasks` - Get project tasks
- `POST /api/v1/projects/{project_id}/summarize` - Generate task summary
- `GET /api/v1/config/` - Get current configuration
- `PUT /api/v1/config/` - Update configuration

## Architecture

- **Backend**: FastAPI with async support for handling API requests
- **Frontend**: React with TypeScript and Vite for fast development
- **LLM Integration**: Abstraction layer supporting multiple providers
- **Containerization**: Docker for easy deployment and development

## Development with DevContainers

This project includes DevContainer configuration for VS Code:

1. Install the Remote - Containers extension in VS Code
2. Open the project in VS Code
3. Click "Reopen in Container" when prompted
4. The development environment will be automatically configured

## License

[Add your license information here]