"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import (
    CurrentUser,
    DBSession,
    get_client_ip,
    login_rate_limit_check,
)
from app.core.exceptions import (
    AccountLockedError,
    AuthenticationError,
    DuplicateError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    TokenBlacklistedError,
)
from app.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user account with username, email, and password.",
)
async def register(
    data: RegisterRequest,
    db: DBSession,
):
    """Register a new user."""
    try:
        auth_service = AuthService(db)
        user = await auth_service.register(data)
        return user
    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate user and obtain access and refresh tokens.",
    dependencies=[Depends(login_rate_limit_check)],
)
async def login(
    request: Request,
    data: LoginRequest,
    db: DBSession,
):
    """Login and get access tokens."""
    try:
        client_ip = get_client_ip(request)
        auth_service = AuthService(db)
        user, tokens = await auth_service.login(data, client_ip)
        return tokens
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=e.message,
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get new access token using refresh token.",
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: DBSession,
):
    """Refresh access token."""
    try:
        auth_service = AuthService(db)
        tokens = await auth_service.refresh_tokens(data.refresh_token)
        return tokens
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    except (TokenInvalidError, TokenBlacklistedError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="User logout",
    description="Invalidate access and refresh tokens.",
)
async def logout(
    request: Request,
    data: RefreshTokenRequest,
    db: DBSession,
    current_user: CurrentUser,
):
    """Logout and invalidate tokens."""
    # Get access token from header
    auth_header = request.headers.get("Authorization", "")
    access_token = auth_header.replace("Bearer ", "")

    auth_service = AuthService(db)
    await auth_service.logout(access_token, data.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get the authenticated user's profile information.",
)
async def get_me(current_user: CurrentUser):
    """Get current user profile."""
    return current_user


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
    description="Change the current user's password. All sessions will be invalidated.",
)
async def change_password(
    data: PasswordChangeRequest,
    db: DBSession,
    current_user: CurrentUser,
):
    """Change user password."""
    try:
        auth_service = AuthService(db)
        await auth_service.change_password(
            user=current_user,
            current_password=data.current_password,
            new_password=data.new_password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout from all devices",
    description="Invalidate all sessions for the current user.",
)
async def logout_all_devices(
    db: DBSession,
    current_user: CurrentUser,
):
    """Logout from all devices."""
    auth_service = AuthService(db)
    await auth_service.logout_all_devices(current_user.id)
