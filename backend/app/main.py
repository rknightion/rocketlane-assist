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
from .services.time_entries_cache import time_entries_cache
from .services.time_entry_categories_cache import time_entry_categories_cache
from .services.user_cache import UserCacheService
from .services.user_statistics_cache import user_statistics_cache
from .services.google_calendar import google_calendar_service

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

        # Build list of cache warming tasks - these don't depend on each other
        warm_tasks = [
            project_cache.warm_cache(),
            user_cache.warm_cache(),
        ]

        # Add user-specific cache warming if user is configured
        if settings.rocketlane_user_id:
            # Calculate current week for time entries cache
            from datetime import datetime, timedelta
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            date_from = start_of_week.strftime("%Y-%m-%d")
            date_to = end_of_week.strftime("%Y-%m-%d")

            warm_tasks.extend([
                user_statistics_cache.warm_cache(),
                tasks_cache_v2.warm_cache(),
                time_entry_categories_cache.warm_cache(),
                time_entries_cache.warm_cache(date_from, date_to),
            ])

        # Start cache warming in background (non-blocking)
        async def warm_caches_in_background():
            try:
                results = await asyncio.gather(*warm_tasks, return_exceptions=True)
                # Log any failures
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Cache warming failed for task {i}: {result}")
                logger.info("Cache warming completed")
            except Exception as e:
                logger.error(f"Error during cache warming: {e}")
        
        # Create background task for cache warming (don't await it)
        cache_warm_task = asyncio.create_task(warm_caches_in_background())
        background_tasks.append(cache_warm_task)

        # Start periodic refresh tasks
        logger.info("Starting periodic cache refresh tasks...")
        project_refresh_task = asyncio.create_task(
            project_cache.refresh_cache_periodically(interval=86400)  # 1 day (changed from 30 min)
        )
        user_refresh_task = asyncio.create_task(
            user_cache.refresh_cache_periodically(interval=86400)  # 1 day (unchanged)
        )

        # Start user-specific cache refresh if user is configured
        if settings.rocketlane_user_id:
            user_stats_refresh_task = asyncio.create_task(
                user_statistics_cache.refresh_cache_periodically(interval=300)  # 5 minutes
            )
            tasks_refresh_task = asyncio.create_task(
                tasks_cache_v2.refresh_cache_periodically(interval=3600)  # 1 hour (changed from 5 min)
            )
            categories_refresh_task = asyncio.create_task(
                time_entry_categories_cache.refresh_cache_periodically(interval=86400)  # 24 hours
            )
            # Note: time_entries_cache doesn't need periodic refresh as it has short TTL (15 min)
            # and is refreshed on demand
            background_tasks.extend([
                project_refresh_task,
                user_refresh_task,
                user_stats_refresh_task,
                tasks_refresh_task,
                categories_refresh_task
            ])
        else:
            background_tasks.extend([project_refresh_task, user_refresh_task])
    
    # Start Google Calendar sync task if authenticated
    async def google_calendar_refresh_task():
        """Periodically sync Google Calendar events if authenticated."""
        while True:
            try:
                status = google_calendar_service.get_status()
                if status.is_authenticated:
                    logger.info("Running periodic Google Calendar sync...")
                    success = await google_calendar_service.sync_events()
                    if success:
                        logger.info(f"Google Calendar sync completed. Events: {len(google_calendar_service.get_cached_events())}")
                    else:
                        logger.warning("Google Calendar sync failed")
                await asyncio.sleep(900)  # 15 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Google Calendar refresh task: {e}")
                await asyncio.sleep(900)  # Continue after error
    
    gcal_task = asyncio.create_task(google_calendar_refresh_task())
    background_tasks.append(gcal_task)

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
