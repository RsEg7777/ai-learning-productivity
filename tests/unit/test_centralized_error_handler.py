"""Unit tests for centralized error handling system."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
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
    AILearningAssistantError,
    ContentProcessingError,
    AWSServiceError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    UnsupportedFormatError,
)


class TestErrorContext:
    """Test ErrorContext class."""

    def test_error_context_initialization(self):
        """Test error context initialization."""
        context = ErrorContext(
            operation="test_operation",
            user_id="user123",
            resource_type="content",
            resource_id="content456",
            request_id="req789",
            metadata={"key": "value"},
        )

        assert context.operation == "test_operation"
        assert context.user_id == "user123"
        assert context.resource_type == "content"
        assert context.resource_id == "content456"
        assert context.request_id == "req789"
        assert context.metadata == {"key": "value"}
        assert isinstance(context.timestamp, datetime)

    def test_error_context_to_dict(self):
        """Test error context conversion to dictionary."""
        context = ErrorContext(
            operation="test_operation",
            user_id="user123",
        )

        context_dict = context.to_dict()

        assert context_dict["operation"] == "test_operation"
        assert context_dict["user_id"] == "user123"
        assert "timestamp" in context_dict
        assert isinstance(context_dict["metadata"], dict)


class TestCentralizedErrorHandler:
    """Test CentralizedErrorHandler class."""

    def test_initialization(self):
        """Test error handler initialization."""
        handler = CentralizedErrorHandler(
            service_name="test_service",
            enable_cloudwatch=True,
        )

        assert handler.service_name == "test_service"
        assert handler.enable_cloudwatch is True

    def test_handle_validation_error(self):
        """Test handling validation error."""
        handler = CentralizedErrorHandler()
        error = ValidationError(
            message="Invalid email format",
            field="email",
        )
        context = ErrorContext(operation="validate_user_input")

        with patch.object(handler, "_log_error_to_cloudwatch"):
            response = handler.handle_error(error, context)

        assert "error_id" in response
        assert "message" in response
        assert "Invalid email" in response["message"]
        assert response["error_code"] == "VALIDATION_ERROR"
        assert response["severity"] == ErrorSeverity.MEDIUM.value

    def test_handle_authentication_error(self):
        """Test handling authentication error."""
        handler = CentralizedErrorHandler()
        error = AuthenticationError(message="Invalid credentials")
        context = ErrorContext(operation="user_login")

        with patch.object(handler, "_log_error_to_cloudwatch"):
            response = handler.handle_error(error, context)

        assert "Authentication failed" in response["message"]
        assert response["error_code"] == "AUTHENTICATION_ERROR"

    def test_handle_authorization_error(self):
        """Test handling authorization error."""
        handler = CentralizedErrorHandler()
        error = AuthorizationError(resource="content/123")
        context = ErrorContext(operation="access_content")

        with patch.object(handler, "_log_error_to_cloudwatch"):
            response = handler.handle_error(error, context)

        assert "permission" in response["message"].lower()
        assert response["error_code"] == "AUTHORIZATION_ERROR"

    def test_handle_content_processing_error(self):
        """Test handling content processing error."""
        handler = CentralizedErrorHandler()
        error = ContentProcessingError(
            message="Failed to process PDF",
            content_type="pdf",
        )
        context = ErrorContext(operation="process_content")

        with patch.object(handler, "_log_error_to_cloudwatch"):
            response = handler.handle_error(error, context)

        assert "processing" in response["message"].lower()
        assert response["error_code"] == "CONTENT_PROCESSING_ERROR"

    def test_handle_aws_service_error_throttling(self):
        """Test handling AWS service throttling error."""
        handler = CentralizedErrorHandler()
        error = AWSServiceError(
            message="Rate exceeded - throttling",
            service="Bedrock",
            operation="invoke_model",
        )
        context = ErrorContext(operation="generate_summary")

        with patch.object(handler, "_log_error_to_cloudwatch"):
            response = handler.handle_error(error, context)

        # Check that message mentions traffic or waiting
        assert "traffic" in response["message"].lower() or "wait" in response["message"].lower()

    def test_handle_unsupported_format_error(self):
        """Test handling unsupported format error."""
        handler = CentralizedErrorHandler()
        error = UnsupportedFormatError(
            format_provided=".xyz",
            supported_formats=[".txt", ".pdf", ".mp4"],
            suggestions=[".pdf", ".txt"],
        )
        context = ErrorContext(operation="upload_content")

        with patch.object(handler, "_log_error_to_cloudwatch"):
            response = handler.handle_error(error, context)

        # UnsupportedFormatError already has good messages
        assert ".xyz" in response["message"]

    def test_user_friendly_message_override(self):
        """Test user-friendly message override."""
        handler = CentralizedErrorHandler()
        error = Exception("Technical error message")
        context = ErrorContext(operation="test_operation")
        custom_message = "Something went wrong. Please try again."

        with patch.object(handler, "_log_error_to_cloudwatch"):
            response = handler.handle_error(
                error,
                context,
                user_friendly_message=custom_message,
            )

        assert response["message"] == custom_message

    def test_sanitize_error_details(self):
        """Test sanitization of error details."""
        handler = CentralizedErrorHandler()
        details = {
            "user_id": "user123",
            "password": "secret123",
            "api_key": "key123",
            "content_type": "pdf",
            "nested": {
                "token": "token123",
                "safe_value": "visible",
            },
        }

        sanitized = handler._sanitize_error_details(details)

        assert "user_id" in sanitized
        assert "content_type" in sanitized
        assert "password" not in sanitized
        assert "api_key" not in sanitized
        assert "token" not in sanitized["nested"]
        assert "safe_value" in sanitized["nested"]

    def test_error_id_generation(self):
        """Test error ID generation."""
        error_id = CentralizedErrorHandler._generate_error_id()

        assert error_id.startswith("ERR-")
        assert len(error_id) == 16  # ERR- + 12 hex chars

    def test_severity_to_log_level(self):
        """Test severity to log level conversion."""
        import logging

        assert CentralizedErrorHandler._severity_to_log_level(
            ErrorSeverity.LOW
        ) == logging.INFO
        assert CentralizedErrorHandler._severity_to_log_level(
            ErrorSeverity.MEDIUM
        ) == logging.WARNING
        assert CentralizedErrorHandler._severity_to_log_level(
            ErrorSeverity.HIGH
        ) == logging.ERROR
        assert CentralizedErrorHandler._severity_to_log_level(
            ErrorSeverity.CRITICAL
        ) == logging.CRITICAL

    def test_log_error_to_cloudwatch(self):
        """Test logging error to CloudWatch."""
        handler = CentralizedErrorHandler()
        error = ContentProcessingError(
            message="Test error",
            content_type="text",
        )
        context = ErrorContext(operation="test_operation")

        with patch.object(handler.logger, "log") as mock_log:
            handler._log_error_to_cloudwatch(
                error=error,
                error_id="ERR-TEST123",
                context=context,
                severity=ErrorSeverity.HIGH,
            )

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][1] == "Error occurred: ContentProcessingError"


class TestRetryHandler:
    """Test RetryHandler class."""

    def test_initialization(self):
        """Test retry handler initialization."""
        handler = RetryHandler(
            max_retries=5,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=2.0,
        )

        assert handler.max_retries == 5
        assert handler.strategy == RetryStrategy.LINEAR_BACKOFF
        assert handler.base_delay == 2.0

    def test_successful_execution_no_retry(self):
        """Test successful execution without retry."""
        handler = RetryHandler(max_retries=3)
        mock_func = Mock(return_value="success")

        result = handler.execute_with_retry(mock_func)

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_on_retryable_exception(self):
        """Test retry on retryable exception."""
        handler = RetryHandler(
            max_retries=2,
            strategy=RetryStrategy.IMMEDIATE,
            base_delay=0.01,
        )
        mock_func = Mock(side_effect=[
            AWSServiceError("Error 1", "S3", "get_object"),
            AWSServiceError("Error 2", "S3", "get_object"),
            "success",
        ])

        result = handler.execute_with_retry(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3

    def test_retry_exhausted(self):
        """Test retry exhaustion."""
        handler = RetryHandler(
            max_retries=2,
            strategy=RetryStrategy.IMMEDIATE,
            base_delay=0.01,
        )
        error = AWSServiceError("Persistent error", "S3", "get_object")
        mock_func = Mock(side_effect=error)

        with pytest.raises(AWSServiceError):
            handler.execute_with_retry(mock_func)

        assert mock_func.call_count == 3  # Initial + 2 retries

    def test_non_retryable_exception(self):
        """Test non-retryable exception."""
        handler = RetryHandler(
            max_retries=3,
            retryable_exceptions=(AWSServiceError,),
        )
        mock_func = Mock(side_effect=ValueError("Not retryable"))

        with pytest.raises(ValueError):
            handler.execute_with_retry(mock_func)

        assert mock_func.call_count == 1  # No retry

    def test_exponential_backoff_delay(self):
        """Test exponential backoff delay calculation."""
        handler = RetryHandler(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=10.0,
        )

        assert handler._calculate_delay(0) == 1.0  # 1 * 2^0
        assert handler._calculate_delay(1) == 2.0  # 1 * 2^1
        assert handler._calculate_delay(2) == 4.0  # 1 * 2^2
        assert handler._calculate_delay(3) == 8.0  # 1 * 2^3
        assert handler._calculate_delay(4) == 10.0  # Capped at max_delay

    def test_linear_backoff_delay(self):
        """Test linear backoff delay calculation."""
        handler = RetryHandler(
            strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=2.0,
            max_delay=10.0,
        )

        assert handler._calculate_delay(0) == 2.0  # 2 * 1
        assert handler._calculate_delay(1) == 4.0  # 2 * 2
        assert handler._calculate_delay(2) == 6.0  # 2 * 3
        assert handler._calculate_delay(3) == 8.0  # 2 * 4
        assert handler._calculate_delay(4) == 10.0  # Capped at max_delay

    def test_immediate_retry_delay(self):
        """Test immediate retry (no delay)."""
        handler = RetryHandler(
            strategy=RetryStrategy.IMMEDIATE,
            base_delay=5.0,
        )

        assert handler._calculate_delay(0) == 0
        assert handler._calculate_delay(1) == 0
        assert handler._calculate_delay(2) == 0

    def test_retry_with_context(self):
        """Test retry with error context."""
        handler = RetryHandler(
            max_retries=1,
            strategy=RetryStrategy.IMMEDIATE,
        )
        mock_func = Mock(side_effect=[
            AWSServiceError("Error", "S3", "get_object"),
            "success",
        ])
        context = ErrorContext(operation="test_operation")

        result = handler.execute_with_retry(mock_func, context=context)

        assert result == "success"


class TestErrorHandlingDecorators:
    """Test error handling decorators."""

    def test_with_error_handling_decorator_success(self):
        """Test with_error_handling decorator on successful execution."""
        @with_error_handling(operation="test_operation")
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

    def test_with_error_handling_decorator_error(self):
        """Test with_error_handling decorator on error."""
        @with_error_handling(
            operation="test_operation",
            severity=ErrorSeverity.HIGH,
        )
        def test_func():
            raise ValidationError("Test error", field="test_field")

        with pytest.raises(ValidationError) as exc_info:
            test_func()

        # Check that error response was attached
        assert "error_response" in exc_info.value.details

    def test_with_retry_decorator_success(self):
        """Test with_retry decorator on successful execution."""
        @with_retry(max_retries=3)
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

    def test_with_retry_decorator_with_retries(self):
        """Test with_retry decorator with retries."""
        call_count = {"count": 0}

        @with_retry(
            max_retries=2,
            strategy=RetryStrategy.IMMEDIATE,
            base_delay=0.01,
        )
        def test_func():
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise AWSServiceError("Temporary error", "S3", "get_object")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count["count"] == 3

    def test_with_retry_decorator_exhausted(self):
        """Test with_retry decorator when retries exhausted."""
        @with_retry(
            max_retries=2,
            strategy=RetryStrategy.IMMEDIATE,
            base_delay=0.01,
        )
        def test_func():
            raise AWSServiceError("Persistent error", "S3", "get_object")

        with pytest.raises(AWSServiceError):
            test_func()


class TestErrorMessageFormatting:
    """Test error message formatting."""

    def test_format_validation_error_with_field(self):
        """Test formatting validation error with field."""
        handler = CentralizedErrorHandler()
        error = ValidationError("Invalid format", field="email")

        message = handler._format_validation_error(error)

        assert "email" in message.lower()
        assert "invalid" in message.lower()

    def test_format_validation_error_without_field(self):
        """Test formatting validation error without field."""
        handler = CentralizedErrorHandler()
        error = ValidationError("Invalid input")

        message = handler._format_validation_error(error)

        assert "validation error" in message.lower()

    def test_format_content_processing_timeout(self):
        """Test formatting content processing timeout error."""
        handler = CentralizedErrorHandler()
        error = ContentProcessingError(
            message="Processing timeout exceeded",
            content_type="video",
        )
        context = ErrorContext(operation="process_video")

        message = handler._format_content_processing_error(error, context)

        assert "longer than expected" in message.lower() or "timeout" in message.lower()

    def test_format_aws_throttling_error(self):
        """Test formatting AWS throttling error."""
        handler = CentralizedErrorHandler()
        error = AWSServiceError(
            message="Rate limit exceeded - throttling",
            service="Bedrock",
        )

        message = handler._format_aws_service_error(error)

        assert "traffic" in message.lower() or "wait" in message.lower()

    def test_format_aws_not_found_error(self):
        """Test formatting AWS not found error."""
        handler = CentralizedErrorHandler()
        error = AWSServiceError(
            message="Resource not found",
            service="S3",
        )

        message = handler._format_aws_service_error(error)

        assert "not found" in message.lower()

    def test_format_aws_access_denied_error(self):
        """Test formatting AWS access denied error."""
        handler = CentralizedErrorHandler()
        error = AWSServiceError(
            message="Access denied to resource",
            service="S3",
        )

        message = handler._format_aws_service_error(error)

        assert "access denied" in message.lower() or "permission" in message.lower()


class TestIntegration:
    """Integration tests for error handling system."""

    def test_end_to_end_error_handling(self):
        """Test end-to-end error handling flow."""
        handler = CentralizedErrorHandler()
        
        # Simulate an error in a service
        error = ContentProcessingError(
            message="Failed to extract text from PDF",
            content_type="pdf",
            details={"file_size": 1024000, "pages": 50},
        )
        
        context = ErrorContext(
            operation="process_pdf",
            user_id="user123",
            resource_type="content",
            resource_id="content456",
        )

        with patch.object(handler, "_log_error_to_cloudwatch"):
            response = handler.handle_error(
                error=error,
                context=context,
                severity=ErrorSeverity.HIGH,
            )

        # Verify response structure
        assert "error_id" in response
        assert "message" in response
        assert "severity" in response
        assert "timestamp" in response
        assert "error_code" in response
        assert response["error_code"] == "CONTENT_PROCESSING_ERROR"
        assert response["severity"] == ErrorSeverity.HIGH.value

    def test_retry_with_error_handling(self):
        """Test retry mechanism with error handling."""
        call_count = {"count": 0}

        @with_retry(max_retries=2, strategy=RetryStrategy.IMMEDIATE, base_delay=0.01)
        @with_error_handling(operation="test_operation")
        def test_func():
            call_count["count"] += 1
            if call_count["count"] < 2:
                raise AWSServiceError("Temporary error", "S3", "get_object")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count["count"] == 2
