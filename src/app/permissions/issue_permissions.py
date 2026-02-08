"""Issue permission checker."""

from typing import Any, List, Optional

from app.models.user import User
from app.models.issue import Issue
from app.models.enums import UserRole
from app.permissions.base import Action, PermissionChecker


class IssuePermissionChecker(PermissionChecker):
    """Permission checker for Issue resources.

    Permission Matrix:
    - VIEW: All authenticated users
    - CREATE: All authenticated users
    - UPDATE: Reporter, Assignee, Manager, Admin
    - ASSIGN: Reporter, Manager, Admin
    """

    # Base role permissions for each action
    PERMISSIONS = {
        Action.VIEW: [UserRole.DEVELOPER, UserRole.MANAGER, UserRole.ADMIN],
        Action.CREATE: [UserRole.DEVELOPER, UserRole.MANAGER, UserRole.ADMIN],
        Action.UPDATE: [UserRole.DEVELOPER, UserRole.MANAGER, UserRole.ADMIN],
        Action.ASSIGN: [UserRole.MANAGER, UserRole.ADMIN],  # + reporter
    }

    def get_allowed_roles(self, action: Action) -> List[UserRole]:
        """Get base roles allowed for an issue action."""
        return self.PERMISSIONS.get(action, [])

    async def has_permission(
        self,
        user: User,
        action: Action,
        resource: Optional[Any] = None,
    ) -> bool:
        """Check if user has permission for issue action.

        Args:
            user: User requesting permission
            action: Action being performed
            resource: Issue instance (optional for CREATE/VIEW)

        Returns:
            True if permitted, False otherwise
        """
        # Basic role check
        allowed_roles = self.get_allowed_roles(action)
        if user.role not in allowed_roles:
            return False

        # For VIEW and CREATE, role check is sufficient
        if action in (Action.VIEW, Action.CREATE):
            return True

        # For UPDATE - check reporter, assignee, or manager/admin
        if action == Action.UPDATE:
            return self._check_update_permission(user, resource)

        # For ASSIGN - check reporter or manager/admin
        if action == Action.ASSIGN:
            return self._check_assign_permission(user, resource)

        return False

    def _check_update_permission(
        self,
        user: User,
        issue: Optional[Issue],
    ) -> bool:
        """Check if user can update a specific issue.

        Args:
            user: User to check
            issue: Issue to check

        Returns:
            True if user can update issue
        """
        if issue is None:
            return False

        # Manager and admin can update any issue
        if self.is_manager_or_admin(user):
            return True

        # Reporter can update their issue
        if issue.reporter_id == user.id:
            return True

        # Assignee can update assigned issue
        if issue.assignee_id and issue.assignee_id == user.id:
            return True

        return False

    def _check_assign_permission(
        self,
        user: User,
        issue: Optional[Issue],
    ) -> bool:
        """Check if user can change issue assignee.

        Args:
            user: User to check
            issue: Issue to check

        Returns:
            True if user can change assignee
        """
        if issue is None:
            return False

        # Manager and admin can change any assignee
        if self.is_manager_or_admin(user):
            return True

        # Reporter can change assignee on their issue
        if issue.reporter_id == user.id:
            return True

        return False

    def can_view(self, user: User) -> bool:
        """Check if user can view issues."""
        return user.role in self.PERMISSIONS[Action.VIEW]

    def can_create(self, user: User) -> bool:
        """Check if user can create issues."""
        return user.role in self.PERMISSIONS[Action.CREATE]

    def can_update(self, user: User, issue: Issue) -> bool:
        """Check if user can update an issue."""
        return self._check_update_permission(user, issue)

    def can_assign(self, user: User, issue: Issue) -> bool:
        """Check if user can change issue assignee."""
        return self._check_assign_permission(user, issue)

    def can_change_status(self, user: User, issue: Issue) -> bool:
        """Check if user can change issue status."""
        return self.can_update(user, issue)


# Global instance
issue_permission_checker = IssuePermissionChecker()
