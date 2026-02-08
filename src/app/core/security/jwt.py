"""JWT token service using RS256 algorithm."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt

from app.config.settings import settings
from app.core.exceptions import TokenExpiredError, TokenInvalidError
from app.schemas.auth import TokenPayload


class JWTService:
    """JWT token service for authentication.

    Uses RS256 (RSA with SHA-256) for asymmetric signing.
    - Private key: Used for signing tokens
    - Public key: Used for verifying tokens
    """

    def __init__(self):
        """Initialize JWT service."""
        self._private_key: Optional[str] = None
        self._public_key: Optional[str] = None
        self._algorithm = settings.jwt_algorithm

    @property
    def private_key(self) -> str:
        """Lazily load private key."""
        if self._private_key is None:
            self._private_key = settings.get_jwt_private_key()
        return self._private_key

    @property
    def public_key(self) -> str:
        """Lazily load public key."""
        if self._public_key is None:
            self._public_key = settings.get_jwt_public_key()
        return self._public_key

    def create_access_token(
        self,
        user_id: str,
        email: str,
        role: str,
        expires_delta: Optional[timedelta] = None,
    ) -> tuple[str, str]:
        """Create an access token.

        Args:
            user_id: User's UUID as string
            email: User's email
            role: User's role
            expires_delta: Optional custom expiry time

        Returns:
            Tuple of (token string, token ID)
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

        return self._create_token(
            user_id=user_id,
            email=email,
            role=role,
            token_type="access",
            expires_delta=expires_delta,
        )

    def create_refresh_token(
        self,
        user_id: str,
        email: str,
        role: str,
        expires_delta: Optional[timedelta] = None,
    ) -> tuple[str, str]:
        """Create a refresh token.

        Args:
            user_id: User's UUID as string
            email: User's email
            role: User's role
            expires_delta: Optional custom expiry time

        Returns:
            Tuple of (token string, token ID)
        """
        if expires_delta is None:
            expires_delta = timedelta(days=settings.refresh_token_expire_days)

        return self._create_token(
            user_id=user_id,
            email=email,
            role=role,
            token_type="refresh",
            expires_delta=expires_delta,
        )

    def _create_token(
        self,
        user_id: str,
        email: str,
        role: str,
        token_type: str,
        expires_delta: timedelta,
    ) -> tuple[str, str]:
        """Create a JWT token.

        Args:
            user_id: User's UUID as string
            email: User's email
            role: User's role
            token_type: "access" or "refresh"
            expires_delta: Token expiry time

        Returns:
            Tuple of (token string, token ID)
        """
        now = datetime.now(timezone.utc)
        token_id = str(uuid.uuid4())

        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "type": token_type,
            "jti": token_id,
            "iat": int(now.timestamp()),
            "exp": int((now + expires_delta).timestamp()),
        }

        token = jwt.encode(payload, self.private_key, algorithm=self._algorithm)
        return token, token_id

    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode a JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenPayload with decoded claims

        Raises:
            TokenExpiredError: If token has expired
            TokenInvalidError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self._algorithm],
            )
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except JWTError as e:
            raise TokenInvalidError(f"Invalid token: {str(e)}")

    def decode_token_unsafe(self, token: str) -> dict[str, Any]:
        """Decode token without verification (for debugging only).

        Args:
            token: JWT token string

        Returns:
            Decoded payload dictionary
        """
        return jwt.decode(
            token,
            self.public_key,
            algorithms=[self._algorithm],
            options={"verify_signature": False},
        )

    def get_token_expiry(self, token: str) -> datetime:
        """Get token expiry time.

        Args:
            token: JWT token string

        Returns:
            Expiry datetime
        """
        payload = self.decode_token_unsafe(token)
        return datetime.fromtimestamp(payload["exp"], tz=timezone.utc)


# Global JWT service instance
jwt_service = JWTService()
