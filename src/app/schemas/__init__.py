"""Schemas module - Pydantic schemas for request/response validation."""

from app.schemas.base import (
    BaseSchema,
    BaseResponseSchema,
    PaginatedResponse,
    ErrorResponse,
    ErrorDetail,
)
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    TokenPayload,
    PasswordChangeRequest,
)
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfile,
    UserSummary,
)
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectWithStats,
    ProjectSummary,
    ProjectListParams,
)
from app.schemas.issue import (
    IssueCreate,
    IssueUpdate,
    IssueResponse,
    IssueDetail,
    IssueSummary,
    IssueListParams,
    IssueStatusUpdate,
)
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentListParams,
)

__all__ = [
    # Base
    "BaseSchema",
    "BaseResponseSchema",
    "PaginatedResponse",
    "ErrorResponse",
    "ErrorDetail",
    # Auth
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "TokenPayload",
    "PasswordChangeRequest",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserProfile",
    "UserSummary",
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectWithStats",
    "ProjectSummary",
    "ProjectListParams",
    # Issue
    "IssueCreate",
    "IssueUpdate",
    "IssueResponse",
    "IssueDetail",
    "IssueSummary",
    "IssueListParams",
    "IssueStatusUpdate",
    # Comment
    "CommentCreate",
    "CommentUpdate",
    "CommentResponse",
    "CommentListParams",
]
