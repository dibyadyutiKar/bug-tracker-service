"""Security headers middleware."""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security (HTTPS only)
    - Content-Security-Policy
    - Referrer-Policy
    - Permissions-Policy
    """

    # Security headers configuration
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    # Production-only headers
    PRODUCTION_HEADERS = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';",
    }

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Add base security headers
        for header, value in self.SECURITY_HEADERS.items():
            response.headers[header] = value

        # Add production-only headers in production mode
        if settings.is_production:
            for header, value in self.PRODUCTION_HEADERS.items():
                response.headers[header] = value

        return response


def add_security_headers_middleware(app):
    """Add security headers middleware to app."""
    app.add_middleware(SecurityHeadersMiddleware)
