"""Comment API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DBSession
from app.core.exceptions import (
    AuthorizationError,
    BusinessRuleError,
    NotFoundError,
)
from app.schemas.base import PaginatedResponse
from app.schemas.comment import (
    CommentCreate,
    CommentListParams,
    CommentResponse,
    CommentUpdate,
)
from app.services.comment_service import CommentService

router = APIRouter(tags=["Comments"])


@router.get(
    "/issues/{issue_id}/comments",
    response_model=PaginatedResponse[CommentResponse],
    summary="List issue comments",
    description="Get list of comments for an issue with pagination.",
)
async def list_issue_comments(
    issue_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """List comments for an issue."""
    params = CommentListParams(page=page, limit=limit)

    try:
        comment_service = CommentService(db)
        comments, total = await comment_service.list_comments(issue_id, params)

        total_pages = (total + limit - 1) // limit

        return PaginatedResponse(
            items=[CommentResponse.model_validate(c) for c in comments],
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages,
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.post(
    "/issues/{issue_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment",
    description="Add a new comment to an issue.",
)
async def create_comment(
    issue_id: UUID,
    data: CommentCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Create a new comment."""
    try:
        comment_service = CommentService(db)
        comment = await comment_service.create_comment(issue_id, data, current_user)
        return comment
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.patch(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    summary="Edit comment",
    description="Edit a comment. Only the author can edit their comment.",
)
async def update_comment(
    comment_id: UUID,
    data: CommentUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    """Update a comment."""
    try:
        comment_service = CommentService(db)
        comment = await comment_service.update_comment(comment_id, data, current_user)
        return comment
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
