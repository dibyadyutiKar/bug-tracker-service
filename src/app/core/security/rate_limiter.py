"""Rate limiting using Redis sliding window algorithm."""

import time
from typing import Optional, Tuple

from app.core.redis import redis_client
from app.config.settings import settings


class RateLimiter:
    """Rate limiter using Redis sliding window algorithm.

    Implements sliding window rate limiting to protect against
    brute force attacks and API abuse.
    """

    # Redis key prefixes
    GLOBAL_PREFIX = "ratelimit:global:"
    LOGIN_PREFIX = "ratelimit:login:"
    ACCOUNT_LOCK_PREFIX = "account:locked:"

    # Account lockout settings
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutes

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        prefix: str = GLOBAL_PREFIX,
    ) -> Tuple[bool, int, int]:
        """Check if request is within rate limit.

        Uses sliding window algorithm:
        1. Get current window count
        2. If under limit, increment and allow
        3. If over limit, deny with retry-after

        Args:
            key: Unique identifier (e.g., IP address, user ID)
            limit: Maximum requests allowed
            window: Time window in seconds
            prefix: Redis key prefix

        Returns:
            Tuple of (allowed, remaining, retry_after)
            - allowed: True if request is allowed
            - remaining: Number of requests remaining
            - retry_after: Seconds until rate limit resets (if denied)
        """
        redis_key = f"{prefix}{key}"
        current_time = int(time.time())

        # Use pipeline for atomic operations
        pipe = redis_client.client.pipeline()

        # Remove old entries outside the window
        window_start = current_time - window
        pipe.zremrangebyscore(redis_key, 0, window_start)

        # Count requests in current window
        pipe.zcard(redis_key)

        # Add current request
        pipe.zadd(redis_key, {str(current_time): current_time})

        # Set expiry on the key
        pipe.expire(redis_key, window)

        results = await pipe.execute()
        request_count = results[1]

        if request_count >= limit:
            # Calculate retry-after
            oldest_request = await redis_client.client.zrange(
                redis_key, 0, 0, withscores=True
            )
            if oldest_request:
                oldest_time = int(oldest_request[0][1])
                retry_after = oldest_time + window - current_time
            else:
                retry_after = window

            return False, 0, max(retry_after, 1)

        remaining = limit - request_count - 1
        return True, remaining, 0

    async def check_global_limit(
        self,
        identifier: str,
    ) -> Tuple[bool, int, int]:
        """Check global API rate limit.

        Args:
            identifier: Client identifier (e.g., IP address)

        Returns:
            Tuple of (allowed, remaining, retry_after)
        """
        return await self.check_rate_limit(
            key=identifier,
            limit=settings.rate_limit_requests,
            window=settings.rate_limit_window,
            prefix=self.GLOBAL_PREFIX,
        )

    async def check_login_limit(
        self,
        identifier: str,
    ) -> Tuple[bool, int, int]:
        """Check login-specific rate limit.

        Args:
            identifier: Client identifier (e.g., IP address or email)

        Returns:
            Tuple of (allowed, remaining, retry_after)
        """
        return await self.check_rate_limit(
            key=identifier,
            limit=settings.login_rate_limit_requests,
            window=settings.login_rate_limit_window,
            prefix=self.LOGIN_PREFIX,
        )

    async def record_failed_login(self, identifier: str) -> Tuple[bool, int]:
        """Record a failed login attempt.

        Args:
            identifier: Account identifier (e.g., email)

        Returns:
            Tuple of (account_locked, attempts_remaining)
        """
        key = f"{self.LOGIN_PREFIX}failed:{identifier}"
        current_time = int(time.time())
        window = settings.login_rate_limit_window

        pipe = redis_client.client.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(key, 0, current_time - window)

        # Add failed attempt
        pipe.zadd(key, {str(current_time): current_time})

        # Count failures
        pipe.zcard(key)

        # Set expiry
        pipe.expire(key, window)

        results = await pipe.execute()
        failure_count = results[2]

        if failure_count >= self.MAX_FAILED_ATTEMPTS:
            # Lock the account
            await self.lock_account(identifier)
            return True, 0

        return False, self.MAX_FAILED_ATTEMPTS - failure_count

    async def clear_failed_logins(self, identifier: str) -> None:
        """Clear failed login attempts after successful login.

        Args:
            identifier: Account identifier (e.g., email)
        """
        key = f"{self.LOGIN_PREFIX}failed:{identifier}"
        await redis_client.delete(key)

    async def lock_account(self, identifier: str) -> None:
        """Lock an account temporarily.

        Args:
            identifier: Account identifier (e.g., email)
        """
        key = f"{self.ACCOUNT_LOCK_PREFIX}{identifier}"
        await redis_client.set(key, "1", ex=self.LOCKOUT_DURATION)

    async def is_account_locked(self, identifier: str) -> Tuple[bool, Optional[int]]:
        """Check if an account is locked.

        Args:
            identifier: Account identifier (e.g., email)

        Returns:
            Tuple of (is_locked, seconds_remaining)
        """
        key = f"{self.ACCOUNT_LOCK_PREFIX}{identifier}"
        exists = await redis_client.exists(key)

        if not exists:
            return False, None

        ttl = await redis_client.ttl(key)
        return True, max(ttl, 0)

    async def unlock_account(self, identifier: str) -> None:
        """Manually unlock an account.

        Args:
            identifier: Account identifier (e.g., email)
        """
        key = f"{self.ACCOUNT_LOCK_PREFIX}{identifier}"
        await redis_client.delete(key)

        # Also clear failed attempts
        await self.clear_failed_logins(identifier)


# Global rate limiter instance
rate_limiter = RateLimiter()
