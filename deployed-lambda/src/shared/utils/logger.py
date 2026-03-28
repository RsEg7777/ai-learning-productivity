"""Logging configuration and utilities."""

import logging
import sys
from typing import Optional
import structlog


def setup_logger(
    name: str = "ai_learning_assistant",
    level: str = "INFO",
    json_logs: bool = False,
) -> structlog.BoundLogger:
    """
    Set up structured logging.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output JSON logs

    Returns:
        Configured logger
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logger = structlog.get_logger(name)
    return logger


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a logger instance.

    Args:
        name: Logger name (optional)

    Returns:
        Logger instance
    """
    return structlog.get_logger(name or "ai_learning_assistant")


def log_function_call(logger: structlog.BoundLogger):
    """
    Decorator to log function calls.

    Args:
        logger: Logger instance

    Returns:
        Decorator function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(
                "function_called",
                function=func.__name__,
                args=args,
                kwargs=kwargs,
            )
            try:
                result = func(*args, **kwargs)
                logger.info(
                    "function_completed",
                    function=func.__name__,
                )
                return result
            except Exception as e:
                logger.error(
                    "function_failed",
                    function=func.__name__,
                    error=str(e),
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator
