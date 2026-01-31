"""Unit tests for error handling and graceful degradation."""

import pytest
from io import BytesIO

from src.shared.utils.errors import (
    UnsupportedFormatError,
    ContentProcessingError,
    PartialProcessingError,
)
from src.shared.utils.validators import (
    validate_content_type,
    validate_file_format_comprehensive,
    _suggest_similar_formats,
)
from src.shared.utils.graceful_degradation import (
    with_fallback,
    try_with_degradation,
    partial_success_handler,
    create_minimal_result,
    validate_processing_result,
)
from src.shared.models.content import ContentType


class TestUnsupportedFormatError:
    """Test enhanced unsupported format error handling."""

    def test_unsupported_format_error_message_structure(self):
        """Test that error message includes categorized formats."""
        with pytest.raises(UnsupportedFormatError) as exc_info:
            validate_content_type(".xyz")
        
        error = exc_info.value
        error_message = str(error)
        
        # Check that error message contains key information
        assert ".xyz" in error_message
        assert "Unsupported file format" in error_message
        assert "Supported formats:" in error_message
        
        # Check that categories are present
        assert "Text:" in error_message or "PDF:" in error_message

    def test_unsupported_format_error_with_suggestions(self):
        """Test that error includes format suggestions."""
        with pytest.raises(UnsupportedFormatError) as exc_info:
            validate_content_type(".mpeg")
        
        error = exc_info.value
        
        # Check that suggestions are provided
        assert error.details["suggestions"] is not None
        assert len(error.details["suggestions"]) > 0

    def test_unsupported_format_error_details(self):
        """Test that error details contain all necessary information."""
        with pytest.raises(UnsupportedFormatError) as exc_info:
            validate_content_type(".unknown")
        
        error = exc_info.value
        
        # Check error details
        assert error.details["format_provided"] == ".unknown"
        assert isinstance(error.details["supported_formats"], list)
        assert len(error.details["supported_formats"]) > 0
        assert isinstance(error.details["suggestions"], list)

    def test_unsupported_format_error_to_dict(self):
        """Test error serialization to dictionary."""
        with pytest.raises(UnsupportedFormatError) as exc_info:
            validate_content_type(".xyz")
        
        error = exc_info.value
        error_dict = error.to_dict()
        
        # Check dictionary structure
        assert "error" in error_dict
        assert "message" in error_dict
        assert "details" in error_dict
        assert error_dict["error"] == "UNSUPPORTED_FORMAT"


class TestFormatSuggestions:
    """Test format suggestion logic."""

    def test_suggest_similar_formats_direct_mapping(self):
        """Test suggestions for formats with direct mappings."""
        supported = [".mp4", ".mp3", ".avi", ".txt", ".pdf"]
        
        # Test MPEG mapping
        suggestions = _suggest_similar_formats(".mpeg", supported)
        assert ".mp4" in suggestions or ".mp3" in suggestions
        
        # Test wave mapping
        suggestions = _suggest_similar_formats(".wave", supported)
        # Should suggest audio formats even if .wav not in supported list

    def test_suggest_similar_formats_by_first_letter(self):
        """Test suggestions based on first letter similarity."""
        supported = [".mp4", ".mov", ".mkv", ".txt", ".pdf"]
        
        suggestions = _suggest_similar_formats(".mxf", supported)
        
        # Should suggest formats starting with 'm'
        assert any(s.startswith(".m") for s in suggestions)

    def test_suggest_similar_formats_common_fallback(self):
        """Test fallback to common formats when no similarity found."""
        supported = [".pdf", ".txt", ".mp4", ".mp3", ".jpg"]
        
        suggestions = _suggest_similar_formats(".xyz", supported)
        
        # Should suggest common formats
        assert len(suggestions) > 0
        assert any(fmt in [".pdf", ".txt", ".mp4", ".mp3"] for fmt in suggestions)

    def test_suggest_similar_formats_limit(self):
        """Test that suggestions are limited to 3."""
        supported = [".mp4", ".mp3", ".avi", ".mov", ".mkv", ".txt", ".pdf"]
        
        suggestions = _suggest_similar_formats(".mpeg", supported)
        
        assert len(suggestions) <= 3


class TestComprehensiveValidation:
    """Test comprehensive file format validation."""

    def test_validate_file_format_comprehensive_success(self):
        """Test successful comprehensive validation."""
        content_type, info = validate_file_format_comprehensive(
            filename="document.pdf",
            file_size=1024 * 1024,  # 1 MB
        )
        
        assert content_type == ContentType.PDF
        assert info["extension"] == ".pdf"
        assert info["content_type"] == "pdf"
        assert info["file_size_valid"] is True
        assert info["file_size"] == 1024 * 1024

    def test_validate_file_format_comprehensive_no_extension(self):
        """Test validation with filename without extension."""
        with pytest.raises(Exception) as exc_info:
            validate_file_format_comprehensive(filename="document")
        
        assert "extension" in str(exc_info.value).lower()

    def test_validate_file_format_comprehensive_unsupported(self):
        """Test validation with unsupported format."""
        with pytest.raises(UnsupportedFormatError):
            validate_file_format_comprehensive(filename="file.xyz")

    def test_validate_file_format_comprehensive_oversized(self):
        """Test validation with oversized file."""
        with pytest.raises(Exception) as exc_info:
            validate_file_format_comprehensive(
                filename="large.txt",
                file_size=20 * 1024 * 1024,  # 20 MB (exceeds 10 MB limit)
            )
        
        assert "size" in str(exc_info.value).lower()

    def test_validate_file_format_comprehensive_with_mime_type(self):
        """Test validation with MIME type checking."""
        content_type, info = validate_file_format_comprehensive(
            filename="document.pdf",
            file_size=1024,
            mime_type="application/pdf",
        )
        
        assert info["mime_type"] == "application/pdf"
        assert info["mime_type_valid"] is True

    def test_validate_file_format_comprehensive_mime_mismatch(self):
        """Test validation with mismatched MIME type."""
        content_type, info = validate_file_format_comprehensive(
            filename="document.pdf",
            file_size=1024,
            mime_type="text/plain",  # Wrong MIME type
        )
        
        # Should still succeed but flag MIME type mismatch
        assert content_type == ContentType.PDF
        assert info["mime_type_valid"] is False


class TestGracefulDegradation:
    """Test graceful degradation utilities."""

    def test_with_fallback_decorator_success(self):
        """Test fallback decorator when function succeeds."""
        @with_fallback(fallback_value="fallback")
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"

    def test_with_fallback_decorator_failure(self):
        """Test fallback decorator when function fails."""
        @with_fallback(fallback_value="fallback")
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        assert result == "fallback"

    def test_with_fallback_decorator_with_function(self):
        """Test fallback decorator with fallback function."""
        def fallback_fn():
            return "fallback_result"
        
        @with_fallback(fallback_fn=fallback_fn)
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        assert result == "fallback_result"

    def test_with_fallback_decorator_specific_errors(self):
        """Test fallback decorator with specific error types."""
        @with_fallback(fallback_value="fallback", error_types=(ValueError,))
        def function_with_type_error():
            raise TypeError("Wrong error type")
        
        # Should not catch TypeError, only ValueError
        with pytest.raises(TypeError):
            function_with_type_error()

    def test_try_with_degradation_primary_success(self):
        """Test degradation when primary function succeeds."""
        def primary():
            return "primary_result"
        
        def fallback():
            return "fallback_result"
        
        result = try_with_degradation(
            primary_fn=primary,
            fallback_fn=fallback,
            content_type="test",
        )
        
        assert result == "primary_result"

    def test_try_with_degradation_fallback_success(self):
        """Test degradation when primary fails but fallback succeeds."""
        def primary():
            raise ValueError("Primary failed")
        
        def fallback():
            return "fallback_result"
        
        result = try_with_degradation(
            primary_fn=primary,
            fallback_fn=fallback,
            content_type="test",
        )
        
        assert result == "fallback_result"

    def test_try_with_degradation_both_fail(self):
        """Test degradation when both primary and fallback fail."""
        def primary():
            raise ValueError("Primary failed")
        
        def fallback():
            raise ValueError("Fallback failed")
        
        with pytest.raises(ContentProcessingError) as exc_info:
            try_with_degradation(
                primary_fn=primary,
                fallback_fn=fallback,
                content_type="test",
            )
        
        error = exc_info.value
        assert "both primary and fallback methods failed" in str(error)

    def test_partial_success_handler_with_valid_result(self):
        """Test partial success handler with valid partial result."""
        partial_result = {
            "text": "Some text",
            "metadata": {"key": "value"},
        }
        
        result = partial_success_handler(
            operation_name="extraction",
            content_type="pdf",
            partial_result=partial_result,
            error=ValueError("Some fields missing"),
            required_fields=["text", "metadata"],
        )
        
        assert result["text"] == "Some text"
        assert "_warnings" in result
        assert len(result["_warnings"]) > 0

    def test_partial_success_handler_missing_required_fields(self):
        """Test partial success handler with missing required fields."""
        partial_result = {
            "text": "Some text",
            # Missing 'metadata' field
        }
        
        with pytest.raises(PartialProcessingError) as exc_info:
            partial_success_handler(
                operation_name="extraction",
                content_type="pdf",
                partial_result=partial_result,
                error=ValueError("Some fields missing"),
                required_fields=["text", "metadata"],
            )
        
        error = exc_info.value
        assert "missing required fields" in str(error)
        assert error.partial_result is not None

    def test_create_minimal_result(self):
        """Test creation of minimal result on complete failure."""
        content = "This is some test content for processing."
        error = ValueError("Processing failed")
        
        result = create_minimal_result(
            content_type="text",
            original_content=content,
            error=error,
            processing_time=1.5,
        )
        
        assert "summary" in result
        assert "key_points" in result
        assert "concepts" in result
        assert "metadata" in result
        assert result["metadata"]["processing_failed"] is True
        assert "_warnings" in result

    def test_create_minimal_result_long_content(self):
        """Test minimal result with long content (should truncate)."""
        content = "x" * 500  # Long content
        error = ValueError("Processing failed")
        
        result = create_minimal_result(
            content_type="text",
            original_content=content,
            error=error,
            processing_time=1.0,
        )
        
        # Summary should be truncated
        assert len(result["summary"]) < len(content)
        assert "..." in result["summary"]

    def test_validate_processing_result_valid(self):
        """Test validation of valid processing result."""
        result = {
            "summary": "Test summary",
            "key_points": ["point1", "point2"],
            "metadata": {"key": "value"},
        }
        
        is_valid = validate_processing_result(
            result=result,
            required_fields=["summary", "key_points"],
            content_type="test",
        )
        
        assert is_valid is True

    def test_validate_processing_result_missing_fields(self):
        """Test validation of result with missing fields."""
        result = {
            "summary": "Test summary",
            # Missing 'key_points'
        }
        
        is_valid = validate_processing_result(
            result=result,
            required_fields=["summary", "key_points"],
            content_type="test",
        )
        
        assert is_valid is False

    def test_validate_processing_result_invalid_type(self):
        """Test validation of result with invalid type."""
        result = "not a dict"
        
        with pytest.raises(ContentProcessingError) as exc_info:
            validate_processing_result(
                result=result,
                required_fields=["summary"],
                content_type="test",
            )
        
        assert "Invalid result type" in str(exc_info.value)


class TestPartialProcessingError:
    """Test PartialProcessingError functionality."""

    def test_partial_processing_error_creation(self):
        """Test creation of partial processing error."""
        partial_result = {"text": "Some text"}
        
        error = PartialProcessingError(
            message="Processing partially failed",
            content_type="pdf",
            partial_result=partial_result,
        )
        
        assert error.partial_result == partial_result
        assert error.error_code == "PARTIAL_PROCESSING"
        assert error.details["has_partial_result"] is True

    def test_partial_processing_error_no_result(self):
        """Test partial processing error without result."""
        error = PartialProcessingError(
            message="Processing failed",
            content_type="pdf",
            partial_result=None,
        )
        
        assert error.partial_result is None
        assert error.details["has_partial_result"] is False

    def test_partial_processing_error_to_dict(self):
        """Test serialization of partial processing error."""
        error = PartialProcessingError(
            message="Processing partially failed",
            content_type="pdf",
            partial_result={"text": "Some text"},
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error"] == "PARTIAL_PROCESSING"
        assert "message" in error_dict
        assert "details" in error_dict
