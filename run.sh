#!/bin/bash

# Rocketlane Assist Development Runner

set -e

echo "🚀 Rocketlane Assist Development Environment"
echo "==========================================="

# Check if .env file exists
if [ ! -f backend/.env ]; then
    echo "⚠️  No .env file found. Creating from example..."
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env - Please update with your API keys!"
fi

# Parse command
case "$1" in
    "dev")
        echo "Starting development servers..."
        echo ""
        echo "Backend will be available at: http://localhost:8000"
        echo "Frontend will be available at: http://localhost:3000"
        echo "API documentation at: http://localhost:8000/docs"
        echo ""
        
        # Start backend
        cd backend
        echo "Installing backend dependencies..."
        uv sync
        echo "Starting backend server..."
        uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        
        # Start frontend
        cd ../frontend
        echo "Installing frontend dependencies..."
        npm install
        echo "Starting frontend server..."
        npm run dev &
        FRONTEND_PID=$!
        
        # Wait for both processes
        wait $BACKEND_PID $FRONTEND_PID
        ;;
        
    "docker")
        echo "Starting with Docker Compose (production mode)..."
        docker compose up -d
        echo ""
        echo "✅ Services started!"
        echo "Frontend: http://localhost:3000"
        echo "Backend API: http://localhost:8000"
        echo "API Docs: http://localhost:8000/docs"
        ;;
        
    "docker-dev")
        echo "Starting with Docker Compose (development mode with hot-reload)..."
        docker compose -f docker-compose.dev.yml up
        ;;
        
    "docker-build")
        echo "Building Docker images..."
        docker compose build
        ;;
        
    "docker-build-dev")
        echo "Building development Docker images..."
        docker compose -f docker-compose.dev.yml build
        ;;
        
    "docker-stop")
        echo "Stopping Docker services..."
        docker compose down
        docker compose -f docker-compose.dev.yml down
        ;;
        
    "test")
        echo "Running tests..."
        cd backend
        uv run pytest
        ;;
        
    *)
        echo "Usage: ./run.sh [command]"
        echo ""
        echo "Commands:"
        echo "  dev          - Start development servers (backend + frontend)"
        echo "  docker       - Start with Docker Compose (production mode)"
        echo "  docker-dev   - Start with Docker Compose (development mode with hot-reload)"
        echo "  docker-build - Build Docker images (production)"
        echo "  docker-build-dev - Build Docker images (development)"
        echo "  docker-stop  - Stop Docker services"
        echo "  test         - Run tests"
        ;;
esac