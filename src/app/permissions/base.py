"""Base permission checker interface using Strategy pattern."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, List, Optional

from app.models.user import User
from app.models.enums import UserRole


class Action(str, Enum):
    """Permission actions."""

    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ARCHIVE = "archive"
    ASSIGN = "assign"


class PermissionChecker(ABC):
    """Abstract base class for permission checkers.

    Implements Strategy pattern for interchangeable permission algorithms.
    """

    @abstractmethod
    async def has_permission(
        self,
        user: User,
        action: Action,
        resource: Optional[Any] = None,
    ) -> bool:
        """Check if user has permission for an action on a resource.

        Args:
            user: User requesting permission
            action: Action being performed
            resource: Optional resource being accessed

        Returns:
            True if permitted, False otherwise
        """
        pass

    @abstractmethod
    def get_allowed_roles(self, action: Action) -> List[UserRole]:
        """Get roles allowed for a specific action.

        Args:
            action: Action to check

        Returns:
            List of allowed roles
        """
        pass

    def is_admin(self, user: User) -> bool:
        """Check if user is admin."""
        return user.role == UserRole.ADMIN

    def is_manager(self, user: User) -> bool:
        """Check if user is manager."""
        return user.role == UserRole.MANAGER

    def is_manager_or_admin(self, user: User) -> bool:
        """Check if user is manager or admin."""
        return user.role in (UserRole.MANAGER, UserRole.ADMIN)


class PermissionDenied(Exception):
    """Exception raised when permission is denied."""

    def __init__(self, message: str = "Permission denied"):
        self.message = message
        super().__init__(self.message)
