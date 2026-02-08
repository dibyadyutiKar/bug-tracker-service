"""Project API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DBSession, RequireManager
from app.core.exceptions import (
    AuthorizationError,
    DuplicateError,
    NotFoundError,
)
from app.schemas.base import PaginatedResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectListParams,
    ProjectResponse,
    ProjectUpdate,
    ProjectWithStats,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get(
    "",
    response_model=PaginatedResponse[ProjectResponse],
    summary="List projects",
    description="Get list of projects with filtering, sorting, and pagination.",
)
async def list_projects(
    db: DBSession,
    current_user: CurrentUser,
    search: Optional[str] = Query(None, description="Search in name and description"),
    is_archived: Optional[bool] = Query(False, description="Filter by archived status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: str = Query(
        "created_at",
        pattern=r"^-?(name|created_at|updated_at)$",
        description="Sort field (prefix with - for descending)",
    ),
):
    """List all projects."""
    params = ProjectListParams(
        search=search,
        is_archived=is_archived,
        page=page,
        limit=limit,
        sort=sort,
    )

    project_service = ProjectService(db)
    projects, total = await project_service.list_projects(params)

    total_pages = (total + limit - 1) // limit

    return PaginatedResponse(
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        page=page,
        page_size=limit,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
    description="Create a new project. Requires manager or admin role.",
)
async def create_project(
    data: ProjectCreate,
    db: DBSession,
    current_user: RequireManager,
):
    """Create a new project."""
    try:
        project_service = ProjectService(db)
        project = await project_service.create_project(data, current_user)
        return project
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )


@router.get(
    "/{project_id}",
    response_model=ProjectWithStats,
    summary="Get project details",
    description="Get detailed project information including issue counts.",
)
async def get_project(
    project_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Get project by ID."""
    try:
        project_service = ProjectService(db)
        project = await project_service.get_project(project_id)

        # Build response with stats
        response = ProjectWithStats.model_validate(project)
        response.issue_count = project.issue_count
        response.open_issue_count = project.open_issue_count

        return response
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="Update project details. Requires owner or admin role.",
)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Update a project."""
    try:
        project_service = ProjectService(db)
        project = await project_service.update_project(project_id, data, current_user)
        return project
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )


@router.delete(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Archive project",
    description="Archive a project (soft delete). Requires owner or admin role.",
)
async def archive_project(
    project_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Archive a project."""
    try:
        project_service = ProjectService(db)
        project = await project_service.archive_project(project_id, current_user)
        return project
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )


@router.post(
    "/{project_id}/unarchive",
    response_model=ProjectResponse,
    summary="Unarchive project",
    description="Unarchive a previously archived project.",
)
async def unarchive_project(
    project_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Unarchive a project."""
    try:
        project_service = ProjectService(db)
        project = await project_service.unarchive_project(project_id, current_user)
        return project
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )
