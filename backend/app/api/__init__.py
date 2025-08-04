from fastapi import APIRouter
from .routes import projects, config

api_router = APIRouter()
api_router.include_router(projects.router)
api_router.include_router(config.router)