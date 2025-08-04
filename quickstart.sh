#!/bin/bash

# Rocketlane Assist Quick Start Script

set -e

echo "🚀 Rocketlane Assist - Quick Start Setup"
echo "========================================"
echo ""

# Check for required commands
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed. Please install $1 to continue."
        exit 1
    fi
}

echo "Checking prerequisites..."
check_command docker
check_command docker compose
echo "✅ All prerequisites installed!"
echo ""

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "Creating .env file..."
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🔑 API Key Configuration Required"
echo "================================"
echo ""
echo "Please update the following in backend/.env:"
echo "  - ROCKETLANE_API_KEY: Your Rocketlane API key"
echo "  - OPENAI_API_KEY: Your OpenAI API key (if using OpenAI)"
echo "  - ANTHROPIC_API_KEY: Your Anthropic API key (if using Anthropic)"
echo ""
echo "Get your Rocketlane API key from:"
echo "  1. Log into your Rocketlane account"
echo "  2. Click your profile icon → Settings → API"
echo "  3. Create a new API key"
echo ""

read -p "Press Enter when you've updated your API keys..."

echo ""
echo "Building Docker images..."
docker compose build

echo ""
echo "Starting services..."
docker compose up -d

echo ""
echo "✅ Rocketlane Assist is now running!"
echo ""
echo "Access the application at:"
echo "  - Frontend: http://localhost:3000"
echo "  - API Documentation: http://localhost:8000/docs"
echo ""
echo "To stop the services, run: docker compose down"
echo "To view logs, run: docker compose logs -f"
echo ""