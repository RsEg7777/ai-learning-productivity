"""Utilities for graceful degradation during content processing."""

import logging
from typing import Optional, Callable, Any, Dict
from functools import wraps

from .errors import (
    ContentProcessingError,
    ProcessingTimeoutError,
    PartialProcessingError,
)

logger = logging.getLogger(__name__)


def with_fallback(
    fallback_value: Any = None,
    fallback_fn: Optional[Callable] = None,
    log_error: bool = True,
    error_types: tuple = (Exception,),
):
    """
    Decorator for graceful degradation with fallback values.

    When a function fails, returns a fallback value or calls a fallback function
    instead of propagating the exception.

    Args:
        fallback_value: Value to return on error (if fallback_fn not provided)
        fallback_fn: Function to call on error to generate fallback value
        log_error: Whether to log the error
        error_types: Tuple of exception types to catch

    Returns:
        Decorated function with fallback behavior

    Example:
        @with_fallback(fallback_value=[])
        def extract_key_points(text):
            # May fail, but will return [] instead of raising
            return complex_extraction(text)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                if log_error:
                    logger.warning(
                        f"Function {func.__name__} failed with {type(e).__name__}: {e}. "
                        f"Using fallback value."
                    )
                
                if fallback_fn:
                    try:
                        return fallback_fn(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(
                            f"Fallback function also failed: {fallback_error}. "
                            f"Returning default fallback value."
                        )
                        return fallback_value
                
                return fallback_value
        
        return wrapper
    return decorator


def try_with_degradation(
    primary_fn: Callable,
    fallback_fn: Optional[Callable] = None,
    error_message: str = "Operation failed",
    content_type: str = "unknown",
) -> Any:
    """
    Try a primary function, fall back to a simpler version on failure.

    This function implements graceful degradation by attempting a primary
    operation and falling back to a simpler alternative if it fails.

    Args:
        primary_fn: Primary function to try
        fallback_fn: Fallback function to use if primary fails
        error_message: Error message for logging
        content_type: Content type for error context

    Returns:
        Result from primary_fn or fallback_fn

    Raises:
        ContentProcessingError: If both primary and fallback fail

    Example:
        result = try_with_degradation(
            primary_fn=lambda: complex_summary(text),
            fallback_fn=lambda: simple_summary(text),
            error_message="Summary generation failed",
            content_type="text"
        )
    """
    try:
        return primary_fn()
    except Exception as primary_error:
        logger.warning(
            f"{error_message} (primary method): {primary_error}. "
            f"Attempting fallback method."
        )
        
        if fallback_fn:
            try:
                result = fallback_fn()
                logger.info(f"Fallback method succeeded for {content_type}")
                return result
            except Exception as fallback_error:
                logger.error(
                    f"{error_message} (fallback method): {fallback_error}"
                )
                raise ContentProcessingError(
                    message=f"{error_message}: both primary and fallback methods failed",
                    content_type=content_type,
                    details={
                        "primary_error": str(primary_error),
                        "fallback_error": str(fallback_error),
                    },
                )
        else:
            raise ContentProcessingError(
                message=f"{error_message}: {primary_error}",
                content_type=content_type,
                details={"error": str(primary_error)},
            )


def partial_success_handler(
    operation_name: str,
    content_type: str,
    partial_result: Any,
    error: Exception,
    required_fields: Optional[list] = None,
) -> Any:
    """
    Handle partial success scenarios in content processing.

    When an operation partially succeeds (e.g., extracts some but not all data),
    this function logs the issue and returns the partial result with appropriate
    warnings.

    Args:
        operation_name: Name of the operation
        content_type: Type of content being processed
        partial_result: Partial result that was obtained
        error: Exception that caused partial failure
        required_fields: List of required fields to check in partial_result

    Returns:
        Partial result with warnings

    Raises:
        PartialProcessingError: If partial result is insufficient

    Example:
        try:
            result = extract_all_data(content)
        except Exception as e:
            result = extract_basic_data(content)
            return partial_success_handler(
                operation_name="data extraction",
                content_type="pdf",
                partial_result=result,
                error=e,
                required_fields=["text", "metadata"]
            )
    """
    logger.warning(
        f"Partial success in {operation_name} for {content_type}: {error}. "
        f"Returning partial result."
    )
    
    # Check if partial result has required fields
    if required_fields and isinstance(partial_result, dict):
        missing_fields = [
            field for field in required_fields
            if field not in partial_result or partial_result[field] is None
        ]
        
        if missing_fields:
            raise PartialProcessingError(
                message=(
                    f"Partial {operation_name} failed: missing required fields: "
                    f"{', '.join(missing_fields)}"
                ),
                content_type=content_type,
                partial_result=partial_result,
                details={
                    "missing_fields": missing_fields,
                    "error": str(error),
                },
            )
    
    # Add warning metadata to partial result
    if isinstance(partial_result, dict):
        partial_result["_warnings"] = partial_result.get("_warnings", [])
        partial_result["_warnings"].append({
            "operation": operation_name,
            "message": f"Partial success: {str(error)}",
            "severity": "warning",
        })
    
    return partial_result


def create_minimal_result(
    content_type: str,
    original_content: str,
    error: Exception,
    processing_time: float,
) -> Dict[str, Any]:
    """
    Create a minimal result when processing fails completely.

    This function creates a basic result structure with minimal information
    when content processing fails, allowing the system to continue operating
    with degraded functionality.

    Args:
        content_type: Type of content
        original_content: Original content text
        error: Exception that caused failure
        processing_time: Time spent processing

    Returns:
        Minimal result dictionary

    Example:
        try:
            result = process_content(content)
        except Exception as e:
            result = create_minimal_result(
                content_type="text",
                original_content=content,
                error=e,
                processing_time=time.time() - start_time
            )
    """
    logger.warning(
        f"Creating minimal result for {content_type} due to processing failure: {error}"
    )
    
    # Extract basic information from content
    word_count = len(original_content.split()) if original_content else 0
    char_count = len(original_content) if original_content else 0
    
    # Create minimal summary (first 200 characters)
    minimal_summary = (
        original_content[:200] + "..."
        if original_content and len(original_content) > 200
        else original_content or "No content available"
    )
    
    return {
        "summary": minimal_summary,
        "key_points": [],
        "concepts": [],
        "metadata": {
            "word_count": word_count,
            "char_count": char_count,
            "processing_failed": True,
            "error_message": str(error),
            "processing_time": processing_time,
        },
        "_warnings": [{
            "operation": "content_processing",
            "message": f"Processing failed: {str(error)}. Returning minimal result.",
            "severity": "error",
        }],
    }


def validate_processing_result(
    result: Dict[str, Any],
    required_fields: list,
    content_type: str,
) -> bool:
    """
    Validate that a processing result contains required fields.

    Args:
        result: Processing result to validate
        required_fields: List of required field names
        content_type: Type of content for error messages

    Returns:
        True if valid, False otherwise

    Raises:
        ContentProcessingError: If result is invalid and cannot be recovered
    """
    if not isinstance(result, dict):
        raise ContentProcessingError(
            message=f"Invalid result type: expected dict, got {type(result).__name__}",
            content_type=content_type,
        )
    
    missing_fields = [
        field for field in required_fields
        if field not in result or result[field] is None
    ]
    
    if missing_fields:
        logger.warning(
            f"Processing result for {content_type} missing fields: {missing_fields}"
        )
        return False
    
    return True
