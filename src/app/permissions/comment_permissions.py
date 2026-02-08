"""Comment permission checker."""

from typing import Any, List, Optional

from app.models.user import User
from app.models.comment import Comment
from app.models.enums import UserRole
from app.permissions.base import Action, PermissionChecker


class CommentPermissionChecker(PermissionChecker):
    """Permission checker for Comment resources.

    Permission Matrix:
    - VIEW: All authenticated users
    - CREATE: All authenticated users
    - UPDATE: Author only
    - DELETE: Not allowed (audit trail)
    """

    # Base role permissions for each action
    PERMISSIONS = {
        Action.VIEW: [UserRole.DEVELOPER, UserRole.MANAGER, UserRole.ADMIN],
        Action.CREATE: [UserRole.DEVELOPER, UserRole.MANAGER, UserRole.ADMIN],
        Action.UPDATE: [UserRole.DEVELOPER, UserRole.MANAGER, UserRole.ADMIN],
        Action.DELETE: [],  # Comments cannot be deleted
    }

    def get_allowed_roles(self, action: Action) -> List[UserRole]:
        """Get base roles allowed for a comment action."""
        return self.PERMISSIONS.get(action, [])

    async def has_permission(
        self,
        user: User,
        action: Action,
        resource: Optional[Any] = None,
    ) -> bool:
        """Check if user has permission for comment action.

        Args:
            user: User requesting permission
            action: Action being performed
            resource: Comment instance (optional for CREATE/VIEW)

        Returns:
            True if permitted, False otherwise
        """
        # DELETE is never allowed (audit trail)
        if action == Action.DELETE:
            return False

        # Basic role check
        allowed_roles = self.get_allowed_roles(action)
        if user.role not in allowed_roles:
            return False

        # For VIEW and CREATE, role check is sufficient
        if action in (Action.VIEW, Action.CREATE):
            return True

        # For UPDATE - only author can edit
        if action == Action.UPDATE:
            return self._check_update_permission(user, resource)

        return False

    def _check_update_permission(
        self,
        user: User,
        comment: Optional[Comment],
    ) -> bool:
        """Check if user can update a specific comment.

        Only the author can edit their own comment.

        Args:
            user: User to check
            comment: Comment to check

        Returns:
            True if user can update comment
        """
        if comment is None:
            return False

        # Only author can edit
        return comment.author_id == user.id

    def can_view(self, user: User) -> bool:
        """Check if user can view comments."""
        return user.role in self.PERMISSIONS[Action.VIEW]

    def can_create(self, user: User) -> bool:
        """Check if user can create comments."""
        return user.role in self.PERMISSIONS[Action.CREATE]

    def can_update(self, user: User, comment: Comment) -> bool:
        """Check if user can update a comment."""
        return self._check_update_permission(user, comment)

    def can_delete(self, user: User, comment: Comment) -> bool:
        """Check if user can delete a comment.

        Always returns False - comments cannot be deleted.
        """
        return False


# Global instance
comment_permission_checker = CommentPermissionChecker()
