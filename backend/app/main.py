import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .api.dependencies import verify_user_id_configured
from .core.config import settings
from .core.otel_config import configure_otel
from .core.telemetry import instrument_app
from .services.project_cache_v2 import ProjectCacheService
from .services.tasks_cache_v2 import tasks_cache_v2
from .services.time_entry_categories_cache import time_entry_categories_cache
from .services.user_cache import UserCacheService
from .services.user_statistics_cache import user_statistics_cache

# Configure OpenTelemetry BEFORE creating the app
configure_otel()

# Configure root logger based on DEBUG_MODE environment variable
if os.getenv("DEBUG_MODE", "false").lower() == "true":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        force=True,
    )
else:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", force=True
    )

logger = logging.getLogger(__name__)

# Cache services
project_cache = ProjectCacheService()
user_cache = UserCacheService()

# Background tasks
background_tasks = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup
    logger.info("Starting application...")
    
    # Warm caches if API keys are configured
    if settings.rocketlane_api_key:
        logger.info("Warming caches at startup...")
        
        # Warm caches concurrently
        try:
            await asyncio.gather(
                project_cache.warm_cache(),
                user_cache.warm_cache(),
                return_exceptions=True
            )
            logger.info("Cache warming completed")
        except Exception as e:
            logger.error(f"Error during cache warming: {e}")
        
        # Start periodic refresh tasks
        logger.info("Starting periodic cache refresh tasks...")
        project_refresh_task = asyncio.create_task(
            project_cache.refresh_cache_periodically(interval=1800)  # 30 minutes
        )
        user_refresh_task = asyncio.create_task(
            user_cache.refresh_cache_periodically(interval=3600)  # 1 hour
        )
        
        # Start user-specific cache refresh if user is configured
        if settings.rocketlane_user_id:
            user_stats_refresh_task = asyncio.create_task(
                user_statistics_cache.refresh_cache_periodically(interval=300)  # 5 minutes
            )
            tasks_refresh_task = asyncio.create_task(
                tasks_cache_v2.refresh_cache_periodically(interval=300)  # 5 minutes
            )
            categories_refresh_task = asyncio.create_task(
                time_entry_categories_cache.refresh_cache_periodically(interval=86400)  # 24 hours
            )
            background_tasks.extend([project_refresh_task, user_refresh_task, user_stats_refresh_task, tasks_refresh_task, categories_refresh_task])
        else:
            background_tasks.extend([project_refresh_task, user_refresh_task])
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Cancel background tasks
    for task in background_tasks:
        task.cancel()
    
    # Wait for tasks to complete cancellation
    if background_tasks:
        await asyncio.gather(*background_tasks, return_exceptions=True)
    
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Rocketlane Assist",
    description="AI-powered assistant for Rocketlane project management",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add middleware to enforce user ID requirement
@app.middleware("http")
async def enforce_user_id_middleware(request: Request, call_next):
    """Middleware to enforce user ID configuration for protected endpoints"""
    try:
        await verify_user_id_configured(request)
        response = await call_next(request)
        return response
    except Exception as e:
        # Log the exception with full traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error in middleware: {e}", exc_info=True)
        raise


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Initialize OpenTelemetry instrumentation
instrument_app(app)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Rocketlane Assist API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
