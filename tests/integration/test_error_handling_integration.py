"""Integration tests for error handling across content processing."""

import pytest
from io import BytesIO
from unittest.mock import Mock

from src.services.content_processing import ContentUploadService
from src.shared.utils.errors import (
    UnsupportedFormatError,
    ValidationError,
    ContentProcessingError,
)


class TestErrorHandlingIntegration:
    """Integration tests for comprehensive error handling."""

    @pytest.fixture
    def mock_s3_client(self):
        """Create mock S3 client."""
        mock_client = Mock()
        mock_client.upload_file = Mock(
            return_value="s3://test-bucket/uploads/user123/2024/01/content-id.pdf"
        )
        return mock_client

    @pytest.fixture
    def upload_service(self, mock_s3_client):
        """Create ContentUploadService instance."""
        return ContentUploadService(s3_client=mock_s3_client)

    def test_unsupported_format_provides_helpful_suggestions(self, upload_service):
        """Test that unsupported format errors provide helpful suggestions."""
        # Arrange
        user_id = "user123"
        file_obj = BytesIO(b"test content")
        
        # Test with MPEG format (should suggest MP4/MP3)
        with pytest.raises(UnsupportedFormatError) as exc_info:
            upload_service.upload_content(
                user_id=user_id,
                file_obj=file_obj,
                filename="video.mpeg",
            )
        
        error = exc_info.value
        error_message = str(error)
        
        # Verify error message structure
        assert "Unsupported file format" in error_message
        assert ".mpeg" in error_message
        assert "Supported formats:" in error_message
        
        # Verify suggestions are provided
        assert error.details["suggestions"] is not None
        assert len(error.details["suggestions"]) > 0
        
        # Verify error can be serialized for API responses
        error_dict = error.to_dict()
        assert error_dict["error"] == "UNSUPPORTED_FORMAT"
        assert "suggestions" in error_dict["details"]

    def test_unsupported_format_categorizes_formats(self, upload_service):
        """Test that error message categorizes supported formats."""
        # Arrange
        user_id = "user123"
        file_obj = BytesIO(b"test content")
        
        with pytest.raises(UnsupportedFormatError) as exc_info:
            upload_service.upload_content(
                user_id=user_id,
                file_obj=file_obj,
                filename="document.xyz",
            )
        
        error_message = str(exc_info.value)
        
        # Verify categories are present
        assert "Text:" in error_message or "PDF:" in error_message
        assert "Video:" in error_message or "Audio:" in error_message

    def test_no_extension_provides_clear_guidance(self, upload_service):
        """Test that missing extension error provides clear guidance."""
        # Arrange
        user_id = "user123"
        file_obj = BytesIO(b"test content")
        
        with pytest.raises(ValidationError) as exc_info:
            upload_service.upload_content(
                user_id=user_id,
                file_obj=file_obj,
                filename="document",  # No extension
            )
        
        error = exc_info.value
        error_message = str(error)
        
        # Verify error provides guidance
        assert "extension" in error_message.lower()
        assert error.details.get("suggestion") is not None

    def test_oversized_file_provides_size_information(self, upload_service):
        """Test that oversized file error provides size information."""
        # Arrange
        user_id = "user123"
        # Create file larger than 10MB limit for text files
        large_content = b"x" * (11 * 1024 * 1024)
        file_obj = BytesIO(large_content)
        
        with pytest.raises(ValidationError) as exc_info:
            upload_service.upload_content(
                user_id=user_id,
                file_obj=file_obj,
                filename="large.txt",
            )
        
        error = exc_info.value
        error_message = str(error)
        
        # Verify error provides size information
        assert "size" in error_message.lower()
        assert "exceeds" in error_message.lower()
        assert "MB" in error_message
        
        # Verify details contain size information
        assert "file_size" in error.details
        assert "max_size" in error.details

    def test_multiple_validation_errors_handled_sequentially(self, upload_service):
        """Test that multiple validation issues are caught appropriately."""
        user_id = "user123"
        
        # Test 1: No extension
        with pytest.raises(ValidationError):
            upload_service.upload_content(
                user_id=user_id,
                file_obj=BytesIO(b"content"),
                filename="noextension",
            )
        
        # Test 2: Unsupported format
        with pytest.raises(UnsupportedFormatError):
            upload_service.upload_content(
                user_id=user_id,
                file_obj=BytesIO(b"content"),
                filename="file.xyz",
            )
        
        # Test 3: Invalid language
        with pytest.raises(ValidationError):
            upload_service.upload_content(
                user_id=user_id,
                file_obj=BytesIO(b"content"),
                filename="file.txt",
                language="invalid-lang",
            )

    def test_error_serialization_for_api_responses(self, upload_service):
        """Test that errors can be properly serialized for API responses."""
        # Arrange
        user_id = "user123"
        file_obj = BytesIO(b"test content")
        
        with pytest.raises(UnsupportedFormatError) as exc_info:
            upload_service.upload_content(
                user_id=user_id,
                file_obj=file_obj,
                filename="file.unknown",
            )
        
        error = exc_info.value
        error_dict = error.to_dict()
        
        # Verify dictionary structure is suitable for API responses
        assert isinstance(error_dict, dict)
        assert "error" in error_dict
        assert "message" in error_dict
        assert "details" in error_dict
        
        # Verify all details are JSON-serializable
        import json
        json_str = json.dumps(error_dict)
        assert json_str is not None

    def test_successful_upload_after_fixing_format(self, upload_service, mock_s3_client):
        """Test that upload succeeds after fixing format error."""
        user_id = "user123"
        content = b"test content"
        
        # First attempt with wrong format
        with pytest.raises(UnsupportedFormatError):
            upload_service.upload_content(
                user_id=user_id,
                file_obj=BytesIO(content),
                filename="document.xyz",
            )
        
        # Second attempt with correct format
        result = upload_service.upload_content(
            user_id=user_id,
            file_obj=BytesIO(content),
            filename="document.pdf",
        )
        
        # Verify success
        assert result is not None
        assert result.user_id == user_id
        assert result.type.value == "pdf"

    def test_format_suggestions_for_common_mistakes(self, upload_service):
        """Test format suggestions for common file format mistakes."""
        user_id = "user123"
        
        test_cases = [
            (".mpeg", [".mp4", ".mp3"]),  # Should suggest video/audio
            (".wave", [".wav"]),  # Should suggest wav
            (".doc", [".txt", ".pdf"]),  # Should suggest text/pdf
        ]
        
        for wrong_format, expected_suggestions in test_cases:
            with pytest.raises(UnsupportedFormatError) as exc_info:
                upload_service.upload_content(
                    user_id=user_id,
                    file_obj=BytesIO(b"content"),
                    filename=f"file{wrong_format}",
                )
            
            error = exc_info.value
            suggestions = error.details["suggestions"]
            
            # Verify at least one expected suggestion is present
            assert any(
                exp in suggestions for exp in expected_suggestions
            ), f"Expected one of {expected_suggestions} in {suggestions}"

    def test_comprehensive_validation_success(self, upload_service, mock_s3_client):
        """Test that comprehensive validation passes for valid files."""
        user_id = "user123"
        
        # Test various valid file types
        valid_files = [
            ("document.pdf", b"PDF content"),
            ("notes.txt", b"Text content"),
            ("video.mp4", b"Video content"),
            ("audio.mp3", b"Audio content"),
            ("script.py", b"Code content"),
        ]
        
        for filename, content in valid_files:
            result = upload_service.upload_content(
                user_id=user_id,
                file_obj=BytesIO(content),
                filename=filename,
            )
            
            assert result is not None
            assert result.user_id == user_id
            assert result.s3_location is not None

    def test_error_details_contain_actionable_information(self, upload_service):
        """Test that error details contain actionable information for users."""
        user_id = "user123"
        
        # Test unsupported format
        with pytest.raises(UnsupportedFormatError) as exc_info:
            upload_service.upload_content(
                user_id=user_id,
                file_obj=BytesIO(b"content"),
                filename="file.xyz",
            )
        
        error = exc_info.value
        
        # Verify actionable information is present
        assert "format_provided" in error.details
        assert "supported_formats" in error.details
        assert "suggestions" in error.details
        
        # Verify the information is useful
        assert error.details["format_provided"] == ".xyz"
        assert len(error.details["supported_formats"]) > 0
        assert len(error.details["suggestions"]) > 0
