"""Structured logging setup."""
import structlog


def get_logger(name: str) -> structlog.BoundLogger:
    """Create a structured logger with context."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )
    return structlog.get_logger(name)
