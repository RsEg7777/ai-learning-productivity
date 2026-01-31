"""Unit tests for content upload service."""

import pytest
from io import BytesIO
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.services.content_processing import ContentUploadService
from src.shared.models.content import ContentType, Content
from src.shared.utils.errors import (
    ValidationError,
    UnsupportedFormatError,
    ContentProcessingError,
)


class TestContentUploadService:
    """Test suite for ContentUploadService."""

    @pytest.fixture
    def mock_s3_client(self):
        """Create mock S3 client."""
        mock_client = Mock()
        mock_client.upload_file = Mock(return_value="s3://test-bucket/uploads/user123/2024/01/content-id.pdf")
        mock_client.download_file = Mock()
        mock_client.get_presigned_url = Mock(return_value="https://presigned-url.com")
        mock_client.delete_file = Mock()
        mock_client.file_exists = Mock(return_value=True)
        return mock_client

    @pytest.fixture
    def upload_service(self, mock_s3_client):
        """Create ContentUploadService instance."""
        return ContentUploadService(s3_client=mock_s3_client)

    @pytest.fixture
    def sample_file(self):
        """Create sample file object."""
        content = b"Sample PDF content for testing"
        return BytesIO(content)

    def test_upload_content_success_pdf(self, upload_service, mock_s3_client, sample_file):
        """Test successful PDF upload."""
        # Arrange
        user_id = "user123"
        filename = "document.pdf"
        title = "Test Document"
        language = "en"

        # Act
        content = upload_service.upload_content(
            user_id=user_id,
            file_obj=sample_file,
            filename=filename,
            title=title,
            language=language,
        )

        # Assert
        assert content.user_id == user_id
        assert content.title == title
        assert content.type == ContentType.PDF
        assert content.language == language
        assert content.s3_location.startswith("s3://")
        assert content.metadata.file_size > 0
        assert content.metadata.mime_type == "application/pdf"

        # Verify S3 upload was called
        mock_s3_client.upload_file.assert_called_once()

    def test_upload_content_success_video(self, upload_service, mock_s3_client):
        """Test successful video upload."""
        # Arrange
        user_id = "user456"
        filename = "lecture.mp4"
        video_content = b"Fake video content" * 1000
        file_obj = BytesIO(video_content)

        # Act
        content = upload_service.upload_content(
            user_id=user_id,
            file_obj=file_obj,
            filename=filename,
        )

        # Assert
        assert content.type == ContentType.VIDEO
        assert content.title == filename
        assert content.metadata.mime_type == "video/mp4"

    def test_upload_content_success_audio(self, upload_service, mock_s3_client):
        """Test successful audio upload."""
        # Arrange
        user_id = "user789"
        filename = "recording.mp3"
        audio_content = b"Fake audio content" * 500
        file_obj = BytesIO(audio_content)

        # Act
        content = upload_service.upload_content(
            user_id=user_id,
            file_obj=file_obj,
            filename=filename,
        )

        # Assert
        assert content.type == ContentType.AUDIO
        assert content.metadata.mime_type == "audio/mpeg"

    def test_upload_content_success_text(self, upload_service, mock_s3_client):
        """Test successful text file upload."""
        # Arrange
        user_id = "user101"
        filename = "notes.txt"
        text_content = b"These are my study notes"
        file_obj = BytesIO(text_content)

        # Act
        content = upload_service.upload_content(
            user_id=user_id,
            file_obj=file_obj,
            filename=filename,
        )

        # Assert
        assert content.type == ContentType.TEXT
        assert content.metadata.mime_type == "text/plain"

    def test_upload_content_unsupported_format(self, upload_service, sample_file):
        """Test upload with unsupported file format."""
        # Arrange
        user_id = "user123"
        filename = "document.xyz"  # Unsupported format

        # Act & Assert
        with pytest.raises(UnsupportedFormatError) as exc_info:
            upload_service.upload_content(
                user_id=user_id,
                file_obj=sample_file,
                filename=filename,
            )

        assert ".xyz" in str(exc_info.value)
        assert "Supported formats" in str(exc_info.value)

    def test_upload_content_no_extension(self, upload_service, sample_file):
        """Test upload with filename without extension."""
        # Arrange
        user_id = "user123"
        filename = "document"  # No extension

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            upload_service.upload_content(
                user_id=user_id,
                file_obj=sample_file,
                filename=filename,
            )

        assert "extension" in str(exc_info.value).lower()

    def test_upload_content_invalid_language(self, upload_service, sample_file):
        """Test upload with invalid language code."""
        # Arrange
        user_id = "user123"
        filename = "document.pdf"
        language = "invalid-lang"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            upload_service.upload_content(
                user_id=user_id,
                file_obj=sample_file,
                filename=filename,
                language=language,
            )

        assert "language" in str(exc_info.value).lower()

    def test_upload_content_file_too_large(self, upload_service, mock_s3_client):
        """Test upload with file exceeding size limit."""
        # Arrange
        user_id = "user123"
        filename = "large.txt"
        # Create file larger than 10MB limit for text files
        large_content = b"x" * (11 * 1024 * 1024)
        file_obj = BytesIO(large_content)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            upload_service.upload_content(
                user_id=user_id,
                file_obj=file_obj,
                filename=filename,
            )

        assert "size" in str(exc_info.value).lower()
        assert "exceeds" in str(exc_info.value).lower()

    def test_upload_content_with_metadata(self, upload_service, mock_s3_client, sample_file):
        """Test upload with custom metadata."""
        # Arrange
        user_id = "user123"
        filename = "document.pdf"
        metadata = {
            "page_count": 10,
            "word_count": 5000,
        }

        # Act
        content = upload_service.upload_content(
            user_id=user_id,
            file_obj=sample_file,
            filename=filename,
            metadata=metadata,
        )

        # Assert
        assert content.metadata.page_count == 10
        assert content.metadata.word_count == 5000

    def test_upload_content_s3_error(self, upload_service, mock_s3_client, sample_file):
        """Test upload when S3 upload fails."""
        # Arrange
        user_id = "user123"
        filename = "document.pdf"
        mock_s3_client.upload_file.side_effect = Exception("S3 upload failed")

        # Act & Assert
        with pytest.raises(ContentProcessingError) as exc_info:
            upload_service.upload_content(
                user_id=user_id,
                file_obj=sample_file,
                filename=filename,
            )

        assert "Failed to upload content" in str(exc_info.value)

    def test_download_content_success(self, upload_service, mock_s3_client):
        """Test successful content download."""
        # Arrange
        content = Content(
            id="content123",
            user_id="user123",
            title="Test",
            type=ContentType.PDF,
            original_text="",
            s3_location="s3://test-bucket/uploads/user123/2024/01/content123.pdf",
        )
        file_obj = BytesIO()

        # Act
        upload_service.download_content(content, file_obj)

        # Assert
        mock_s3_client.download_file.assert_called_once()

    def test_download_content_no_s3_location(self, upload_service):
        """Test download when content has no S3 location."""
        # Arrange
        content = Content(
            id="content123",
            user_id="user123",
            title="Test",
            type=ContentType.PDF,
            original_text="",
            s3_location=None,
        )
        file_obj = BytesIO()

        # Act & Assert
        with pytest.raises(ContentProcessingError) as exc_info:
            upload_service.download_content(content, file_obj)

        assert "no S3 location" in str(exc_info.value)

    def test_get_presigned_url_success(self, upload_service, mock_s3_client):
        """Test successful presigned URL generation."""
        # Arrange
        content = Content(
            id="content123",
            user_id="user123",
            title="Test",
            type=ContentType.PDF,
            original_text="",
            s3_location="s3://test-bucket/uploads/user123/2024/01/content123.pdf",
        )

        # Act
        url = upload_service.get_presigned_url(content, expiration=7200)

        # Assert
        assert url == "https://presigned-url.com"
        mock_s3_client.get_presigned_url.assert_called_once()

    def test_get_presigned_url_no_s3_location(self, upload_service):
        """Test presigned URL generation when content has no S3 location."""
        # Arrange
        content = Content(
            id="content123",
            user_id="user123",
            title="Test",
            type=ContentType.PDF,
            original_text="",
            s3_location=None,
        )

        # Act & Assert
        with pytest.raises(ContentProcessingError) as exc_info:
            upload_service.get_presigned_url(content)

        assert "no S3 location" in str(exc_info.value)

    def test_delete_content_success(self, upload_service, mock_s3_client):
        """Test successful content deletion."""
        # Arrange
        content = Content(
            id="content123",
            user_id="user123",
            title="Test",
            type=ContentType.PDF,
            original_text="",
            s3_location="s3://test-bucket/uploads/user123/2024/01/content123.pdf",
        )

        # Act
        upload_service.delete_content(content)

        # Assert
        mock_s3_client.delete_file.assert_called_once()

    def test_delete_content_no_s3_location(self, upload_service, mock_s3_client):
        """Test deletion when content has no S3 location."""
        # Arrange
        content = Content(
            id="content123",
            user_id="user123",
            title="Test",
            type=ContentType.PDF,
            original_text="",
            s3_location=None,
        )

        # Act
        upload_service.delete_content(content)

        # Assert - should not raise error, just skip deletion
        mock_s3_client.delete_file.assert_not_called()

    def test_content_exists_true(self, upload_service, mock_s3_client):
        """Test content existence check when content exists."""
        # Arrange
        content = Content(
            id="content123",
            user_id="user123",
            title="Test",
            type=ContentType.PDF,
            original_text="",
            s3_location="s3://test-bucket/uploads/user123/2024/01/content123.pdf",
        )
        mock_s3_client.file_exists.return_value = True

        # Act
        exists = upload_service.content_exists(content)

        # Assert
        assert exists is True

    def test_content_exists_false(self, upload_service, mock_s3_client):
        """Test content existence check when content doesn't exist."""
        # Arrange
        content = Content(
            id="content123",
            user_id="user123",
            title="Test",
            type=ContentType.PDF,
            original_text="",
            s3_location="s3://test-bucket/uploads/user123/2024/01/content123.pdf",
        )
        mock_s3_client.file_exists.return_value = False

        # Act
        exists = upload_service.content_exists(content)

        # Assert
        assert exists is False

    def test_content_exists_no_s3_location(self, upload_service):
        """Test content existence check when content has no S3 location."""
        # Arrange
        content = Content(
            id="content123",
            user_id="user123",
            title="Test",
            type=ContentType.PDF,
            original_text="",
            s3_location=None,
        )

        # Act
        exists = upload_service.content_exists(content)

        # Assert
        assert exists is False

    def test_generate_s3_key_format(self, upload_service):
        """Test S3 key generation format."""
        # Arrange
        user_id = "user123"
        content_id = "content456"
        extension = ".pdf"

        # Act
        s3_key = upload_service._generate_s3_key(user_id, content_id, extension)

        # Assert
        assert s3_key.startswith(f"uploads/{user_id}/")
        assert s3_key.endswith(f"/{content_id}{extension}")
        # Should contain year and month
        assert len(s3_key.split("/")) == 5  # uploads/user/year/month/file

    def test_extract_s3_key_valid(self, upload_service):
        """Test S3 key extraction from valid URI."""
        # Arrange
        s3_uri = "s3://test-bucket/uploads/user123/2024/01/content123.pdf"

        # Act
        s3_key = upload_service._extract_s3_key(s3_uri)

        # Assert
        assert s3_key == "uploads/user123/2024/01/content123.pdf"

    def test_extract_s3_key_invalid_format(self, upload_service):
        """Test S3 key extraction from invalid URI."""
        # Arrange
        invalid_uri = "https://example.com/file.pdf"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            upload_service._extract_s3_key(invalid_uri)

        assert "Invalid S3 URI" in str(exc_info.value)

    def test_get_file_extension_valid(self, upload_service):
        """Test file extension extraction."""
        # Arrange
        filename = "document.PDF"

        # Act
        extension = upload_service._get_file_extension(filename)

        # Assert
        assert extension == ".pdf"  # Should be lowercase

    def test_get_file_extension_no_extension(self, upload_service):
        """Test file extension extraction when no extension."""
        # Arrange
        filename = "document"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            upload_service._get_file_extension(filename)

        assert "extension" in str(exc_info.value).lower()

    def test_get_file_size(self, upload_service):
        """Test file size calculation."""
        # Arrange
        content = b"Test content"
        file_obj = BytesIO(content)

        # Act
        size = upload_service._get_file_size(file_obj)

        # Assert
        assert size == len(content)
        # Verify file pointer is restored
        assert file_obj.tell() == 0

    def test_upload_content_indian_language(self, upload_service, mock_s3_client, sample_file):
        """Test upload with Indian language."""
        # Arrange
        user_id = "user123"
        filename = "document.pdf"
        language = "hi"  # Hindi

        # Act
        content = upload_service.upload_content(
            user_id=user_id,
            file_obj=sample_file,
            filename=filename,
            language=language,
        )

        # Assert
        assert content.language == "hi"

    def test_upload_content_multiple_file_types(self, upload_service, mock_s3_client):
        """Test uploading different file types."""
        user_id = "user123"

        test_cases = [
            ("doc.txt", ContentType.TEXT),
            ("doc.pdf", ContentType.PDF),
            ("video.mp4", ContentType.VIDEO),
            ("audio.mp3", ContentType.AUDIO),
            ("code.py", ContentType.CODE),
        ]

        for filename, expected_type in test_cases:
            # Arrange
            file_obj = BytesIO(b"test content")

            # Act
            content = upload_service.upload_content(
                user_id=user_id,
                file_obj=file_obj,
                filename=filename,
            )

            # Assert
            assert content.type == expected_type, f"Failed for {filename}"
