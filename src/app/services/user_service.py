"""User service."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateError, NotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate


class UserService:
    """User service for user management operations."""

    def __init__(self, session: AsyncSession):
        """Initialize user service with database session.

        Args:
            session: Async database session
        """
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_user(self, user_id: UUID) -> User:
        """Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User instance

        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User instance or None
        """
        return await self.user_repo.get_by_email(email)

    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
    ) -> List[User]:
        """Get list of users.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            active_only: Only return active users

        Returns:
            List of users
        """
        if active_only:
            return await self.user_repo.get_active_users(skip, limit)
        return await self.user_repo.get_all(skip, limit)

    async def update_user(
        self,
        user_id: UUID,
        data: UserUpdate,
        current_user: User,
    ) -> User:
        """Update user profile.

        Args:
            user_id: User UUID to update
            data: Update data
            current_user: User making the request

        Returns:
            Updated user

        Raises:
            NotFoundError: If user not found
            DuplicateError: If email/username already exists
        """
        user = await self.get_user(user_id)

        # Check for duplicate email
        if data.email and data.email != user.email:
            if await self.user_repo.email_exists(data.email, exclude_id=user_id):
                raise DuplicateError("email", data.email)

        # Check for duplicate username
        if data.username and data.username != user.username:
            if await self.user_repo.username_exists(data.username, exclude_id=user_id):
                raise DuplicateError("username", data.username)

        # Filter out None values
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if update_data:
            user = await self.user_repo.update(user, update_data)

        return user

    async def deactivate_user(self, user_id: UUID) -> User:
        """Deactivate a user account.

        Args:
            user_id: User UUID

        Returns:
            Updated user

        Raises:
            NotFoundError: If user not found
        """
        user = await self.get_user(user_id)
        return await self.user_repo.update(user, {"is_active": False})

    async def activate_user(self, user_id: UUID) -> User:
        """Activate a user account.

        Args:
            user_id: User UUID

        Returns:
            Updated user

        Raises:
            NotFoundError: If user not found
        """
        user = await self.get_user(user_id)
        return await self.user_repo.update(user, {"is_active": True})
