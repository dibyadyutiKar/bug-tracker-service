"""Authentication service."""

from datetime import datetime, timezone
from typing import Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.core.exceptions import (
    AccountLockedError,
    AuthenticationError,
    DuplicateError,
    InvalidCredentialsError,
    TokenBlacklistedError,
    TokenExpiredError,
    TokenInvalidError,
)
from app.core.security import (
    jwt_service,
    password_hasher,
    rate_limiter,
    token_blacklist,
)
from app.models.user import User
from app.models.enums import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenPayload,
    TokenResponse,
)


class AuthService:
    """Authentication service handling user registration, login, and token management."""

    def __init__(self, session: AsyncSession):
        """Initialize auth service with database session.

        Args:
            session: Async database session
        """
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user.

        Args:
            data: Registration request data

        Returns:
            Created user instance

        Raises:
            DuplicateError: If email or username already exists
        """
        # Check for duplicate email
        if await self.user_repo.email_exists(data.email):
            raise DuplicateError("email", data.email)

        # Check for duplicate username
        if await self.user_repo.username_exists(data.username):
            raise DuplicateError("username", data.username)

        # Hash password
        password_hash = password_hasher.hash(data.password)

        # Create user
        user = await self.user_repo.create({
            "username": data.username,
            "email": data.email,
            "password_hash": password_hash,
            "role": UserRole.DEVELOPER,
            "is_active": True,
        })

        return user

    async def login(
        self,
        data: LoginRequest,
        client_ip: str,
    ) -> Tuple[User, TokenResponse]:
        """Authenticate user and generate tokens.

        Args:
            data: Login request data
            client_ip: Client IP address for rate limiting

        Returns:
            Tuple of (user, token response)

        Raises:
            AccountLockedError: If account is locked
            InvalidCredentialsError: If credentials are invalid
        """
        # Check if account is locked
        is_locked, remaining = await rate_limiter.is_account_locked(data.email)
        if is_locked:
            raise AccountLockedError(
                f"Account temporarily locked. Try again in {remaining} seconds."
            )

        # Get user by email
        user = await self.user_repo.get_by_email(data.email)
        if not user:
            # Record failed attempt even if user doesn't exist (timing attack prevention)
            await rate_limiter.record_failed_login(data.email)
            raise InvalidCredentialsError()

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        # Verify password
        if not password_hasher.verify(data.password, user.password_hash):
            locked, attempts_remaining = await rate_limiter.record_failed_login(data.email)
            if locked:
                raise AccountLockedError(
                    "Too many failed attempts. Account temporarily locked."
                )
            raise InvalidCredentialsError()

        # Clear failed login attempts
        await rate_limiter.clear_failed_logins(data.email)

        # Update last login
        await self.user_repo.update_last_login(user)

        # Generate tokens
        tokens = await self._create_tokens(user)

        return user, tokens

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token string

        Returns:
            New token response

        Raises:
            TokenExpiredError: If refresh token has expired
            TokenInvalidError: If refresh token is invalid
            TokenBlacklistedError: If refresh token is blacklisted
        """
        # Verify refresh token
        payload = jwt_service.verify_token(refresh_token)

        # Check token type
        if payload.type != "refresh":
            raise TokenInvalidError("Invalid token type")

        # Check if token is blacklisted
        if await token_blacklist.is_blacklisted(payload.jti):
            raise TokenBlacklistedError()

        # Get user
        user = await self.user_repo.get(UUID(payload.sub))
        if not user or not user.is_active:
            raise TokenInvalidError("User not found or inactive")

        # Blacklist old refresh token
        await token_blacklist.blacklist_token(
            jti=payload.jti,
            exp=payload.exp,
            user_id=payload.sub,
        )

        # Generate new tokens
        return await self._create_tokens(user)

    async def logout(self, access_token: str, refresh_token: str) -> None:
        """Logout user by blacklisting tokens.

        Args:
            access_token: Access token to invalidate
            refresh_token: Refresh token to invalidate
        """
        try:
            # Blacklist access token
            access_payload = jwt_service.verify_token(access_token)
            await token_blacklist.blacklist_token(
                jti=access_payload.jti,
                exp=access_payload.exp,
                user_id=access_payload.sub,
            )
        except (TokenExpiredError, TokenInvalidError):
            pass  # Token already expired or invalid, no need to blacklist

        try:
            # Blacklist refresh token
            refresh_payload = jwt_service.verify_token(refresh_token)
            await token_blacklist.blacklist_token(
                jti=refresh_payload.jti,
                exp=refresh_payload.exp,
                user_id=refresh_payload.sub,
            )
        except (TokenExpiredError, TokenInvalidError):
            pass

    async def logout_all_devices(self, user_id: UUID) -> int:
        """Logout user from all devices.

        Args:
            user_id: User's UUID

        Returns:
            Number of sessions invalidated
        """
        return await token_blacklist.invalidate_all_user_sessions(str(user_id))

    async def verify_token(self, token: str) -> TokenPayload:
        """Verify an access token.

        Args:
            token: Access token string

        Returns:
            Token payload

        Raises:
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid
            TokenBlacklistedError: If token is blacklisted
        """
        payload = jwt_service.verify_token(token)

        if payload.type != "access":
            raise TokenInvalidError("Invalid token type")

        if await token_blacklist.is_blacklisted(payload.jti):
            raise TokenBlacklistedError()

        return payload

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change user's password.

        Args:
            user: User instance
            current_password: Current password for verification
            new_password: New password

        Raises:
            InvalidCredentialsError: If current password is wrong
        """
        # Verify current password
        if not password_hasher.verify(current_password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect")

        # Hash and update new password
        new_hash = password_hasher.hash(new_password)
        await self.user_repo.update(user, {"password_hash": new_hash})

        # Invalidate all sessions (force re-login)
        await token_blacklist.invalidate_all_user_sessions(str(user.id))

    async def _create_tokens(self, user: User) -> TokenResponse:
        """Create access and refresh tokens for user.

        Args:
            user: User instance

        Returns:
            Token response
        """
        user_id = str(user.id)

        # Create access token
        access_token, access_jti = jwt_service.create_access_token(
            user_id=user_id,
            email=user.email,
            role=user.role.value,
        )

        # Create refresh token
        refresh_token, refresh_jti = jwt_service.create_refresh_token(
            user_id=user_id,
            email=user.email,
            role=user.role.value,
        )

        # Track sessions
        refresh_ttl = settings.refresh_token_expire_days * 24 * 60 * 60
        await token_blacklist.add_user_session(user_id, refresh_jti, refresh_ttl)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )
