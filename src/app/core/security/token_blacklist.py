"""Token blacklist service using Redis."""

from datetime import datetime, timezone
from typing import Optional

from app.core.redis import redis_client
from app.config.settings import settings


class TokenBlacklist:
    """Token blacklist service for invalidating JWT tokens.

    Uses Redis to store blacklisted token IDs (JTI).
    Tokens are automatically removed when they expire.
    """

    # Redis key prefix for blacklisted tokens
    KEY_PREFIX = "token:blacklist:"

    # Redis key prefix for user sessions
    USER_SESSIONS_PREFIX = "user:sessions:"

    async def blacklist_token(
        self,
        jti: str,
        exp: int,
        user_id: Optional[str] = None,
    ) -> None:
        """Add a token to the blacklist.

        Args:
            jti: Token's unique ID
            exp: Token's expiry timestamp
            user_id: Optional user ID for session tracking
        """
        # Calculate TTL (time until token expires)
        now = int(datetime.now(timezone.utc).timestamp())
        ttl = max(exp - now, 0)

        if ttl > 0:
            # Store token ID with TTL
            key = f"{self.KEY_PREFIX}{jti}"
            await redis_client.set(key, "1", ex=ttl)

            # Remove from user's active sessions
            if user_id:
                sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
                await redis_client.client.srem(sessions_key, jti)

    async def is_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted.

        Args:
            jti: Token's unique ID

        Returns:
            True if blacklisted, False otherwise
        """
        key = f"{self.KEY_PREFIX}{jti}"
        return await redis_client.exists(key)

    async def add_user_session(
        self,
        user_id: str,
        jti: str,
        ttl: int,
    ) -> None:
        """Track a user's active session.

        Args:
            user_id: User's UUID as string
            jti: Token's unique ID
            ttl: Session TTL in seconds
        """
        key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
        await redis_client.sadd(key, jti)
        await redis_client.expire(key, ttl)

    async def get_user_sessions(self, user_id: str) -> set[str]:
        """Get all active session IDs for a user.

        Args:
            user_id: User's UUID as string

        Returns:
            Set of active token IDs
        """
        key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
        result = await redis_client.client.smembers(key)
        return set(result) if result else set()

    async def invalidate_all_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for a user (logout all devices).

        Args:
            user_id: User's UUID as string

        Returns:
            Number of sessions invalidated
        """
        sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
        sessions = await redis_client.client.smembers(sessions_key)

        if not sessions:
            return 0

        count = 0
        # Blacklist all tokens
        for jti in sessions:
            # Set a default TTL for blacklist entry
            ttl = settings.refresh_token_expire_days * 24 * 60 * 60
            key = f"{self.KEY_PREFIX}{jti}"
            await redis_client.set(key, "1", ex=ttl)
            count += 1

        # Clear user's sessions set
        await redis_client.delete(sessions_key)

        return count


# Global token blacklist instance
token_blacklist = TokenBlacklist()
