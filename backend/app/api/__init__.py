from fastapi import APIRouter

from .routes import config, projects, statistics, tasks, test, timesheets, users

api_router = APIRouter()
api_router.include_router(projects.router)
api_router.include_router(config.router)
api_router.include_router(users.router)
api_router.include_router(statistics.router)
api_router.include_router(tasks.router)
api_router.include_router(timesheets.router)
api_router.include_router(test.router)
