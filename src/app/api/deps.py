"""API dependencies for dependency injection."""

from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.exceptions import (
    AuthenticationError,
    TokenBlacklistedError,
    TokenExpiredError,
    TokenInvalidError,
)
from app.core.security import rate_limiter
from app.models.user import User
from app.models.enums import UserRole
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Type alias for database session
DBSession = Annotated[AsyncSession, Depends(get_db)]


def get_client_ip(request: Request) -> str:
    """Extract client IP from request.

    Handles X-Forwarded-For header for reverse proxy setups.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def get_current_user(
    request: Request,
    db: DBSession,
    authorization: str = Header(..., description="Bearer token"),
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        request: FastAPI request
        db: Database session
        authorization: Authorization header

    Returns:
        Authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    # Extract token from header
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]

    try:
        # Verify token
        auth_service = AuthService(db)
        payload = await auth_service.verify_token(token)

        # Get user from database
        user_repo = UserRepository(db)
        user = await user_repo.get(UUID(payload.sub))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenBlacklistedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (TokenInvalidError, AuthenticationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# Type alias for current user
CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_optional_user(
    request: Request,
    db: DBSession,
    authorization: str = Header(None, description="Bearer token"),
) -> User | None:
    """Get current user if authenticated, None otherwise."""
    if not authorization:
        return None
    try:
        return await get_current_user(request, db, authorization)
    except HTTPException:
        return None


# Type alias for optional user
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def require_roles(*roles: UserRole):
    """Dependency factory for role-based access control.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: CurrentUser = Depends(require_roles(UserRole.ADMIN))):
            ...
    """
    async def role_checker(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {[r.value for r in roles]}",
            )
        return current_user
    return role_checker


# Pre-defined role dependencies
RequireAdmin = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
RequireManager = Annotated[User, Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN))]
RequireDeveloper = Annotated[
    User,
    Depends(require_roles(UserRole.DEVELOPER, UserRole.MANAGER, UserRole.ADMIN))
]


async def rate_limit_check(request: Request) -> None:
    """Check global rate limit.

    Raises:
        HTTPException: If rate limit exceeded
    """
    client_ip = get_client_ip(request)
    allowed, remaining, retry_after = await rate_limiter.check_global_limit(client_ip)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


async def login_rate_limit_check(request: Request) -> None:
    """Check login-specific rate limit.

    Raises:
        HTTPException: If rate limit exceeded
    """
    client_ip = get_client_ip(request)
    allowed, remaining, retry_after = await rate_limiter.check_login_limit(client_ip)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts",
            headers={"Retry-After": str(retry_after)},
        )


# Rate limit dependencies
RateLimitDep = Depends(rate_limit_check)
LoginRateLimitDep = Depends(login_rate_limit_check)
