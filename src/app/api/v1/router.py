"""Main API v1 router."""

from fastapi import APIRouter

from app.api.v1 import auth, comments, issues, projects

# Create main v1 router
api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(issues.router)
api_router.include_router(comments.router)
