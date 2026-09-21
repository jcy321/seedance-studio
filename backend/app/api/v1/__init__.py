from fastapi import APIRouter

from app.api.v1.endpoints import (
    health, auth, projects, scripts, characters, storyboards,
    assets, generation, ws, user, asset_management, generation_tasks
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(projects.router)
api_router.include_router(scripts.router)
api_router.include_router(characters.router)
api_router.include_router(storyboards.router)
api_router.include_router(assets.router)
api_router.include_router(generation.router)
api_router.include_router(asset_management.router)
api_router.include_router(generation_tasks.router)
api_router.include_router(ws.router)
