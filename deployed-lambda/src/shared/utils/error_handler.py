"""Centralized error handling system with CloudWatch integration and retry mechanisms."""

import logging
import time
import traceback
from typing import Optional, Dict, Any, Callable, Type, Tuple
from functools import wraps
from datetime import datetime
from enum import Enum

from .errors import (
    AILearningAssistantError,
    ContentProcessingError,
    AWSServiceError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
)
from .logger import get_logger

logger = get_logger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels for categorization."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetryStrategy(str, Enum):
    """Retry strategies for error recovery."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE = "immediate"
    NO_RETRY = "no_retry"


class ErrorContext:
    """Context information for error handling."""

    def __init__(
        self,
        operation: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize error context.

        Args:
            operation: Operation being performed
            user_id: User identifier
            resource_type: Type of resource
            resource_id: Resource identifier
            request_id: Request identifier for tracing
            metadata: Additional context metadata
        """
        self.operation = operation
        self.user_id = user_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.request_id = request_id
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "operation": self.operation,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class CentralizedErrorHandler:
    """Centralized error handling system with CloudWatch integration."""

    def __init__(
        self,
        service_name: str = "ai_learning_assistant",
        enable_cloudwatch: bool = True,
    ) -> None:
        """
        Initialize centralized error handler.

        Args:
            service_name: Name of the service
            enable_cloudwatch: Whether to enable CloudWatch logging
        """
        self.service_name = service_name
        self.enable_cloudwatch = enable_cloudwatch
        self.logger = get_logger(service_name)

    def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_friendly_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle an error with comprehensive logging and user-friendly messaging.

        Args:
            error: Exception that occurred
            context: Error context information
            severity: Error severity level
            user_friendly_message: Optional user-friendly message override

        Returns:
            Error response dictionary with user-friendly message
        """
        # Generate error ID for tracking
        error_id = self._generate_error_id()

        # Log detailed error information to CloudWatch
        self._log_error_to_cloudwatch(
            error=error,
            error_id=error_id,
            context=context,
            severity=severity,
        )

        # Generate user-friendly message
        friendly_message = user_friendly_message or self._generate_user_friendly_message(
            error, context
        )

        # Create error response
        error_response = {
            "error_id": error_id,
            "message": friendly_message,
            "severity": severity.value,
            "timestamp": context.timestamp.isoformat(),
        }

        # Add error code if available
        if isinstance(error, AILearningAssistantError):
            error_response["error_code"] = error.error_code
            # Include safe details (no sensitive information)
            error_response["details"] = self._sanitize_error_details(error.details)

        return error_response

    def _log_error_to_cloudwatch(
        self,
        error: Exception,
        error_id: str,
        context: ErrorContext,
        severity: ErrorSeverity,
    ) -> None:
        """
        Log detailed error information to CloudWatch.

        Args:
            error: Exception that occurred
            error_id: Unique error identifier
            context: Error context
            severity: Error severity
        """
        # Prepare detailed log entry
        log_entry = {
            "error_id": error_id,
            "service": self.service_name,
            "severity": severity.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context.to_dict(),
            "traceback": traceback.format_exc(),
        }

        # Add custom error details if available
        if isinstance(error, AILearningAssistantError):
            log_entry["error_code"] = error.error_code
            log_entry["error_details"] = error.details

        # Log to CloudWatch with appropriate severity
        log_level = self._severity_to_log_level(severity)
        self.logger.log(
            log_level,
            f"Error occurred: {type(error).__name__}",
            **log_entry,
        )

        # For critical errors, also log to stderr
        if severity == ErrorSeverity.CRITICAL:
            logging.critical(
                f"CRITICAL ERROR [{error_id}]: {str(error)}",
                extra=log_entry,
            )

    def _generate_user_friendly_message(
        self,
        error: Exception,
        context: ErrorContext,
    ) -> str:
        """
        Generate user-friendly error message.

        Args:
            error: Exception that occurred
            context: Error context

        Returns:
            User-friendly error message
        """
        # Map error types to user-friendly messages
        if isinstance(error, ValidationError):
            return self._format_validation_error(error)
        elif isinstance(error, AuthenticationError):
            return "Authentication failed. Please check your credentials and try again."
        elif isinstance(error, AuthorizationError):
            return "You don't have permission to perform this action."
        elif isinstance(error, ContentProcessingError):
            return self._format_content_processing_error(error, context)
        elif isinstance(error, AWSServiceError):
            return self._format_aws_service_error(error)
        else:
            # Generic error message
            return (
                f"An error occurred while {context.operation}. "
                "Our team has been notified and is working on a fix. "
                "Please try again later."
            )

    def _format_validation_error(self, error: ValidationError) -> str:
        """Format validation error message."""
        field = error.details.get("field")
        if field:
            return f"Invalid {field}: {error.message}"
        return f"Validation error: {error.message}"

    def _format_content_processing_error(
        self,
        error: ContentProcessingError,
        context: ErrorContext,
    ) -> str:
        """Format content processing error message."""
        content_type = error.details.get("content_type", "content")
        
        # Check for specific error types
        if "timeout" in str(error).lower():
            return (
                f"Processing your {content_type} is taking longer than expected. "
                "Please try with a smaller file or try again later."
            )
        elif "unsupported" in str(error).lower():
            return str(error)  # UnsupportedFormatError already has good messages
        else:
            return (
                f"We encountered an issue processing your {content_type}. "
                "Please check the file format and try again."
            )

    def _format_aws_service_error(self, error: AWSServiceError) -> str:
        """Format AWS service error message."""
        service = error.details.get("service", "service")
        
        # Map common AWS errors to user-friendly messages
        if "throttl" in str(error).lower():
            return (
                "We're experiencing high traffic right now. "
                "Please wait a moment and try again."
            )
        elif "not found" in str(error).lower():
            return "The requested resource was not found."
        elif "access denied" in str(error).lower():
            return "Access denied. Please check your permissions."
        else:
            return (
                f"A temporary {service} issue occurred. "
                "Please try again in a few moments."
            )

    def _sanitize_error_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize error details to remove sensitive information.

        Args:
            details: Error details dictionary

        Returns:
            Sanitized details dictionary
        """
        # List of keys that should not be exposed to users
        sensitive_keys = {
            "password", "token", "secret", "key", "credential",
            "api_key", "access_token", "refresh_token",
        }

        sanitized = {}
        for key, value in details.items():
            # Skip sensitive keys
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                continue
            
            # Include safe values
            if isinstance(value, (str, int, float, bool, list)):
                sanitized[key] = value
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_error_details(value)

        return sanitized

    @staticmethod
    def _generate_error_id() -> str:
        """Generate unique error ID for tracking."""
        import uuid
        return f"ERR-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def _severity_to_log_level(severity: ErrorSeverity) -> int:
        """Convert error severity to logging level."""
        severity_map = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }
        return severity_map.get(severity, logging.WARNING)


class RetryHandler:
    """Handler for automatic retry with various strategies."""

    def __init__(
        self,
        max_retries: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    ) -> None:
        """
        Initialize retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            strategy: Retry strategy to use
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            retryable_exceptions: Tuple of exception types that should trigger retry
        """
        self.max_retries = max_retries
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retryable_exceptions = retryable_exceptions or (
            AWSServiceError,
            ContentProcessingError,
        )
        self.logger = get_logger(__name__)

    def execute_with_retry(
        self,
        func: Callable,
        *args,
        context: Optional[ErrorContext] = None,
        **kwargs,
    ) -> Any:
        """
        Execute function with automatic retry on failure.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            context: Error context for logging
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                # Log successful retry if not first attempt
                if attempt > 0:
                    func_name = getattr(func, '__name__', repr(func))
                    self.logger.info(
                        "retry_succeeded",
                        attempt=attempt,
                        function=func_name,
                        context=context.to_dict() if context else {},
                    )
                
                return result

            except self.retryable_exceptions as e:
                last_exception = e
                
                # Don't retry if max attempts reached
                if attempt >= self.max_retries:
                    func_name = getattr(func, '__name__', repr(func))
                    self.logger.error(
                        "retry_exhausted",
                        attempt=attempt,
                        max_retries=self.max_retries,
                        function=func_name,
                        error=str(e),
                        context=context.to_dict() if context else {},
                    )
                    break

                # Calculate delay based on strategy
                delay = self._calculate_delay(attempt)
                
                func_name = getattr(func, '__name__', repr(func))
                self.logger.warning(
                    "retry_attempt",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    delay=delay,
                    function=func_name,
                    error=str(e),
                    context=context.to_dict() if context else {},
                )
                
                # Wait before retry
                time.sleep(delay)

            except Exception as e:
                # Non-retryable exception
                func_name = getattr(func, '__name__', repr(func))
                self.logger.error(
                    "non_retryable_error",
                    function=func_name,
                    error_type=type(e).__name__,
                    error=str(e),
                    context=context.to_dict() if context else {},
                )
                raise

        # All retries exhausted
        raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt based on strategy.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        if self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            # Exponential backoff: base_delay * 2^attempt
            delay = self.base_delay * (2 ** attempt)
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            # Linear backoff: base_delay * (attempt + 1)
            delay = self.base_delay * (attempt + 1)
        elif self.strategy == RetryStrategy.IMMEDIATE:
            # No delay
            delay = 0
        else:
            # Default to base delay
            delay = self.base_delay

        # Cap at max delay
        return min(delay, self.max_delay)


def with_error_handling(
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    user_friendly_message: Optional[str] = None,
):
    """
    Decorator for automatic error handling with CloudWatch logging.

    Args:
        operation: Operation name for context
        severity: Error severity level
        user_friendly_message: Optional user-friendly message override

    Returns:
        Decorated function with error handling

    Example:
        @with_error_handling(operation="process_content", severity=ErrorSeverity.HIGH)
        def process_content(content_id: str):
            # Function implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = CentralizedErrorHandler()
            context = ErrorContext(
                operation=operation,
                metadata={"function": func.__name__},
            )
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_response = error_handler.handle_error(
                    error=e,
                    context=context,
                    severity=severity,
                    user_friendly_message=user_friendly_message,
                )
                
                # Re-raise with error response attached
                if isinstance(e, AILearningAssistantError):
                    e.details["error_response"] = error_response
                raise

        return wrapper
    return decorator


def with_retry(
    max_retries: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    base_delay: float = 1.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
):
    """
    Decorator for automatic retry on failure.

    Args:
        max_retries: Maximum number of retry attempts
        strategy: Retry strategy to use
        base_delay: Base delay in seconds
        retryable_exceptions: Tuple of exception types that should trigger retry

    Returns:
        Decorated function with retry logic

    Example:
        @with_retry(max_retries=3, strategy=RetryStrategy.EXPONENTIAL_BACKOFF)
        def call_external_api():
            # Function implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_handler = RetryHandler(
                max_retries=max_retries,
                strategy=strategy,
                base_delay=base_delay,
                retryable_exceptions=retryable_exceptions,
            )
            
            context = ErrorContext(
                operation=func.__name__,
                metadata={"function": func.__name__},
            )
            
            return retry_handler.execute_with_retry(
                func, *args, context=context, **kwargs
            )

        return wrapper
    return decorator
