import logging
import sys
from typing import Any, Dict

import structlog
from rich.console import Console
from rich.logging import RichHandler

from app.core.config import settings


def setup_logging() -> None:
    """Set up structured logging with different outputs for different environments."""

    # Configure structlog
    timestamper = structlog.processors.TimeStamper(fmt="ISO")

    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.LOG_FORMAT == "json" or settings.is_production:
        # JSON logging for production
        structlog.configure(
            processors=shared_processors
            + [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Configure standard library logging for JSON
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, settings.LOG_LEVEL.upper()),
        )
    else:
        # Rich/console logging for development
        console = Console(color_system="auto")

        structlog.configure(
            processors=shared_processors + [structlog.dev.ConsoleRenderer(colors=True)],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Configure standard library logging with Rich
        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL.upper()),
            format="%(message)s",
            datefmt="[%X]",
            handlers=[
                RichHandler(
                    console=console,
                    rich_tracebacks=True,
                    tracebacks_show_locals=settings.DEBUG,
                )
            ],
        )

    # Suppress noisy third-party logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class LoggingMiddleware:
    """Middleware for logging requests and responses."""

    def __init__(self, logger_name: str = "app.middleware.logging"):
        self.logger = get_logger(logger_name)

    async def __call__(self, request, call_next):
        """Log request and response details."""
        import time
        from uuid import uuid4

        # Generate request ID
        request_id = str(uuid4())

        # Log request
        start_time = time.perf_counter()

        self.logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            client_ip=request.client.host if request.client else None,
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.perf_counter() - start_time

            # Log response
            self.logger.info(
                "Request completed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )

            return response

        except Exception as exc:
            # Calculate duration for failed requests
            duration = time.perf_counter() - start_time

            # Log error
            self.logger.error(
                "Request failed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                duration_ms=round(duration * 1000, 2),
                error=str(exc),
                exc_info=exc,
            )

            raise


def log_firebase_operation(operation: str, **kwargs: Any) -> None:
    """Log Firebase operations."""
    logger = get_logger("app.firebase")
    logger.info("Firebase operation", operation=operation, **kwargs)


def log_api_call(
    endpoint: str, method: str, user_id: str = None, **kwargs: Any
) -> None:
    """Log API calls with context."""
    logger = get_logger("app.api")
    logger.info("API call", endpoint=endpoint, method=method, user_id=user_id, **kwargs)


def log_security_event(event_type: str, user_id: str = None, **kwargs: Any) -> None:
    """Log security-related events."""
    logger = get_logger("app.security")
    logger.warning("Security event", event_type=event_type, user_id=user_id, **kwargs)


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """Log errors with context."""
    logger = get_logger("app.error")
    logger.error(
        "Application error",
        error=str(error),
        error_type=type(error).__name__,
        context=context or {},
        exc_info=error,
    )
