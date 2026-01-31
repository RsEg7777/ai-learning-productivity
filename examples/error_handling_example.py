"""Example demonstrating centralized error handling system."""

import time
from datetime import datetime

from src.shared.utils.error_handler import (
    CentralizedErrorHandler,
    RetryHandler,
    ErrorContext,
    ErrorSeverity,
    RetryStrategy,
    with_error_handling,
    with_retry,
)
from src.shared.utils.errors import (
    ContentProcessingError,
    AWSServiceError,
    ValidationError,
    UnsupportedFormatError,
)


def example_basic_error_handling():
    """Example: Basic error handling with CloudWatch logging."""
    print("\n=== Example 1: Basic Error Handling ===\n")
    
    # Initialize error handler
    error_handler = CentralizedErrorHandler(
        service_name="content_processing",
        enable_cloudwatch=True,
    )
    
    # Simulate an error
    try:
        # This would be actual processing code
        raise ContentProcessingError(
            message="Failed to extract text from PDF",
            content_type="pdf",
            details={"file_size": 5242880, "pages": 50},
        )
    except Exception as e:
        # Create error context
        context = ErrorContext(
            operation="process_pdf",
            user_id="user123",
            resource_type="content",
            resource_id="content456",
            request_id="req789",
            metadata={"filename": "document.pdf"},
        )
        
        # Handle error
        error_response = error_handler.handle_error(
            error=e,
            context=context,
            severity=ErrorSeverity.HIGH,
        )
        
        print(f"Error ID: {error_response['error_id']}")
        print(f"User Message: {error_response['message']}")
        print(f"Severity: {error_response['severity']}")
        print(f"Error Code: {error_response.get('error_code')}")


def example_retry_mechanism():
    """Example: Automatic retry with exponential backoff."""
    print("\n=== Example 2: Retry Mechanism ===\n")
    
    # Initialize retry handler
    retry_handler = RetryHandler(
        max_retries=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=1.0,
        max_delay=10.0,
    )
    
    # Simulate a function that fails initially but succeeds on retry
    attempt_count = {"count": 0}
    
    def unstable_operation():
        attempt_count["count"] += 1
        print(f"Attempt {attempt_count['count']}...")
        
        if attempt_count["count"] < 3:
            raise AWSServiceError(
                message="Temporary service unavailability",
                service="Bedrock",
                operation="invoke_model",
            )
        
        return "Success!"
    
    # Execute with retry
    context = ErrorContext(operation="invoke_bedrock_model")
    
    try:
        result = retry_handler.execute_with_retry(
            unstable_operation,
            context=context,
        )
        print(f"Result: {result}")
        print(f"Total attempts: {attempt_count['count']}")
    except Exception as e:
        print(f"Failed after all retries: {e}")


def example_decorator_usage():
    """Example: Using decorators for error handling and retry."""
    print("\n=== Example 3: Decorator Usage ===\n")
    
    # Example 1: Error handling decorator
    @with_error_handling(
        operation="validate_user_input",
        severity=ErrorSeverity.MEDIUM,
    )
    def validate_email(email: str):
        if "@" not in email:
            raise ValidationError(
                message="Invalid email format",
                field="email",
            )
        return True
    
    # Example 2: Retry decorator
    call_count = {"count": 0}
    
    @with_retry(
        max_retries=2,
        strategy=RetryStrategy.LINEAR_BACKOFF,
        base_delay=0.5,
    )
    def fetch_from_api():
        call_count["count"] += 1
        print(f"API call attempt {call_count['count']}")
        
        if call_count["count"] < 2:
            raise AWSServiceError(
                message="Rate limit exceeded",
                service="API Gateway",
                operation="invoke",
            )
        
        return {"data": "success"}
    
    # Example 3: Combined decorators
    @with_retry(max_retries=2, strategy=RetryStrategy.IMMEDIATE, base_delay=0.1)
    @with_error_handling(operation="process_content", severity=ErrorSeverity.HIGH)
    def process_content(content_id: str):
        # Simulated processing
        return f"Processed content {content_id}"
    
    # Test validation
    try:
        validate_email("invalid-email")
    except ValidationError as e:
        print(f"Validation failed: {e.message}")
        print(f"Error response attached: {e.details.get('error_response', {}).get('error_id')}")
    
    # Test retry
    result = fetch_from_api()
    print(f"API result: {result}")
    
    # Test combined
    result = process_content("content123")
    print(f"Processing result: {result}")


def example_user_friendly_messages():
    """Example: User-friendly error messages."""
    print("\n=== Example 4: User-Friendly Messages ===\n")
    
    error_handler = CentralizedErrorHandler()
    
    # Test different error types
    errors = [
        (
            ValidationError("Email format is invalid", field="email"),
            ErrorContext(operation="validate_registration"),
            "Validation Error",
        ),
        (
            UnsupportedFormatError(
                format_provided=".xyz",
                supported_formats=[".txt", ".pdf", ".mp4"],
                suggestions=[".pdf", ".txt"],
            ),
            ErrorContext(operation="upload_file"),
            "Unsupported Format",
        ),
        (
            AWSServiceError(
                message="ThrottlingException: Rate exceeded",
                service="Bedrock",
                operation="invoke_model",
            ),
            ErrorContext(operation="generate_summary"),
            "AWS Throttling",
        ),
        (
            ContentProcessingError(
                message="Processing timeout exceeded",
                content_type="video",
            ),
            ErrorContext(operation="process_video"),
            "Processing Timeout",
        ),
    ]
    
    for error, context, error_name in errors:
        response = error_handler.handle_error(
            error=error,
            context=context,
            severity=ErrorSeverity.MEDIUM,
        )
        
        print(f"\n{error_name}:")
        print(f"  Error ID: {response['error_id']}")
        print(f"  User Message: {response['message']}")


def example_error_recovery():
    """Example: Error recovery with fallback."""
    print("\n=== Example 5: Error Recovery ===\n")
    
    retry_handler = RetryHandler(
        max_retries=2,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=0.5,
    )
    
    def primary_processing(content: str):
        """Primary processing method (may fail)."""
        print("Attempting primary processing...")
        raise ContentProcessingError(
            message="Advanced processing failed",
            content_type="text",
        )
    
    def fallback_processing(content: str):
        """Fallback processing method (simpler, more reliable)."""
        print("Using fallback processing...")
        return {
            "summary": content[:100] + "...",
            "key_points": ["Basic extraction"],
            "method": "fallback",
        }
    
    # Try primary, fall back on failure
    content = "This is a long piece of content that needs processing..."
    
    try:
        result = primary_processing(content)
    except ContentProcessingError as e:
        print(f"Primary processing failed: {e.message}")
        print("Falling back to simpler processing...")
        result = fallback_processing(content)
    
    print(f"Result: {result}")
    print(f"Processing method: {result['method']}")


def example_cloudwatch_integration():
    """Example: CloudWatch integration for monitoring."""
    print("\n=== Example 6: CloudWatch Integration ===\n")
    
    # Note: This requires actual AWS credentials and CloudWatch setup
    # For demonstration, we'll show the structure
    
    from src.shared.aws_clients.cloudwatch_client import CloudWatchClient
    
    print("CloudWatch integration example:")
    print("1. Error logs are automatically sent to CloudWatch Logs")
    print("2. Metrics are tracked for monitoring and alerting")
    print("3. Structured logging enables easy querying and analysis")
    print("\nLog structure:")
    print({
        "error_id": "ERR-ABC123",
        "service": "ai_learning_assistant",
        "severity": "high",
        "error_type": "ContentProcessingError",
        "error_message": "Failed to process content",
        "context": {
            "operation": "process_pdf",
            "user_id": "user123",
            "resource_type": "content",
            "resource_id": "content456",
        },
        "timestamp": datetime.utcnow().isoformat(),
    })


def example_custom_error_messages():
    """Example: Custom user-friendly messages."""
    print("\n=== Example 7: Custom Error Messages ===\n")
    
    error_handler = CentralizedErrorHandler()
    
    # Use custom message instead of auto-generated one
    error = ContentProcessingError(
        message="Technical error: PDF extraction failed at page 42",
        content_type="pdf",
    )
    
    context = ErrorContext(
        operation="process_pdf",
        user_id="user123",
    )
    
    custom_message = (
        "We're having trouble processing your PDF. "
        "This might be due to complex formatting or large file size. "
        "Please try splitting the document into smaller parts."
    )
    
    response = error_handler.handle_error(
        error=error,
        context=context,
        severity=ErrorSeverity.MEDIUM,
        user_friendly_message=custom_message,
    )
    
    print(f"Error ID: {response['error_id']}")
    print(f"Custom Message: {response['message']}")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Centralized Error Handling System Examples")
    print("=" * 60)
    
    example_basic_error_handling()
    example_retry_mechanism()
    example_decorator_usage()
    example_user_friendly_messages()
    example_error_recovery()
    example_cloudwatch_integration()
    example_custom_error_messages()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
