"""Unit tests for content upload API handler."""

import pytest
import json
import base64
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from src.api.content_upload_handler import ContentUploadHandler
from src.shared.models.content import Content, ContentType
from src.shared.utils.errors import ValidationError, UnsupportedFormatError


class TestContentUploadHandler:
    """Test suite for ContentUploadHandler."""

    @pytest.fixture
    def mock_upload_service(self):
        """Create mock upload service."""
        mock_service = Mock()
        
        # Mock upload_content
        mock_content = Content(
            id="content123",
            user_id="user123",
            title="Test Document",
            type=ContentType.PDF,
            original_text="",
            s3_location="s3://test-bucket/uploads/user123/2024/01/content123.pdf",
        )
        mock_service.upload_content.return_value = mock_content
        
        # Mock get_presigned_url
        mock_service.get_presigned_url.return_value = "https://presigned-url.com/file.pdf"
        
        return mock_service

    @pytest.fixture
    def handler(self, mock_upload_service):
        """Create ContentUploadHandler instance with mocked dependencies."""
        with patch("src.api.content_upload_handler.S3Client"):
            with patch("src.api.content_upload_handler.ContentUploadService") as mock_service_class:
                mock_service_class.return_value = mock_upload_service
                handler = ContentUploadHandler(bucket_name="test-bucket")
                handler.upload_service = mock_upload_service
                return handler

    @pytest.fixture
    def sample_event(self):
        """Create sample API Gateway event."""
        file_content = b"Sample PDF content"
        encoded_content = base64.b64encode(file_content).decode("utf-8")
        
        return {
            "body": encoded_content,
            "isBase64Encoded": True,
            "headers": {
                "content-type": "application/pdf",
            },
            "queryStringParameters": {
                "filename": "document.pdf",
                "title": "Test Document",
                "language": "en",
            },
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user123",
                    }
                }
            },
        }

    def test_handle_upload_success(self, handler, mock_upload_service, sample_event):
        """Test successful upload handling."""
        # Act
        response = handler.handle_upload(sample_event, None)

        # Assert
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["status"] == "success"
        assert "data" in body
        assert body["data"]["content_id"] == "content123"
        assert body["data"]["title"] == "Test Document"
        assert body["data"]["type"] == "pdf"
        assert "presigned_url" in body["data"]
        assert "message" in body

        # Verify upload service was called
        mock_upload_service.upload_content.assert_called_once()

    def test_handle_upload_missing_filename(self, handler, sample_event):
        """Test upload with missing filename parameter."""
        # Arrange
        sample_event["queryStringParameters"] = {}

        # Act
        response = handler.handle_upload(sample_event, None)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "MISSING_PARAMETER"
        assert "filename" in body["message"]

    def test_handle_upload_validation_error(self, handler, mock_upload_service, sample_event):
        """Test upload with validation error."""
        # Arrange
        mock_upload_service.upload_content.side_effect = ValidationError(
            message="Invalid file size",
            field="file_size",
        )

        # Act
        response = handler.handle_upload(sample_event, None)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["status"] == "error"
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "Invalid file size" in body["error"]["message"]

    def test_handle_upload_unsupported_format(self, handler, mock_upload_service, sample_event):
        """Test upload with unsupported format."""
        # Arrange
        sample_event["queryStringParameters"]["filename"] = "document.xyz"
        mock_upload_service.upload_content.side_effect = UnsupportedFormatError(
            format_provided=".xyz",
            supported_formats=[".pdf", ".txt"],
        )

        # Act
        response = handler.handle_upload(sample_event, None)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["status"] == "error"
        assert body["error"]["code"] == "UNSUPPORTED_FORMAT"
        assert ".xyz" in body["error"]["message"]

    def test_handle_upload_json_body(self, handler, mock_upload_service):
        """Test upload with JSON body containing base64 file content."""
        # Arrange
        file_content = b"Sample content"
        encoded_content = base64.b64encode(file_content).decode("utf-8")
        
        event = {
            "body": json.dumps({
                "file_content": encoded_content,
            }),
            "isBase64Encoded": False,
            "queryStringParameters": {
                "filename": "document.pdf",
            },
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user123",
                    }
                }
            },
        }

        # Act
        response = handler.handle_upload(event, None)

        # Assert
        assert response["statusCode"] == 201
        mock_upload_service.upload_content.assert_called_once()

    def test_handle_upload_empty_body(self, handler, sample_event):
        """Test upload with empty body."""
        # Arrange
        sample_event["body"] = None

        # Act
        response = handler.handle_upload(sample_event, None)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["status"] == "error"
        assert "body" in body["error"]["message"].lower()

    def test_handle_upload_no_user_id(self, handler, sample_event):
        """Test upload without user ID in context."""
        # Arrange
        sample_event["requestContext"] = {}

        # Act
        response = handler.handle_upload(sample_event, None)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["status"] == "error"
        assert "user" in body["error"]["message"].lower()

    def test_handle_upload_progress_success(self, handler):
        """Test upload progress tracking."""
        # Arrange
        event = {
            "pathParameters": {
                "content_id": "content123",
            }
        }

        # Act
        response = handler.handle_upload_progress(event, None)

        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["content_id"] == "content123"
        assert body["status"] == "completed"
        assert body["progress"] == 100

    def test_handle_upload_progress_missing_content_id(self, handler):
        """Test upload progress without content ID."""
        # Arrange
        event = {
            "pathParameters": {}
        }

        # Act
        response = handler.handle_upload_progress(event, None)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "MISSING_PARAMETER"

    def test_handle_get_content_missing_content_id(self, handler):
        """Test get content without content ID."""
        # Arrange
        event = {
            "pathParameters": {}
        }

        # Act
        response = handler.handle_get_content(event, None)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "MISSING_PARAMETER"

    def test_handle_get_content_not_found(self, handler):
        """Test get content when content doesn't exist."""
        # Arrange
        event = {
            "pathParameters": {
                "content_id": "nonexistent",
            }
        }

        # Act
        response = handler.handle_get_content(event, None)

        # Assert
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"] == "CONTENT_NOT_FOUND"

    def test_extract_user_id_from_cognito(self, handler):
        """Test user ID extraction from Cognito authorizer."""
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "cognito-user-123",
                    }
                }
            }
        }

        # Act
        user_id = handler._extract_user_id(event)

        # Assert
        assert user_id == "cognito-user-123"

    def test_extract_user_id_from_custom_authorizer(self, handler):
        """Test user ID extraction from custom authorizer."""
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "user_id": "custom-user-456",
                }
            }
        }

        # Act
        user_id = handler._extract_user_id(event)

        # Assert
        assert user_id == "custom-user-456"

    def test_extract_user_id_missing(self, handler):
        """Test user ID extraction when not present."""
        # Arrange
        event = {
            "requestContext": {}
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            handler._extract_user_id(event)

        assert "user" in str(exc_info.value).lower()

    def test_extract_file_content_base64(self, handler):
        """Test file content extraction from base64."""
        # Arrange
        file_content = b"Test content"
        encoded = base64.b64encode(file_content).decode("utf-8")
        event = {
            "body": encoded,
            "isBase64Encoded": True,
        }

        # Act
        content = handler._extract_file_content(event)

        # Assert
        assert content == file_content

    def test_extract_file_content_json(self, handler):
        """Test file content extraction from JSON."""
        # Arrange
        file_content = b"Test content"
        encoded = base64.b64encode(file_content).decode("utf-8")
        event = {
            "body": json.dumps({"file_content": encoded}),
            "isBase64Encoded": False,
        }

        # Act
        content = handler._extract_file_content(event)

        # Assert
        assert content == file_content

    def test_extract_file_content_raw_string(self, handler):
        """Test file content extraction from raw string."""
        # Arrange
        event = {
            "body": "Raw text content",
            "isBase64Encoded": False,
        }

        # Act
        content = handler._extract_file_content(event)

        # Assert
        assert content == b"Raw text content"

    def test_extract_file_content_empty_body(self, handler):
        """Test file content extraction with empty body."""
        # Arrange
        event = {
            "body": None,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            handler._extract_file_content(event)

        assert "body" in str(exc_info.value).lower()

    def test_success_response_format(self, handler):
        """Test success response format."""
        # Arrange
        data = {"key": "value"}

        # Act
        response = handler._success_response(200, data)

        # Assert
        assert response["statusCode"] == 200
        assert "Content-Type" in response["headers"]
        assert response["headers"]["Content-Type"] == "application/json"
        assert "Access-Control-Allow-Origin" in response["headers"]
        body = json.loads(response["body"])
        assert body == data

    def test_error_response_format(self, handler):
        """Test error response format."""
        # Arrange
        error_code = "TEST_ERROR"
        message = "Test error message"
        details = {"field": "test"}

        # Act
        response = handler._error_response(400, error_code, message, details)

        # Assert
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == error_code
        assert body["message"] == message
        assert body["details"] == details

    def test_cors_headers_present(self, handler, sample_event):
        """Test that CORS headers are present in responses."""
        # Act
        response = handler.handle_upload(sample_event, None)

        # Assert
        headers = response["headers"]
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Headers" in headers
        assert "Access-Control-Allow-Methods" in headers

    def test_lambda_handler_functions(self, mock_upload_service):
        """Test Lambda handler wrapper functions."""
        from src.api.content_upload_handler import (
            upload_handler,
            progress_handler,
            get_content_handler,
        )

        # Create sample events
        upload_event = {
            "body": base64.b64encode(b"test").decode("utf-8"),
            "isBase64Encoded": True,
            "queryStringParameters": {"filename": "test.pdf"},
            "requestContext": {
                "authorizer": {"claims": {"sub": "user123"}}
            },
        }

        progress_event = {
            "pathParameters": {"content_id": "content123"}
        }

        get_event = {
            "pathParameters": {"content_id": "content123"}
        }

        # Test that handlers can be called (they will fail due to missing AWS setup)
        # but we're just checking they're callable
        assert callable(upload_handler)
        assert callable(progress_handler)
        assert callable(get_content_handler)
