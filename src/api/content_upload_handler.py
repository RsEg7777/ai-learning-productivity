"""API handler for content upload with progress tracking."""

import json
import logging
import base64
from io import BytesIO
from typing import Dict, Any, Optional
import os

from ..services.content_processing import ContentUploadService
from ..shared.aws_clients.s3_client import S3Client
from ..shared.utils.errors import (
    ValidationError,
    UnsupportedFormatError,
    ContentProcessingError,
)
from ..shared.utils.response_formatter import (
    ResponseFormatter,
    ResponseSection,
)

logger = logging.getLogger(__name__)


class ContentUploadHandler:
    """Handler for content upload API endpoints."""

    def __init__(self, bucket_name: Optional[str] = None) -> None:
        """
        Initialize upload handler.

        Args:
            bucket_name: S3 bucket name (defaults to env variable)
        """
        self.bucket_name = bucket_name or os.environ.get(
            "CONTENT_BUCKET_NAME", "ai-learning-assistant-content"
        )
        self.s3_client = S3Client(bucket_name=self.bucket_name)
        self.upload_service = ContentUploadService(s3_client=self.s3_client)
        logger.info(f"Initialized ContentUploadHandler with bucket: {self.bucket_name}")

    def handle_upload(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle content upload request.

        Supports both multipart/form-data and base64-encoded file uploads.
        Implements drag-and-drop functionality through API Gateway.

        Expected event structure:
        {
            "body": base64-encoded file content or JSON with file data,
            "headers": {
                "content-type": "multipart/form-data" or "application/json"
            },
            "queryStringParameters": {
                "filename": "document.pdf",
                "title": "My Document",
                "language": "en"
            },
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-id"
                    }
                }
            }
        }

        Args:
            event: API Gateway event
            context: Lambda context

        Returns:
            API Gateway response with upload details
        """
        try:
            # Extract user ID from authorizer
            user_id = self._extract_user_id(event)

            # Extract upload parameters
            params = event.get("queryStringParameters") or {}
            filename = params.get("filename")
            title = params.get("title")
            language = params.get("language", "en")

            if not filename:
                return self._error_response(
                    400,
                    "MISSING_PARAMETER",
                    "filename parameter is required",
                )

            # Extract file content from request body
            file_content = self._extract_file_content(event)

            # Create file object
            file_obj = BytesIO(file_content)

            # Upload content
            logger.info(
                f"Processing upload request: user={user_id}, "
                f"filename={filename}, size={len(file_content)} bytes"
            )

            content = self.upload_service.upload_content(
                user_id=user_id,
                file_obj=file_obj,
                filename=filename,
                title=title,
                language=language,
            )

            # Generate presigned URL for immediate access
            presigned_url = self.upload_service.get_presigned_url(
                content=content,
                expiration=3600,  # 1 hour
            )

            # Return success response with content details using scannable format
            sections = [
                ResponseSection(
                    heading="Upload Summary",
                    content=f"Content uploaded successfully: {content.title}",
                    metadata={"content_id": content.id},
                ),
                ResponseSection(
                    heading="Content Details",
                    content={
                        "type": content.type.value,
                        "language": content.language,
                        "uploaded_at": content.uploaded_at.isoformat(),
                    },
                ),
                ResponseSection(
                    heading="File Information",
                    content=[
                        f"File size: {content.metadata.file_size} bytes",
                        f"MIME type: {content.metadata.mime_type}",
                        f"S3 location: {content.s3_location}",
                    ],
                ),
                ResponseSection(
                    heading="Access",
                    content=f"Presigned URL valid for 1 hour",
                    metadata={"presigned_url": presigned_url},
                ),
            ]

            response_data = {
                "content_id": content.id,
                "title": content.title,
                "type": content.type.value,
                "language": content.language,
                "uploaded_at": content.uploaded_at.isoformat(),
                "s3_location": content.s3_location,
                "presigned_url": presigned_url,
                "metadata": {
                    "file_size": content.metadata.file_size,
                    "mime_type": content.metadata.mime_type,
                },
            }

            logger.info(f"Successfully processed upload for content {content.id}")

            return ResponseFormatter.success_response(
                data=response_data,
                message="Content uploaded successfully",
                status_code=201,
                sections=sections,
            )

        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return ResponseFormatter.error_response(
                error_code=e.error_code,
                message=e.message,
                status_code=400,
                details=e.details,
            )

        except UnsupportedFormatError as e:
            logger.warning(f"Unsupported format: {e.message}")
            return ResponseFormatter.error_response(
                error_code=e.error_code,
                message=e.message,
                status_code=400,
                details=e.details,
                suggestions=e.details.get("supported_formats") if e.details else None,
            )

        except ContentProcessingError as e:
            logger.error(f"Content processing error: {e.message}")
            return ResponseFormatter.error_response(
                error_code=e.error_code,
                message=e.message,
                status_code=500,
                details=e.details,
            )

        except Exception as e:
            logger.error(f"Unexpected error in upload handler: {e}", exc_info=True)
            return ResponseFormatter.error_response(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred during upload",
                status_code=500,
            )

    def handle_upload_progress(
        self, event: Dict[str, Any], context: Any
    ) -> Dict[str, Any]:
        """
        Handle upload progress tracking request.

        This endpoint can be polled to check upload status for large files.
        For direct uploads, progress is tracked client-side.
        For multipart uploads, this can track S3 multipart upload progress.

        Args:
            event: API Gateway event
            context: Lambda context

        Returns:
            API Gateway response with progress information
        """
        try:
            # Extract content ID from path parameters
            path_params = event.get("pathParameters") or {}
            content_id = path_params.get("content_id")

            if not content_id:
                return self._error_response(
                    400,
                    "MISSING_PARAMETER",
                    "content_id is required",
                )

            # In a real implementation, this would check upload status
            # For now, return a simple status response
            response_data = {
                "content_id": content_id,
                "status": "completed",
                "progress": 100,
                "message": "Upload completed successfully",
            }

            return self._success_response(200, response_data)

        except Exception as e:
            logger.error(f"Error checking upload progress: {e}", exc_info=True)
            return self._error_response(
                500,
                "INTERNAL_ERROR",
                "Failed to check upload progress",
            )

    def handle_get_content(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Handle get content request (returns presigned URL).

        Args:
            event: API Gateway event
            context: Lambda context

        Returns:
            API Gateway response with presigned URL
        """
        try:
            # Extract content ID from path parameters
            path_params = event.get("pathParameters") or {}
            content_id = path_params.get("content_id")

            if not content_id:
                return self._error_response(
                    400,
                    "MISSING_PARAMETER",
                    "content_id is required",
                )

            # In a real implementation, retrieve content from database
            # For now, return error indicating content not found
            return self._error_response(
                404,
                "CONTENT_NOT_FOUND",
                f"Content {content_id} not found",
            )

        except Exception as e:
            logger.error(f"Error retrieving content: {e}", exc_info=True)
            return self._error_response(
                500,
                "INTERNAL_ERROR",
                "Failed to retrieve content",
            )

    def _extract_user_id(self, event: Dict[str, Any]) -> str:
        """
        Extract user ID from API Gateway authorizer.

        Args:
            event: API Gateway event

        Returns:
            User ID

        Raises:
            ValidationError: If user ID cannot be extracted
        """
        try:
            # Try to get from Cognito authorizer
            request_context = event.get("requestContext", {})
            authorizer = request_context.get("authorizer", {})
            claims = authorizer.get("claims", {})
            user_id = claims.get("sub")

            if user_id:
                return user_id

            # Fallback: try to get from custom authorizer
            user_id = authorizer.get("user_id")

            if user_id:
                return user_id

            raise ValidationError(
                message="User ID not found in request context",
                field="user_id",
            )

        except Exception as e:
            logger.error(f"Error extracting user ID: {e}")
            raise ValidationError(
                message="Failed to extract user ID from request",
                field="user_id",
            )

    def _extract_file_content(self, event: Dict[str, Any]) -> bytes:
        """
        Extract file content from API Gateway event.

        Supports both base64-encoded body and JSON with file data.

        Args:
            event: API Gateway event

        Returns:
            File content as bytes

        Raises:
            ValidationError: If file content cannot be extracted
        """
        body = event.get("body")

        if not body:
            raise ValidationError(
                message="Request body is empty",
                field="body",
            )

        # Check if body is base64 encoded
        is_base64 = event.get("isBase64Encoded", False)

        if is_base64:
            # Decode base64 content
            try:
                return base64.b64decode(body)
            except Exception as e:
                raise ValidationError(
                    message=f"Failed to decode base64 content: {str(e)}",
                    field="body",
                )

        # Try to parse as JSON
        try:
            data = json.loads(body)
            if "file_content" in data:
                # Assume file_content is base64 encoded
                return base64.b64decode(data["file_content"])
        except json.JSONDecodeError:
            pass

        # Treat as raw bytes
        if isinstance(body, str):
            return body.encode("utf-8")

        return body

    def _success_response(self, status_code: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create success API response.

        Args:
            status_code: HTTP status code
            data: Response data

        Returns:
            API Gateway response
        """
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",  # Configure CORS as needed
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            },
            "body": json.dumps(data),
        }

    def _error_response(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create error API response.

        Args:
            status_code: HTTP status code
            error_code: Error code
            message: Error message
            details: Additional error details

        Returns:
            API Gateway response
        """
        error_data = {
            "error": error_code,
            "message": message,
        }

        if details:
            error_data["details"] = details

        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            },
            "body": json.dumps(error_data),
        }


# Lambda handler functions
def upload_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for content upload."""
    handler = ContentUploadHandler()
    return handler.handle_upload(event, context)


def progress_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for upload progress tracking."""
    handler = ContentUploadHandler()
    return handler.handle_upload_progress(event, context)


def get_content_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for getting content."""
    handler = ContentUploadHandler()
    return handler.handle_get_content(event, context)
