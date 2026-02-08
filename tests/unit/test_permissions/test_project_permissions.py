"""Unit tests for project permissions."""

import pytest
from unittest.mock import Mock
from uuid import uuid4

from app.models.enums import UserRole
from app.permissions import Action
from app.permissions.project_permissions import ProjectPermissionChecker


class TestProjectPermissionChecker:
    """Test project permission checker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = ProjectPermissionChecker()

    def _create_mock_user(self, role: UserRole, user_id=None) -> Mock:
        """Create a mock user."""
        user = Mock()
        user.id = user_id or uuid4()
        user.role = role
        return user

    def _create_mock_project(self, created_by_id) -> Mock:
        """Create a mock project."""
        project = Mock()
        project.id = uuid4()
        project.created_by_id = created_by_id
        return project

    def test_developer_can_view(self):
        """Test developer can view projects."""
        user = self._create_mock_user(UserRole.DEVELOPER)
        assert self.checker.can_view(user)

    def test_developer_cannot_create(self):
        """Test developer cannot create projects."""
        user = self._create_mock_user(UserRole.DEVELOPER)
        assert not self.checker.can_create(user)

    def test_manager_can_create(self):
        """Test manager can create projects."""
        user = self._create_mock_user(UserRole.MANAGER)
        assert self.checker.can_create(user)

    def test_admin_can_create(self):
        """Test admin can create projects."""
        user = self._create_mock_user(UserRole.ADMIN)
        assert self.checker.can_create(user)

    def test_owner_can_update(self):
        """Test project owner can update."""
        user_id = uuid4()
        user = self._create_mock_user(UserRole.MANAGER, user_id)
        project = self._create_mock_project(user_id)

        assert self.checker.can_update(user, project)

    def test_non_owner_cannot_update(self):
        """Test non-owner cannot update."""
        user = self._create_mock_user(UserRole.MANAGER)
        project = self._create_mock_project(uuid4())  # Different owner

        assert not self.checker.can_update(user, project)

    def test_admin_can_update_any_project(self):
        """Test admin can update any project."""
        user = self._create_mock_user(UserRole.ADMIN)
        project = self._create_mock_project(uuid4())  # Different owner

        assert self.checker.can_update(user, project)

    def test_owner_can_archive(self):
        """Test project owner can archive."""
        user_id = uuid4()
        user = self._create_mock_user(UserRole.MANAGER, user_id)
        project = self._create_mock_project(user_id)

        assert self.checker.can_archive(user, project)

    @pytest.mark.asyncio
    async def test_has_permission_view(self):
        """Test has_permission for view action."""
        user = self._create_mock_user(UserRole.DEVELOPER)
        result = await self.checker.has_permission(user, Action.VIEW)
        assert result is True

    @pytest.mark.asyncio
    async def test_has_permission_create_denied_for_developer(self):
        """Test has_permission denies create for developer."""
        user = self._create_mock_user(UserRole.DEVELOPER)
        result = await self.checker.has_permission(user, Action.CREATE)
        assert result is False
