"""Custom error classes for the AI Learning Assistant."""

from typing import Optional, Dict, Any


class AILearningAssistantError(Exception):
    """Base exception for all AI Learning Assistant errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize error.

        Args:
            message: Error message
            error_code: Error code for categorization
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ContentProcessingError(AILearningAssistantError):
    """Error during content processing."""

    def __init__(
        self,
        message: str,
        content_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize content processing error.

        Args:
            message: Error message
            content_type: Type of content being processed
            details: Additional error details
        """
        error_details = details or {}
        if content_type:
            error_details["content_type"] = content_type

        super().__init__(
            message=message,
            error_code="CONTENT_PROCESSING_ERROR",
            details=error_details,
        )


class UnsupportedFormatError(ContentProcessingError):
    """Error for unsupported file formats."""

    def __init__(
        self,
        format_provided: str,
        supported_formats: list,
        suggestions: Optional[list] = None,
    ) -> None:
        """
        Initialize unsupported format error.

        Args:
            format_provided: The format that was provided
            supported_formats: List of supported formats
            suggestions: Optional list of suggested formats based on similarity
        """
        # Create detailed error message with suggestions
        message_parts = [
            f"Unsupported file format: '{format_provided}'.",
            f"\n\nSupported formats:",
        ]
        
        # Group formats by content type for better readability
        format_groups = {
            "Text": [".txt", ".md", ".markdown"],
            "PDF": [".pdf"],
            "Video": [".mp4", ".avi", ".mov", ".mkv", ".webm"],
            "Audio": [".mp3", ".wav", ".m4a", ".flac", ".ogg"],
            "Code": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".cs", ".go", ".rs", ".php", ".rb"],
        }
        
        for category, formats in format_groups.items():
            if any(fmt in supported_formats for fmt in formats):
                category_formats = [fmt for fmt in formats if fmt in supported_formats]
                message_parts.append(f"\n  • {category}: {', '.join(category_formats)}")
        
        # Add suggestions if provided
        if suggestions:
            message_parts.append(f"\n\nDid you mean one of these? {', '.join(suggestions)}")
        
        message = "".join(message_parts)
        
        super().__init__(
            message=message,
            details={
                "format_provided": format_provided,
                "supported_formats": supported_formats,
                "suggestions": suggestions or [],
            },
        )
        self.error_code = "UNSUPPORTED_FORMAT"


class ProcessingTimeoutError(ContentProcessingError):
    """Error when content processing exceeds time limit."""

    def __init__(
        self,
        content_type: str,
        time_limit: int,
        time_elapsed: int,
    ) -> None:
        """
        Initialize processing timeout error.

        Args:
            content_type: Type of content
            time_limit: Time limit in seconds
            time_elapsed: Time elapsed in seconds
        """
        message = (
            f"Processing timeout: {content_type} processing exceeded "
            f"{time_limit}s limit (elapsed: {time_elapsed}s)"
        )
        super().__init__(
            message=message,
            content_type=content_type,
            details={
                "time_limit": time_limit,
                "time_elapsed": time_elapsed,
            },
        )
        self.error_code = "PROCESSING_TIMEOUT"


class PartialProcessingError(ContentProcessingError):
    """Error when processing partially succeeds with degraded results."""

    def __init__(
        self,
        message: str,
        content_type: str,
        partial_result: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize partial processing error.

        Args:
            message: Error message
            content_type: Type of content
            partial_result: Partial result that was obtained
            details: Additional error details
        """
        error_details = details or {}
        error_details["has_partial_result"] = partial_result is not None
        
        super().__init__(
            message=message,
            content_type=content_type,
            details=error_details,
        )
        self.error_code = "PARTIAL_PROCESSING"
        self.partial_result = partial_result


class AuthenticationError(AILearningAssistantError):
    """Error during authentication."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize authentication error.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )


class AuthorizationError(AILearningAssistantError):
    """Error during authorization."""

    def __init__(
        self,
        message: str = "Access denied",
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize authorization error.

        Args:
            message: Error message
            resource: Resource being accessed
            details: Additional error details
        """
        error_details = details or {}
        if resource:
            error_details["resource"] = resource

        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=error_details,
        )


class ValidationError(AILearningAssistantError):
    """Error during input validation."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation
            details: Additional error details
        """
        error_details = details or {}
        if field:
            error_details["field"] = field

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=error_details,
        )


class AWSServiceError(AILearningAssistantError):
    """Error from AWS services."""

    def __init__(
        self,
        message: str,
        service: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize AWS service error.

        Args:
            message: Error message
            service: AWS service name
            operation: Operation that failed
            details: Additional error details
        """
        error_details = details or {}
        error_details["service"] = service
        if operation:
            error_details["operation"] = operation

        super().__init__(
            message=message,
            error_code="AWS_SERVICE_ERROR",
            details=error_details,
        )


class QuizGenerationError(AILearningAssistantError):
    """Error during quiz generation."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize quiz generation error.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="QUIZ_GENERATION_ERROR",
            details=details,
        )


class CodeAnalysisError(AILearningAssistantError):
    """Error during code analysis."""

    def __init__(
        self,
        message: str,
        language: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize code analysis error.

        Args:
            message: Error message
            language: Programming language
            details: Additional error details
        """
        error_details = details or {}
        if language:
            error_details["language"] = language

        super().__init__(
            message=message,
            error_code="CODE_ANALYSIS_ERROR",
            details=error_details,
        )


class VoiceProcessingError(AILearningAssistantError):
    """Error during voice processing."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize voice processing error.

        Args:
            message: Error message
            operation: Operation that failed (transcribe, synthesize)
            details: Additional error details
        """
        error_details = details or {}
        if operation:
            error_details["operation"] = operation

        super().__init__(
            message=message,
            error_code="VOICE_PROCESSING_ERROR",
            details=error_details,
        )


class LanguageDetectionError(AILearningAssistantError):
    """Error during language detection."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize language detection error.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="LANGUAGE_DETECTION_ERROR",
            details=details,
        )


class LanguageProcessingError(AILearningAssistantError):
    """Error during language-specific processing."""

    def __init__(
        self,
        message: str,
        language_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize language processing error.

        Args:
            message: Error message
            language_code: Language code being processed
            details: Additional error details
        """
        error_details = details or {}
        if language_code:
            error_details["language_code"] = language_code

        super().__init__(
            message=message,
            error_code="LANGUAGE_PROCESSING_ERROR",
            details=error_details,
        )


class ServiceCommunicationError(AILearningAssistantError):
    """Error during service-to-service communication."""

    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize service communication error.

        Args:
            message: Error message
            service: Service that failed
            details: Additional error details
        """
        error_details = details or {}
        if service:
            error_details["service"] = service

        super().__init__(
            message=message,
            error_code="SERVICE_COMMUNICATION_ERROR",
            details=error_details,
        )
