"""Project service."""

from typing import Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthorizationError,
    DuplicateError,
    NotFoundError,
)
from app.models.project import Project
from app.models.user import User
from app.models.enums import UserRole
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectListParams, ProjectUpdate


class ProjectService:
    """Project service for project management operations."""

    def __init__(self, session: AsyncSession):
        """Initialize project service with database session.

        Args:
            session: Async database session
        """
        self.session = session
        self.project_repo = ProjectRepository(session)

    async def get_project(self, project_id: UUID) -> Project:
        """Get project by ID with creator loaded.

        Args:
            project_id: Project UUID

        Returns:
            Project instance

        Raises:
            NotFoundError: If project not found
        """
        project = await self.project_repo.get_with_creator(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        return project

    async def get_project_with_stats(self, project_id: UUID) -> Project:
        """Get project by ID with creator and issues loaded for stats.

        Args:
            project_id: Project UUID

        Returns:
            Project instance with issues loaded

        Raises:
            NotFoundError: If project not found
        """
        project = await self.project_repo.get_with_stats(project_id)
        if not project:
            raise NotFoundError("Project", project_id)
        return project

    async def list_projects(
        self,
        params: ProjectListParams,
    ) -> Tuple[list[Project], int]:
        """List projects with filtering and pagination.

        Args:
            params: Query parameters

        Returns:
            Tuple of (projects list, total count)
        """
        return await self.project_repo.list_projects(params)

    async def create_project(
        self,
        data: ProjectCreate,
        current_user: User,
    ) -> Project:
        """Create a new project.

        Args:
            data: Project creation data
            current_user: User creating the project

        Returns:
            Created project

        Raises:
            AuthorizationError: If user cannot create projects
            DuplicateError: If project name already exists
        """
        # Check if user can create projects
        if not current_user.can_create_project:
            raise AuthorizationError(
                "Only managers and admins can create projects"
            )

        # Check for duplicate name
        if await self.project_repo.name_exists(data.name):
            raise DuplicateError("project name", data.name)

        # Create project
        project = await self.project_repo.create({
            "name": data.name,
            "description": data.description,
            "created_by_id": current_user.id,
            "is_archived": False,
        })

        # Load creator relationship
        return await self.get_project(project.id)

    async def update_project(
        self,
        project_id: UUID,
        data: ProjectUpdate,
        current_user: User,
    ) -> Project:
        """Update a project.

        Args:
            project_id: Project UUID
            data: Update data
            current_user: User making the update

        Returns:
            Updated project

        Raises:
            NotFoundError: If project not found
            AuthorizationError: If user cannot update this project
            DuplicateError: If new name already exists
        """
        project = await self.get_project(project_id)

        # Check authorization
        self._check_modify_permission(project, current_user)

        # Check for duplicate name if changing
        if data.name and data.name != project.name:
            if await self.project_repo.name_exists(data.name, exclude_id=project_id):
                raise DuplicateError("project name", data.name)

        # Filter out None values
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if update_data:
            project = await self.project_repo.update(project, update_data)

        return project

    async def archive_project(
        self,
        project_id: UUID,
        current_user: User,
    ) -> Project:
        """Archive a project (soft delete).

        Args:
            project_id: Project UUID
            current_user: User archiving the project

        Returns:
            Archived project

        Raises:
            NotFoundError: If project not found
            AuthorizationError: If user cannot archive this project
        """
        project = await self.get_project(project_id)

        # Check authorization
        self._check_modify_permission(project, current_user)

        return await self.project_repo.archive(project)

    async def unarchive_project(
        self,
        project_id: UUID,
        current_user: User,
    ) -> Project:
        """Unarchive a project.

        Args:
            project_id: Project UUID
            current_user: User unarchiving the project

        Returns:
            Unarchived project

        Raises:
            NotFoundError: If project not found
            AuthorizationError: If user cannot unarchive this project
        """
        project = await self.get_project(project_id)

        # Check authorization
        self._check_modify_permission(project, current_user)

        return await self.project_repo.unarchive(project)

    def _check_modify_permission(
        self,
        project: Project,
        user: User,
    ) -> None:
        """Check if user can modify a project.

        Args:
            project: Project instance
            user: User to check

        Raises:
            AuthorizationError: If user cannot modify the project
        """
        # Admins can modify any project
        if user.role == UserRole.ADMIN:
            return

        # Project creator can modify their project
        if project.created_by_id == user.id:
            return

        # Managers can modify projects they created
        if user.role == UserRole.MANAGER and project.created_by_id == user.id:
            return

        raise AuthorizationError(
            "Only the project owner or admin can modify this project"
        )
