"""Rate limiting middleware."""

from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security.rate_limiter import rate_limiter


def get_client_ip(request: Request) -> str:
    """Extract client IP from request.

    Handles X-Forwarded-For header for reverse proxy setups.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for global rate limiting.

    Applies sliding window rate limiting to all requests.
    Returns 429 Too Many Requests when limit exceeded.
    """

    # Paths to exclude from rate limiting
    EXCLUDED_PATHS = {"/health", "/ready", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Check rate limit before processing request."""
        # Skip rate limiting for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Get client identifier
        client_ip = get_client_ip(request)

        # Check rate limit
        allowed, remaining, retry_after = await rate_limiter.check_global_limit(
            client_ip
        )

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                    }
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


def add_rate_limit_middleware(app):
    """Add rate limit middleware to app."""
    app.add_middleware(RateLimitMiddleware)
