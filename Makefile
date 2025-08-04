# Makefile for Rocketlane Assist
# Convenient commands for development

.PHONY: help install lint lint-fix type-check pre-commit backend-lint frontend-lint

help:
	@echo "Available commands:"
	@echo "  make install      - Install all dependencies and pre-commit hooks"
	@echo "  make lint         - Run linting for both backend and frontend"
	@echo "  make lint-fix     - Fix linting issues automatically"
	@echo "  make type-check   - Run type checking for backend"
	@echo "  make pre-commit   - Run pre-commit hooks on all files"
	@echo "  make test         - Run tests for backend"

install:
	@echo "Installing backend dependencies..."
	cd backend && uv sync
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing pre-commit hooks..."
	pip install pre-commit
	pre-commit install
	@echo "✅ Installation complete!"

lint: backend-lint frontend-lint

backend-lint:
	@echo "Running backend linting..."
	cd backend && uv run ruff check .

frontend-lint:
	@echo "Running frontend linting..."
	cd frontend && npm run lint

lint-fix:
	@echo "Fixing backend linting issues..."
	cd backend && uv run ruff check . --fix && uv run ruff format .
	@echo "Fixing frontend linting issues..."
	cd frontend && npm run lint:fix

type-check:
	@echo "Running type checking for backend..."
	cd backend && uv run mypy .

pre-commit:
	@echo "Running pre-commit hooks..."
	pre-commit run --all-files

test:
	@echo "Running backend tests..."
	cd backend && uv run pytest

# Development shortcuts
dev-backend:
	cd backend && uv run uvicorn app.main:app --reload

dev-frontend:
	cd frontend && npm run dev

dev:
	@echo "Start backend with: make dev-backend"
	@echo "Start frontend with: make dev-frontend"
