"""Audit logging middleware."""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import settings


# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_id_from_request(request: Request) -> Optional[str]:
    """Extract user ID from request state if available."""
    return getattr(request.state, "user_id", None)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware for audit logging.

    Logs:
    - Request details (method, path, IP, user)
    - Response status and timing
    - Authentication events
    - Permission-sensitive operations
    """

    # Paths that should be logged for security
    SENSITIVE_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/logout",
        "/api/v1/auth/register",
        "/api/v1/auth/change-password",
    }

    # Methods that modify data
    MODIFYING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Log request and response details."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Capture request details
        start_time = time.time()
        client_ip = get_client_ip(request)
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else None

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Get user ID if set during request processing
        user_id = get_user_id_from_request(request)

        # Build log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "client_ip": client_ip,
            "method": method,
            "path": path,
            "query": query,
            "user_id": user_id,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Determine if this should be logged
        should_log = self._should_log(method, path, response.status_code)

        if should_log:
            self._log_entry(log_entry)

        return response

    def _should_log(self, method: str, path: str, status_code: int) -> bool:
        """Determine if request should be logged."""
        # Always log authentication events
        if path in self.SENSITIVE_PATHS:
            return True

        # Always log errors
        if status_code >= 400:
            return True

        # Log modifying requests
        if method in self.MODIFYING_METHODS:
            return True

        # In development, log everything
        if settings.is_development:
            return True

        return False

    def _log_entry(self, entry: dict) -> None:
        """Write log entry."""
        if settings.log_format == "json":
            audit_logger.info(json.dumps(entry))
        else:
            audit_logger.info(
                f"[{entry['request_id']}] {entry['method']} {entry['path']} "
                f"- {entry['status_code']} ({entry['duration_ms']}ms) "
                f"- IP: {entry['client_ip']} User: {entry['user_id']}"
            )


def add_audit_log_middleware(app):
    """Add audit log middleware to app."""
    app.add_middleware(AuditLogMiddleware)
