from fastapi import APIRouter

from app.api.v1 import agents, health, me, organizations

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(me.router, tags=["auth"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
