from fastapi import APIRouter

from .routes import config, projects, test, users

api_router = APIRouter()
api_router.include_router(projects.router)
api_router.include_router(config.router)
api_router.include_router(users.router)
api_router.include_router(test.router)
