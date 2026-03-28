"""Content upload and storage service."""

import logging
import uuid
from datetime import datetime
from io import BytesIO
from typing import BinaryIO, Optional, Dict, Any, Tuple
import mimetypes

from ...shared.aws_clients.s3_client import S3Client
from ...shared.models.content import (
    Content,
    ContentType,
    ContentMetadata,
)
from ...shared.utils.validators import (
    validate_content_type,
    validate_file_size,
    validate_language_code,
    validate_file_format_comprehensive,
)
from ...shared.utils.errors import (
    ValidationError,
    UnsupportedFormatError,
    ContentProcessingError,
)

logger = logging.getLogger(__name__)


class ContentUploadService:
    """Service for handling content uploads and storage."""

    def __init__(self, s3_client: S3Client) -> None:
        """
        Initialize content upload service.

        Args:
            s3_client: S3 client for file storage
        """
        self.s3_client = s3_client
        logger.info("Initialized ContentUploadService")

    def upload_content(
        self,
        user_id: str,
        file_obj: BinaryIO,
        filename: str,
        title: Optional[str] = None,
        language: str = "en",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Content:
        """
        Upload content file with validation and encryption.

        This method:
        1. Validates file format and size
        2. Generates unique content ID and S3 key
        3. Uploads file to S3 with AES-256 encryption
        4. Creates and returns Content object with metadata

        Args:
            user_id: ID of the user uploading content
            file_obj: File object to upload
            filename: Original filename
            title: Content title (defaults to filename)
            language: Content language code (default: "en")
            metadata: Additional metadata

        Returns:
            Content object with upload details

        Raises:
            ValidationError: If validation fails
            UnsupportedFormatError: If file format is not supported
            ContentProcessingError: If upload fails
        """
        try:
            # Validate language code
            language = validate_language_code(language)

            # Get file size first for comprehensive validation
            file_size = self._get_file_size(file_obj)

            # Perform comprehensive format validation
            content_type, validation_info = validate_file_format_comprehensive(
                filename=filename,
                file_size=file_size,
                mime_type=None,  # Will be determined later
            )

            logger.info(
                f"File validation passed: {filename} -> {content_type.value}, "
                f"size: {file_size} bytes"
            )

            # Generate unique content ID and S3 key
            file_extension = validation_info["extension"]
            content_id = str(uuid.uuid4())
            s3_key = self._generate_s3_key(user_id, content_id, file_extension)

            # Determine MIME type
            mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

            # Prepare metadata for S3
            s3_metadata = {
                "user_id": user_id,
                "content_id": content_id,
                "original_filename": filename,
                "content_type": content_type.value,
                "language": language,
            }

            # Upload to S3 with AES-256 encryption (handled by S3Client)
            logger.info(
                f"Uploading content {content_id} for user {user_id}, "
                f"type: {content_type.value}, size: {file_size} bytes"
            )

            # Reset file pointer to beginning
            file_obj.seek(0)

            s3_uri = self.s3_client.upload_file(
                file_obj=file_obj,
                key=s3_key,
                content_type=mime_type,
                metadata=s3_metadata,
            )

            # Create content metadata
            content_metadata = ContentMetadata(
                file_size=file_size,
                mime_type=mime_type,
                language_detected=language,
            )

            # Add custom metadata if provided
            if metadata:
                if "duration" in metadata:
                    content_metadata.duration = metadata["duration"]
                if "page_count" in metadata:
                    content_metadata.page_count = metadata["page_count"]
                if "word_count" in metadata:
                    content_metadata.word_count = metadata["word_count"]

            # Create Content object
            content = Content(
                id=content_id,
                user_id=user_id,
                title=title or filename,
                type=content_type,
                original_text="",  # Will be populated during processing
                language=language,
                uploaded_at=datetime.utcnow(),
                s3_location=s3_uri,
                metadata=content_metadata,
            )

            logger.info(
                f"Successfully uploaded content {content_id} to {s3_uri}"
            )

            return content

        except (ValidationError, UnsupportedFormatError) as e:
            logger.error(f"Validation error during upload: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during content upload: {e}")
            raise ContentProcessingError(
                message=f"Failed to upload content: {str(e)}",
                content_type=content_type.value if 'content_type' in locals() else None,
            )

    def download_content(
        self,
        content: Content,
        file_obj: BinaryIO,
    ) -> None:
        """
        Download content from S3.

        Args:
            content: Content object with S3 location
            file_obj: File object to write downloaded content

        Raises:
            ContentProcessingError: If download fails
        """
        try:
            if not content.s3_location:
                raise ContentProcessingError(
                    message="Content has no S3 location",
                    content_type=content.type.value,
                )

            # Extract S3 key from URI
            s3_key = self._extract_s3_key(content.s3_location)

            logger.info(f"Downloading content {content.id} from {content.s3_location}")

            self.s3_client.download_file(s3_key, file_obj)

            logger.info(f"Successfully downloaded content {content.id}")

        except Exception as e:
            logger.error(f"Error downloading content {content.id}: {e}")
            raise ContentProcessingError(
                message=f"Failed to download content: {str(e)}",
                content_type=content.type.value,
            )

    def get_presigned_url(
        self,
        content: Content,
        expiration: int = 3600,
    ) -> str:
        """
        Generate presigned URL for temporary content access.

        Args:
            content: Content object
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL for content access

        Raises:
            ContentProcessingError: If URL generation fails
        """
        try:
            if not content.s3_location:
                raise ContentProcessingError(
                    message="Content has no S3 location",
                    content_type=content.type.value,
                )

            s3_key = self._extract_s3_key(content.s3_location)

            logger.info(
                f"Generating presigned URL for content {content.id}, "
                f"expiration: {expiration}s"
            )

            url = self.s3_client.get_presigned_url(s3_key, expiration)

            return url

        except Exception as e:
            logger.error(f"Error generating presigned URL for content {content.id}: {e}")
            raise ContentProcessingError(
                message=f"Failed to generate presigned URL: {str(e)}",
                content_type=content.type.value,
            )

    def delete_content(self, content: Content) -> None:
        """
        Delete content from S3.

        Args:
            content: Content object to delete

        Raises:
            ContentProcessingError: If deletion fails
        """
        try:
            if not content.s3_location:
                logger.warning(f"Content {content.id} has no S3 location, skipping deletion")
                return

            s3_key = self._extract_s3_key(content.s3_location)

            logger.info(f"Deleting content {content.id} from {content.s3_location}")

            self.s3_client.delete_file(s3_key)

            logger.info(f"Successfully deleted content {content.id}")

        except Exception as e:
            logger.error(f"Error deleting content {content.id}: {e}")
            raise ContentProcessingError(
                message=f"Failed to delete content: {str(e)}",
                content_type=content.type.value,
            )

    def content_exists(self, content: Content) -> bool:
        """
        Check if content exists in S3.

        Args:
            content: Content object to check

        Returns:
            True if content exists, False otherwise
        """
        try:
            if not content.s3_location:
                return False

            s3_key = self._extract_s3_key(content.s3_location)
            return self.s3_client.file_exists(s3_key)

        except Exception as e:
            logger.error(f"Error checking content existence for {content.id}: {e}")
            return False

    def _get_file_extension(self, filename: str) -> str:
        """
        Extract file extension from filename.

        Args:
            filename: Filename with extension

        Returns:
            File extension (e.g., '.pdf')

        Raises:
            ValidationError: If filename has no extension
        """
        if "." not in filename:
            raise ValidationError(
                message="Filename must have an extension",
                field="filename",
            )

        extension = "." + filename.rsplit(".", 1)[1].lower()
        return extension

    def _get_file_size(self, file_obj: BinaryIO) -> int:
        """
        Get file size in bytes.

        Args:
            file_obj: File object

        Returns:
            File size in bytes
        """
        # Save current position
        current_pos = file_obj.tell()

        # Seek to end to get size
        file_obj.seek(0, 2)
        file_size = file_obj.tell()

        # Restore original position
        file_obj.seek(current_pos)

        return file_size

    def _generate_s3_key(self, user_id: str, content_id: str, extension: str) -> str:
        """
        Generate S3 key for content storage.

        Format: uploads/{user_id}/{year}/{month}/{content_id}{extension}

        Args:
            user_id: User ID
            content_id: Content ID
            extension: File extension

        Returns:
            S3 key
        """
        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")

        s3_key = f"uploads/{user_id}/{year}/{month}/{content_id}{extension}"
        return s3_key

    def _extract_s3_key(self, s3_uri: str) -> str:
        """
        Extract S3 key from S3 URI.

        Args:
            s3_uri: S3 URI (e.g., 's3://bucket/key')

        Returns:
            S3 key

        Raises:
            ValidationError: If URI format is invalid
        """
        if not s3_uri.startswith("s3://"):
            raise ValidationError(
                message="Invalid S3 URI format",
                field="s3_location",
                details={"s3_uri": s3_uri},
            )

        # Remove 's3://bucket/' prefix to get key
        parts = s3_uri.replace("s3://", "").split("/", 1)
        if len(parts) < 2:
            raise ValidationError(
                message="Invalid S3 URI format",
                field="s3_location",
                details={"s3_uri": s3_uri},
            )

        return parts[1]
