"""Permissions module - Role-based access control using Strategy pattern."""

from app.permissions.base import Action, PermissionChecker, PermissionDenied
from app.permissions.project_permissions import (
    ProjectPermissionChecker,
    project_permission_checker,
)
from app.permissions.issue_permissions import (
    IssuePermissionChecker,
    issue_permission_checker,
)
from app.permissions.comment_permissions import (
    CommentPermissionChecker,
    comment_permission_checker,
)

__all__ = [
    "Action",
    "PermissionChecker",
    "PermissionDenied",
    "ProjectPermissionChecker",
    "project_permission_checker",
    "IssuePermissionChecker",
    "issue_permission_checker",
    "CommentPermissionChecker",
    "comment_permission_checker",
]
