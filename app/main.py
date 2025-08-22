import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.auth import router as auth_router
from app.api.v1.items import router as items_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.core.logging import LoggingMiddleware, get_logger, setup_logging
from app.services.firebase import get_firebase_health, initialize_firebase

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(
        "Starting FastAPI application",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
    )

    try:
        # Initialize Firebase
        initialize_firebase()
        logger.info("Firebase initialized successfully")

        # Add any other startup tasks here

        yield

    except Exception as e:
        logger.error("Startup failed", error=str(e), exc_info=e)
        raise
    finally:
        # Shutdown
        logger.info("Shutting down FastAPI application")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready FastAPI boilerplate for Google Cloud Run with Firebase",
    openapi_url="/api/openapi.json" if not settings.is_production else None,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# Add CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

# Add trusted host middleware for production
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.googleusercontent.com", "*.run.app"]
        + settings.BACKEND_CORS_ORIGINS,
    )

# Add logging middleware
logging_middleware = LoggingMiddleware()
app.middleware("http")(logging_middleware)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add process time header to responses."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    return response


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    """Add request ID header to responses."""
    from uuid import uuid4

    request_id = str(uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Basic rate limiting middleware."""
    # In production, you would implement proper rate limiting
    # using Redis or another storage backend

    # For now, just log the request
    client_ip = request.client.host if request.client else "unknown"
    logger.debug("Request from client", client_ip=client_ip, path=request.url.path)

    response = await call_next(request)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=exc,
    )

    if settings.DEBUG:
        # In debug mode, return detailed error information
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "type": type(exc).__name__,
            },
        )
    else:
        # In production, return generic error message
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred",
            },
        )


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint with Firebase health check."""
    firebase_health = get_firebase_health()

    is_ready = firebase_health["status"] == "healthy"

    response_data = {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": time.time(),
        "checks": {
            "firebase": firebase_health,
        },
    }

    status_code = 200 if is_ready else 503
    return JSONResponse(content=response_data, status_code=status_code)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs" if not settings.is_production else None,
        "health_check": "/health",
        "readiness_check": "/ready",
    }


# API routes
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])

app.include_router(items_router, prefix="/api/v1/items", tags=["Items"])


# Additional utility endpoints for development
if not settings.is_production:

    @app.get("/debug/config")
    async def debug_config():
        """Debug endpoint to show current configuration (development only)."""
        config_data = settings.model_dump()

        # Remove sensitive data
        sensitive_keys = [
            "SECRET_KEY",
            "FIREBASE_CREDENTIALS_PATH",
            "GOOGLE_APPLICATION_CREDENTIALS",
        ]
        for key in sensitive_keys:
            if key in config_data:
                config_data[key] = "***HIDDEN***"

        return {
            "config": config_data,
            "firebase_emulator_config": settings.firebase_emulator_config,
            "should_use_emulator": settings.should_use_emulator,
        }

    @app.get("/debug/firebase")
    async def debug_firebase():
        """Debug endpoint to show Firebase status (development only)."""
        return get_firebase_health()


# Error handling for specific HTTP exceptions
from fastapi import HTTPException


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(
        "HTTP exception",
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
        detail=exc.detail,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


# Validation error handler
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(
        "Validation error",
        path=request.url.path,
        method=request.method,
        errors=exc.errors(),
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD and settings.is_development,
        log_config=None,  # We handle logging ourselves
        access_log=False,  # We handle access logging in middleware
    )
