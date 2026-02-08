"""Custom exception classes."""

from typing import Any, Dict, List, Optional


class TaskTrackerException(Exception):
    """Base exception for Task Tracker application."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(self.message)


class AuthenticationError(TaskTrackerException):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class InvalidCredentialsError(AuthenticationError):
    """Invalid credentials provided."""

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message=message)
        self.code = "INVALID_CREDENTIALS"


class TokenExpiredError(AuthenticationError):
    """Token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message=message)
        self.code = "TOKEN_EXPIRED"


class TokenInvalidError(AuthenticationError):
    """Token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message=message)
        self.code = "TOKEN_INVALID"


class TokenBlacklistedError(AuthenticationError):
    """Token has been blacklisted."""

    def __init__(self, message: str = "Token has been revoked"):
        super().__init__(message=message)
        self.code = "TOKEN_BLACKLISTED"


class AuthorizationError(TaskTrackerException):
    """Authorization failed - insufficient permissions."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
        )


class NotFoundError(TaskTrackerException):
    """Resource not found."""

    def __init__(self, resource: str, identifier: Any = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
        )


class ValidationError(TaskTrackerException):
    """Validation error."""

    def __init__(
        self,
        message: str = "Validation error",
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            errors=errors,
        )


class ConflictError(TaskTrackerException):
    """Resource conflict (e.g., duplicate)."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
        )


class DuplicateError(ConflictError):
    """Duplicate resource error."""

    def __init__(self, field: str, value: Any):
        super().__init__(message=f"{field} '{value}' already exists")
        self.code = "DUPLICATE"


class RateLimitError(TaskTrackerException):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )
        self.retry_after = retry_after


class BusinessRuleError(TaskTrackerException):
    """Business rule violation."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            status_code=400,
        )


class InvalidStateTransitionError(BusinessRuleError):
    """Invalid state transition."""

    def __init__(self, current_state: str, target_state: str):
        super().__init__(
            message=f"Cannot transition from '{current_state}' to '{target_state}'"
        )
        self.code = "INVALID_STATE_TRANSITION"


class AccountLockedError(AuthenticationError):
    """Account is locked due to too many failed attempts."""

    def __init__(self, message: str = "Account temporarily locked"):
        super().__init__(message=message)
        self.code = "ACCOUNT_LOCKED"
        self.status_code = 423
