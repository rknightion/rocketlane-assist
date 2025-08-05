# syntax=docker/dockerfile:1

# =============================================================================
# Backend Build Stage
# =============================================================================
FROM python:3.13-slim as backend-builder

# Install uv using the standalone installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install dependencies in a separate layer for better caching
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies without the project itself for better layer caching
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Now copy the rest of the backend code
COPY backend/ ./backend/

# Install the project with compiled bytecode for faster startup
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --compile-bytecode

# =============================================================================
# Frontend Build Stage
# =============================================================================
FROM node:22-alpine as frontend-builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./
RUN npm ci

# Copy source code
COPY frontend/ .

# Build the application
RUN npm run build

# =============================================================================
# Backend Production Stage
# =============================================================================
FROM python:3.13-slim as backend

# Install curl for health checks
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy the virtual environment and application from builder
COPY --from=backend-builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=backend-builder --chown=appuser:appuser /app/backend /app/backend

# Copy entrypoint script
COPY --chmod=755 backend/entrypoint.sh /app/entrypoint.sh

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/backend"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint for permissions handling
ENTRYPOINT ["/app/entrypoint.sh"]

# Run the application - can be overridden for debug mode
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# Frontend Production Stage
# =============================================================================
FROM nginx:alpine as frontend

# Copy built assets from builder
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
