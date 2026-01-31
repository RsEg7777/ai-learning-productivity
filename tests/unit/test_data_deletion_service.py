"""Unit tests for data deletion service."""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from botocore.exceptions import ClientError

from src.services.user_management.data_deletion_service import DataDeletionService
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
    return Mock()


@pytest.fixture
def mock_cognito_client():
    """Create mock Cognito client."""
    return Mock()


@pytest.fixture
def deletion_service(mock_tables, mock_s3_client, mock_cognito_client):
    """Create data deletion service with mocked dependencies."""
    return DataDeletionService(
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
        content_bucket="test-bucket",
        cognito_client=mock_cognito_client,
    )


class TestDataDeletionService:
    """Test DataDeletionService class."""

    def test_initialization(self, deletion_service):
        """Test service initialization."""
        assert deletion_service.content_bucket == "test-bucket"
        assert deletion_service.cognito_client is not None

    def test_delete_all_user_data_success(
        self, deletion_service, mock_tables
    ):
        """Test successful deletion of all user data."""
        # Setup mocks
        mock_tables["content_table"].query.return_value = []
        mock_tables["quiz_result_table"].query.return_value = []
        mock_tables["code_snippet_table"].query.return_value = []
        mock_tables["voice_recording_table"].query.return_value = []
        mock_tables["audit_table"].query.return_value = []

        result = deletion_service.delete_all_user_data("user123")

        assert result["user_id"] == "user123"
        assert "deleted_at" in result
        assert "categories" in result
        assert len(result["errors"]) == 0

    def test_delete_specific_categories(
        self, deletion_service, mock_tables
    ):
        """Test deletion of specific data categories."""
        mock_tables["content_table"].query.return_value = []

        result = deletion_service.delete_all_user_data(
            "user123",
            categories=[DataCategory.CONTENT],
        )

        assert "content" in result["categories"]
        assert "profile" not in result["categories"]

    def test_delete_profile_data(self, deletion_service, mock_tables):
        """Test profile data deletion."""
        count = deletion_service._delete_profile_data("user123")

        assert count == 1
        mock_tables["user_table"].delete_item.assert_called_once_with(
            {"id": "user123"}
        )

    def test_delete_content_data_with_s3_files(
        self, deletion_service, mock_tables, mock_s3_client
    ):
        """Test content deletion including S3 files."""
        mock_tables["content_table"].query.return_value = [
            {
                "id": "content1",
                "user_id": "user123",
                "s3_location": "s3://test-bucket/user123/file1.pdf",
            },
        ]
        mock_tables["summary_table"].query.return_value = [
            {"id": "summary1", "content_id": "content1"},
        ]

        count = deletion_service._delete_content_data("user123")

        assert count >= 1
        mock_s3_client.delete_file.assert_called_once()
        mock_tables["content_table"].delete_item.assert_called()

    def test_delete_content_data_without_s3_files(
        self, deletion_service, mock_tables
    ):
        """Test content deletion without S3 files."""
        mock_tables["content_table"].query.return_value = [
            {
                "id": "content1",
                "user_id": "user123",
                "s3_location": None,
            },
        ]
        mock_tables["summary_table"].query.return_value = []

        count = deletion_service._delete_content_data("user123")

        assert count >= 1
        mock_tables["content_table"].delete_item.assert_called()

    def test_delete_quiz_data(self, deletion_service, mock_tables):
        """Test quiz data deletion."""
        mock_tables["quiz_result_table"].query.return_value = [
            {"user_id": "user123", "quiz_id": "quiz1"},
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

        count = deletion_service._delete_quiz_data("user123")

        assert count >= 1
        mock_tables["quiz_result_table"].delete_item.assert_called()

    def test_delete_progress_data(self, deletion_service, mock_tables):
        """Test progress data deletion."""
        count = deletion_service._delete_progress_data("user123")

        assert count == 1
        mock_tables["progress_table"].delete_item.assert_called_once_with(
            {"user_id": "user123"}
        )

    def test_delete_voice_data_with_recordings(
        self, deletion_service, mock_tables, mock_s3_client
    ):
        """Test voice data deletion with S3 recordings."""
        mock_tables["voice_recording_table"].query.return_value = [
            {
                "id": "recording1",
                "user_id": "user123",
                "s3_location": "s3://test-bucket/voice/recording1.mp3",
            },
        ]

        count = deletion_service._delete_voice_data("user123")

        assert count == 1
        mock_s3_client.delete_file.assert_called_once()
        mock_tables["voice_recording_table"].delete_item.assert_called()

    def test_delete_code_data(self, deletion_service, mock_tables):
        """Test code snippets deletion."""
        mock_tables["code_snippet_table"].query.return_value = [
            {"id": "snippet1", "user_id": "user123"},
            {"id": "snippet2", "user_id": "user123"},
        ]

        count = deletion_service._delete_code_data("user123")

        assert count == 2
        assert mock_tables["code_snippet_table"].delete_item.call_count == 2

    def test_anonymize_audit_logs(self, deletion_service, mock_tables):
        """Test audit log anonymization."""
        mock_tables["audit_table"].query.return_value = [
            {
                "id": "log1",
                "user_id": "user123",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0",
            },
        ]

        count = deletion_service._anonymize_audit_logs("user123")

        assert count == 1
        mock_tables["audit_table"].update_item.assert_called_once()
        call_args = mock_tables["audit_table"].update_item.call_args
        assert "DELETED_USER_" in call_args[1]["expression_values"][":anon_id"]

    def test_delete_cognito_account_success(
        self, deletion_service, mock_cognito_client
    ):
        """Test Cognito account deletion."""
        deletion_service.delete_cognito_account("user123", "access_token")

        mock_cognito_client.delete_user.assert_called_once_with("access_token")

    def test_delete_cognito_account_no_client(self, mock_tables, mock_s3_client):
        """Test Cognito deletion when client not configured."""
        service = DataDeletionService(
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
            content_bucket="test-bucket",
            cognito_client=None,
        )

        # Should not raise error
        service.delete_cognito_account("user123", "access_token")

    def test_delete_cognito_account_failure(
        self, deletion_service, mock_cognito_client
    ):
        """Test Cognito account deletion failure."""
        mock_cognito_client.delete_user.side_effect = ClientError(
            {"Error": {"Code": "NotAuthorizedException", "Message": "Invalid token"}},
            "DeleteUser",
        )

        with pytest.raises(AWSServiceError):
            deletion_service.delete_cognito_account("user123", "invalid_token")

    def test_deletion_with_errors(self, deletion_service, mock_tables):
        """Test deletion continues even if some categories fail."""
        # Make content deletion fail
        mock_tables["content_table"].query.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service error"}},
            "Query",
        )
        # Other tables work fine
        mock_tables["quiz_result_table"].query.return_value = []
        mock_tables["code_snippet_table"].query.return_value = []
        mock_tables["voice_recording_table"].query.return_value = []
        mock_tables["audit_table"].query.return_value = []

        result = deletion_service.delete_all_user_data("user123")

        # Should have errors but continue with other categories
        assert len(result["errors"]) > 0
        assert "content" in result["errors"][0].lower()

    def test_s3_deletion_failure_continues(
        self, deletion_service, mock_tables, mock_s3_client
    ):
        """Test that S3 deletion failure doesn't stop content deletion."""
        mock_tables["content_table"].query.return_value = [
            {
                "id": "content1",
                "user_id": "user123",
                "s3_location": "s3://test-bucket/file1.pdf",
            },
        ]
        mock_tables["summary_table"].query.return_value = []
        mock_s3_client.delete_file.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "File not found"}},
            "DeleteObject",
        )

        # Should not raise, just log warning
        count = deletion_service._delete_content_data("user123")

        assert count >= 1
        mock_tables["content_table"].delete_item.assert_called()


class TestDataDeletionEdgeCases:
    """Test edge cases for data deletion."""

    def test_delete_user_with_no_data(self, deletion_service, mock_tables):
        """Test deleting user with no data."""
        # All queries return empty
        for table in mock_tables.values():
            table.query.return_value = []

        result = deletion_service.delete_all_user_data("user123")

        assert result["user_id"] == "user123"
        assert len(result["errors"]) == 0

    def test_delete_with_empty_categories_list(
        self, deletion_service, mock_tables
    ):
        """Test deletion with empty categories list."""
        # Setup mocks to return empty
        for table in mock_tables.values():
            table.query.return_value = []
            
        result = deletion_service.delete_all_user_data("user123", categories=[])

        # With empty list, it iterates over empty list, so no categories deleted
        # But the function still processes the empty list
        assert isinstance(result["categories"], dict)

    def test_anonymize_logs_with_no_logs(self, deletion_service, mock_tables):
        """Test anonymizing when no logs exist."""
        mock_tables["audit_table"].query.return_value = []

        count = deletion_service._anonymize_audit_logs("user123")

        assert count == 0
