"""Project permission checker."""

from typing import Any, List, Optional

from app.models.user import User
from app.models.project import Project
from app.models.enums import UserRole
from app.permissions.base import Action, PermissionChecker


class ProjectPermissionChecker(PermissionChecker):
    """Permission checker for Project resources.

    Permission Matrix:
    - VIEW: All authenticated users
    - CREATE: Manager, Admin only
    - UPDATE: Project owner, Admin
    - DELETE/ARCHIVE: Project owner, Admin
    """

    # Role permissions for each action
    PERMISSIONS = {
        Action.VIEW: [UserRole.DEVELOPER, UserRole.MANAGER, UserRole.ADMIN],
        Action.CREATE: [UserRole.MANAGER, UserRole.ADMIN],
        Action.UPDATE: [UserRole.MANAGER, UserRole.ADMIN],
        Action.DELETE: [UserRole.MANAGER, UserRole.ADMIN],
        Action.ARCHIVE: [UserRole.MANAGER, UserRole.ADMIN],
    }

    def get_allowed_roles(self, action: Action) -> List[UserRole]:
        """Get roles allowed for a project action."""
        return self.PERMISSIONS.get(action, [])

    async def has_permission(
        self,
        user: User,
        action: Action,
        resource: Optional[Any] = None,
    ) -> bool:
        """Check if user has permission for project action.

        Args:
            user: User requesting permission
            action: Action being performed
            resource: Project instance (optional for CREATE/VIEW)

        Returns:
            True if permitted, False otherwise
        """
        # Check if user's role is allowed for this action
        allowed_roles = self.get_allowed_roles(action)
        if user.role not in allowed_roles:
            return False

        # For CREATE and VIEW actions, role check is sufficient
        if action in (Action.CREATE, Action.VIEW):
            return True

        # For UPDATE, DELETE, ARCHIVE - check ownership
        if action in (Action.UPDATE, Action.DELETE, Action.ARCHIVE):
            return self._check_modify_permission(user, resource)

        return False

    def _check_modify_permission(
        self,
        user: User,
        project: Optional[Project],
    ) -> bool:
        """Check if user can modify a specific project.

        Args:
            user: User to check
            project: Project to check

        Returns:
            True if user can modify project
        """
        if project is None:
            return False

        # Admin can modify any project
        if self.is_admin(user):
            return True

        # Only creator can modify (for managers)
        return project.created_by_id == user.id

    def can_view(self, user: User) -> bool:
        """Check if user can view projects."""
        return user.role in self.PERMISSIONS[Action.VIEW]

    def can_create(self, user: User) -> bool:
        """Check if user can create projects."""
        return user.role in self.PERMISSIONS[Action.CREATE]

    def can_update(self, user: User, project: Project) -> bool:
        """Check if user can update a project."""
        if self.is_admin(user):
            return True
        if user.role == UserRole.MANAGER and project.created_by_id == user.id:
            return True
        return False

    def can_archive(self, user: User, project: Project) -> bool:
        """Check if user can archive a project."""
        return self.can_update(user, project)


# Global instance
project_permission_checker = ProjectPermissionChecker()
