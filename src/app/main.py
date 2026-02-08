"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config.settings import settings
from app.core.database import close_db
from app.core.redis import redis_client
from app.middleware import (
    add_security_headers_middleware,
    add_rate_limit_middleware,
    add_audit_log_middleware,
)
from app.schemas.base import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown."""
    # Startup
    await redis_client.connect()
    yield
    # Shutdown
    await redis_client.disconnect()
    await close_db()


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="Production-ready Bug Tracking API",
        version="1.0.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=600,  # 10 minutes preflight cache
    )

    # Add custom middleware (order matters - last added is first executed)
    add_audit_log_middleware(app)
    add_rate_limit_middleware(app)
    add_security_headers_middleware(app)

    # Include API router
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for load balancers and monitoring."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": "1.0.0",
        }

    # Readiness check endpoint
    @app.get("/ready", tags=["Health"])
    async def readiness_check():
        """Readiness check for Kubernetes."""
        # Check database connection
        try:
            from app.core.database import engine
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not ready", "reason": "database unavailable"},
            )

        # Check Redis connection
        try:
            await redis_client.client.ping()
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not ready", "reason": "redis unavailable"},
            )

        return {"status": "ready"}

    return app


# Create app instance
app = create_application()


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle validation errors with custom format."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body' prefix
        errors.append({
            "field": field,
            "message": error["msg"],
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            code="VALIDATION_ERROR",
            message="Invalid input data",
            errors=errors,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions."""
    # Log the exception in production
    if settings.is_production:
        # In production, return generic error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
            ).model_dump(),
        )
    else:
        # In development, return detailed error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                code="INTERNAL_ERROR",
                message=str(exc),
            ).model_dump(),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        workers=settings.workers if not settings.is_development else 1,
    )
