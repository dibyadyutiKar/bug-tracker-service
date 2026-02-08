"""Project repository."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.repositories.base import BaseRepository
from app.schemas.project import ProjectListParams


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Project, session)

    async def get_with_creator(self, id: UUID) -> Optional[Project]:
        """Get project with creator relationship loaded.

        Args:
            id: Project UUID

        Returns:
            Project instance with creator loaded or None
        """
        result = await self.session.execute(
            select(Project)
            .options(selectinload(Project.creator))
            .where(Project.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Project]:
        """Get project by name.

        Args:
            name: Project name

        Returns:
            Project instance or None
        """
        result = await self.session.execute(
            select(Project).where(Project.name == name)
        )
        return result.scalar_one_or_none()

    async def name_exists(
        self,
        name: str,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if project name is already in use.

        Args:
            name: Project name to check
            exclude_id: Optional project ID to exclude from check

        Returns:
            True if name exists, False otherwise
        """
        query = select(Project).where(Project.name == name)
        if exclude_id:
            query = query.where(Project.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def list_projects(
        self,
        params: ProjectListParams,
    ) -> Tuple[List[Project], int]:
        """List projects with filtering, sorting, and pagination.

        Args:
            params: Query parameters

        Returns:
            Tuple of (list of projects, total count)
        """
        # Base query
        query = select(Project).options(selectinload(Project.creator))

        # Apply filters
        if params.is_archived is not None:
            query = query.where(Project.is_archived == params.is_archived)

        if params.search:
            search_term = f"%{params.search}%"
            query = query.where(
                or_(
                    Project.name.ilike(search_term),
                    Project.description.ilike(search_term),
                )
            )

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply sorting
        query = self._apply_sorting(query, params.sort_field, params.sort_desc)

        # Apply pagination
        query = self._apply_pagination(query, params.page, params.limit)

        # Execute query
        result = await self.session.execute(query)
        projects = list(result.scalars().all())

        return projects, total

    async def get_user_projects(
        self,
        user_id: UUID,
        include_archived: bool = False,
    ) -> List[Project]:
        """Get projects created by a specific user.

        Args:
            user_id: Creator user ID
            include_archived: Include archived projects

        Returns:
            List of projects
        """
        query = select(Project).where(Project.created_by_id == user_id)
        if not include_archived:
            query = query.where(Project.is_archived == False)  # noqa: E712
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def archive(self, project: Project) -> Project:
        """Archive a project (soft delete).

        Args:
            project: Project to archive

        Returns:
            Archived project
        """
        project.is_archived = True
        self.session.add(project)
        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def unarchive(self, project: Project) -> Project:
        """Unarchive a project.

        Args:
            project: Project to unarchive

        Returns:
            Unarchived project
        """
        project.is_archived = False
        self.session.add(project)
        await self.session.flush()
        await self.session.refresh(project)
        return project
