import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .api.dependencies import verify_user_id_configured
from .core.config import settings

# Configure root logger based on DEBUG_MODE environment variable
if os.getenv("DEBUG_MODE", "false").lower() == "true":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        force=True
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        force=True
    )

app = FastAPI(
    title="Rocketlane Assist",
    description="AI-powered assistant for Rocketlane project management",
    version="1.0.0",
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


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Rocketlane Assist API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
