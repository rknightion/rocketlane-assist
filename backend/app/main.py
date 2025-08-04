from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .api.dependencies import verify_user_id_configured
from .core.config import settings

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
    await verify_user_id_configured(request)
    response = await call_next(request)
    return response


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
