"""User repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address.

        Args:
            email: Email address

        Returns:
            User instance or None
        """
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User instance or None
        """
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if email is already in use.

        Args:
            email: Email address to check
            exclude_id: Optional user ID to exclude from check

        Returns:
            True if email exists, False otherwise
        """
        query = select(User).where(User.email == email)
        if exclude_id:
            query = query.where(User.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def username_exists(
        self,
        username: str,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """Check if username is already in use.

        Args:
            username: Username to check
            exclude_id: Optional user ID to exclude from check

        Returns:
            True if username exists, False otherwise
        """
        query = select(User).where(User.username == username)
        if exclude_id:
            query = query.where(User.id != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Get all active users.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active users
        """
        result = await self.session.execute(
            select(User)
            .where(User.is_active == True)  # noqa: E712
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_last_login(self, user: User) -> User:
        """Update user's last login timestamp.

        Args:
            user: User instance

        Returns:
            Updated user instance
        """
        from datetime import datetime, timezone

        user.last_login = datetime.now(timezone.utc)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
