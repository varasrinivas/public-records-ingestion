"""Structured logging for pipeline operations."""
import structlog

def get_logger(name: str) -> structlog.BoundLogger:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )
    return structlog.get_logger(name)
