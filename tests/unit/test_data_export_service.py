"""Unit tests for data export service."""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from botocore.exceptions import ClientError

from src.services.user_management.data_export_service import DataExportService
from src.services.user_management.privacy_manager import DataCategory
from src.shared.utils.errors import AWSServiceError


@pytest.fixture
def mock_tables():
    """Create mock DynamoDB tables."""
    return {
        "user_table": Mock(),
        "progress_table": Mock(),
        "content_table": Mock(),
        "summary_table": Mock(),
        "quiz_table": Mock(),
        "flashcard_table": Mock(),
        "quiz_result_table": Mock(),
        "code_snippet_table": Mock(),
        "voice_recording_table": Mock(),
        "audit_table": Mock(),
    }


@pytest.fixture
def mock_s3_client():
    """Create mock S3 client."""
    mock = Mock()
    mock.upload_file.return_value = "s3://export-bucket/exports/user123/data_export.json"
    return mock


@pytest.fixture
def export_service(mock_tables, mock_s3_client):
    """Create data export service with mocked dependencies."""
    return DataExportService(
        user_table=mock_tables["user_table"],
        progress_table=mock_tables["progress_table"],
        content_table=mock_tables["content_table"],
        summary_table=mock_tables["summary_table"],
        quiz_table=mock_tables["quiz_table"],
        flashcard_table=mock_tables["flashcard_table"],
        quiz_result_table=mock_tables["quiz_result_table"],
        code_snippet_table=mock_tables["code_snippet_table"],
        voice_recording_table=mock_tables["voice_recording_table"],
        audit_table=mock_tables["audit_table"],
        s3_client=mock_s3_client,
        export_bucket="export-bucket",
    )


class TestDataExportService:
    """Test DataExportService class."""

    def test_initialization(self, export_service):
        """Test service initialization."""
        assert export_service.export_bucket == "export-bucket"

    def test_export_user_data_success(self, export_service, mock_tables, mock_s3_client):
        """Test successful export of all user data."""
        # Setup mocks
        mock_tables["user_table"].get_item.return_value = {
            "id": "user123",
            "email": "user@example.com",
        }
        mock_tables["progress_table"].get_item.return_value = {
            "user_id": "user123",
            "total_study_time": 100,
        }
        mock_tables["content_table"].query.return_value = []
        mock_tables["quiz_result_table"].query.return_value = []
        mock_tables["code_snippet_table"].query.return_value = []
        mock_tables["voice_recording_table"].query.return_value = []
        mock_tables["audit_table"].query.return_value = []

        s3_uri = export_service.export_user_data("user123")

        assert s3_uri.startswith("s3://export-bucket/")
        mock_s3_client.upload_file.assert_called_once()

    def test_export_specific_categories(self, export_service, mock_tables, mock_s3_client):
        """Test export of specific data categories."""
        mock_tables["user_table"].get_item.return_value = {
            "id": "user123",
            "email": "user@example.com",
        }

        s3_uri = export_service.export_user_data(
            "user123",
            categories=[DataCategory.PROFILE],
        )

        assert s3_uri is not None
        # Verify upload was called
        mock_s3_client.upload_file.assert_called_once()
        
        # Check the uploaded data
        call_args = mock_s3_client.upload_file.call_args
        uploaded_data = call_args[1]["file_obj"].getvalue().decode('utf-8')
        export_data = json.loads(uploaded_data)
        
        assert "profile" in export_data["data"]
        assert "content" not in export_data["data"]

    def test_export_profile_data(self, export_service, mock_tables):
        """Test profile data export."""
        mock_tables["user_table"].get_item.return_value = {
            "id": "user123",
            "email": "user@example.com",
            "username": "testuser",
        }

        profile = export_service._export_profile_data("user123")

        assert profile["id"] == "user123"
        assert profile["email"] == "user@example.com"

    def test_export_profile_data_not_found(self, export_service, mock_tables):
        """Test profile export when user not found."""
        mock_tables["user_table"].get_item.return_value = None

        profile = export_service._export_profile_data("user123")

        assert profile == {}

    def test_export_content_data_with_summaries(self, export_service, mock_tables):
        """Test content export including summaries."""
        mock_tables["content_table"].query.return_value = [
            {
                "id": "content1",
                "user_id": "user123",
                "title": "Test Content",
            },
        ]
        mock_tables["summary_table"].query.return_value = [
            {
                "id": "summary1",
                "content_id": "content1",
                "text": "Summary text",
            },
        ]

        content = export_service._export_content_data("user123")

        assert len(content) == 1
        assert content[0]["id"] == "content1"
        assert "summaries" in content[0]
        assert len(content[0]["summaries"]) == 1

    def test_export_quiz_data(self, export_service, mock_tables):
        """Test quiz data export."""
        mock_tables["quiz_result_table"].query.return_value = [
            {"quiz_id": "quiz1", "user_id": "user123", "score": 85},
        ]
        mock_tables["content_table"].query.return_value = [
            {"id": "content1"},
        ]
        mock_tables["flashcard_table"].query.return_value = [
            {"id": "flashcard1", "content_id": "content1"},
        ]
        mock_tables["quiz_table"].query.return_value = [
            {"id": "quiz1", "content_id": "content1"},
        ]

        quiz_data = export_service._export_quiz_data("user123")

        assert "quiz_results" in quiz_data
        assert "flashcards" in quiz_data
        assert "quizzes" in quiz_data
        assert len(quiz_data["quiz_results"]) == 1

    def test_export_progress_data(self, export_service, mock_tables):
        """Test progress data export."""
        mock_tables["progress_table"].get_item.return_value = {
            "user_id": "user123",
            "total_study_time": 500,
            "quizzes_completed": 10,
        }

        progress = export_service._export_progress_data("user123")

        assert progress["user_id"] == "user123"
        assert progress["total_study_time"] == 500

    def test_export_progress_data_not_found(self, export_service, mock_tables):
        """Test progress export when not found."""
        mock_tables["progress_table"].get_item.return_value = None

        progress = export_service._export_progress_data("user123")

        assert progress == {}

    def test_export_voice_data(self, export_service, mock_tables):
        """Test voice recordings export."""
        mock_tables["voice_recording_table"].query.return_value = [
            {
                "id": "recording1",
                "user_id": "user123",
                "s3_location": "s3://bucket/voice/recording1.mp3",
            },
        ]

        recordings = export_service._export_voice_data("user123")

        assert len(recordings) == 1
        assert recordings[0]["id"] == "recording1"

    def test_export_code_data(self, export_service, mock_tables):
        """Test code snippets export."""
        mock_tables["code_snippet_table"].query.return_value = [
            {
                "id": "snippet1",
                "user_id": "user123",
                "code": "print('hello')",
            },
        ]

        snippets = export_service._export_code_data("user123")

        assert len(snippets) == 1
        assert snippets[0]["id"] == "snippet1"

    def test_export_audit_logs(self, export_service, mock_tables):
        """Test audit logs export."""
        mock_tables["audit_table"].query.return_value = [
            {
                "id": "log1",
                "user_id": "user123",
                "event_type": "login",
            },
        ]

        logs = export_service._export_audit_logs("user123")

        assert len(logs) == 1
        assert logs[0]["id"] == "log1"

    def test_export_with_category_error(self, export_service, mock_tables, mock_s3_client):
        """Test export continues when a category fails."""
        mock_tables["user_table"].get_item.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service error"}},
            "GetItem",
        )
        mock_tables["progress_table"].get_item.return_value = {
            "user_id": "user123",
            "total_study_time": 100,
        }
        mock_tables["content_table"].query.return_value = []
        mock_tables["quiz_result_table"].query.return_value = []
        mock_tables["code_snippet_table"].query.return_value = []
        mock_tables["voice_recording_table"].query.return_value = []
        mock_tables["audit_table"].query.return_value = []

        s3_uri = export_service.export_user_data("user123")

        assert s3_uri is not None
        # Verify the export includes error information
        call_args = mock_s3_client.upload_file.call_args
        uploaded_data = call_args[1]["file_obj"].getvalue().decode('utf-8')
        export_data = json.loads(uploaded_data)
        
        assert "profile" in export_data["data"]
        assert "error" in export_data["data"]["profile"]

    def test_export_upload_failure(self, export_service, mock_tables, mock_s3_client):
        """Test export failure during S3 upload."""
        mock_tables["user_table"].get_item.return_value = {"id": "user123"}
        mock_tables["progress_table"].get_item.return_value = {}
        mock_tables["content_table"].query.return_value = []
        mock_tables["quiz_result_table"].query.return_value = []
        mock_tables["code_snippet_table"].query.return_value = []
        mock_tables["voice_recording_table"].query.return_value = []
        mock_tables["audit_table"].query.return_value = []
        
        mock_s3_client.upload_file.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "S3 error"}},
            "PutObject",
        )

        with pytest.raises(AWSServiceError):
            export_service.export_user_data("user123")

    def test_get_export_download_url_success(self, export_service, mock_s3_client):
        """Test generating download URL for export."""
        mock_s3_client.get_presigned_url.return_value = "https://s3.amazonaws.com/..."

        url = export_service.get_export_download_url(
            user_id="user123",
            export_key="exports/user123/data_export_20240101.json",
        )

        assert url.startswith("https://")
        mock_s3_client.get_presigned_url.assert_called_once()

    def test_get_export_download_url_wrong_user(self, export_service):
        """Test download URL generation fails for wrong user."""
        with pytest.raises(ValueError) as exc_info:
            export_service.get_export_download_url(
                user_id="user123",
                export_key="exports/user456/data_export.json",
            )

        assert "does not belong" in str(exc_info.value)

    def test_get_export_download_url_failure(self, export_service, mock_s3_client):
        """Test download URL generation failure."""
        mock_s3_client.get_presigned_url.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "File not found"}},
            "GetObject",
        )

        with pytest.raises(AWSServiceError):
            export_service.get_export_download_url(
                user_id="user123",
                export_key="exports/user123/data_export.json",
            )


class TestDataExportEdgeCases:
    """Test edge cases for data export."""

    def test_export_user_with_no_data(self, export_service, mock_tables, mock_s3_client):
        """Test exporting user with no data."""
        # All queries return empty/None
        mock_tables["user_table"].get_item.return_value = None
        mock_tables["progress_table"].get_item.return_value = None
        for table in ["content_table", "quiz_result_table", "code_snippet_table",
                      "voice_recording_table", "audit_table"]:
            mock_tables[table].query.return_value = []

        s3_uri = export_service.export_user_data("user123")

        assert s3_uri is not None
        # Verify export was created even with no data
        mock_s3_client.upload_file.assert_called_once()

    def test_export_with_empty_categories_list(self, export_service, mock_tables, mock_s3_client):
        """Test export with empty categories list."""
        # Setup mocks to return empty
        mock_tables["user_table"].get_item.return_value = None
        mock_tables["progress_table"].get_item.return_value = None
        for table in ["content_table", "quiz_result_table", "code_snippet_table",
                      "voice_recording_table", "audit_table"]:
            mock_tables[table].query.return_value = []
            
        s3_uri = export_service.export_user_data("user123", categories=[])

        assert s3_uri is not None
        # Empty list is treated as "all categories" by the implementation
        call_args = mock_s3_client.upload_file.call_args
        uploaded_data = call_args[1]["file_obj"].getvalue().decode('utf-8')
        export_data = json.loads(uploaded_data)
        
        # All categories are exported (with empty data)
        assert "profile" in export_data["data"]
        assert "content" in export_data["data"]

    def test_export_json_serialization(self, export_service, mock_tables, mock_s3_client):
        """Test that export properly serializes to JSON."""
        mock_tables["user_table"].get_item.return_value = {
            "id": "user123",
            "created_at": datetime.utcnow(),  # datetime object
        }
        mock_tables["progress_table"].get_item.return_value = {}
        mock_tables["content_table"].query.return_value = []
        mock_tables["quiz_result_table"].query.return_value = []
        mock_tables["code_snippet_table"].query.return_value = []
        mock_tables["voice_recording_table"].query.return_value = []
        mock_tables["audit_table"].query.return_value = []

        s3_uri = export_service.export_user_data("user123")

        assert s3_uri is not None
        # Verify JSON was properly serialized
        call_args = mock_s3_client.upload_file.call_args
        uploaded_data = call_args[1]["file_obj"].getvalue().decode('utf-8')
        # Should not raise JSON decode error
        export_data = json.loads(uploaded_data)
        assert export_data["user_id"] == "user123"
