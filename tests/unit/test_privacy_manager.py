"""Unit tests for privacy manager module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from botocore.exceptions import ClientError

from src.services.user_management.privacy_manager import (
    PrivacyManager,
    ConsentType,
    DataCategory,
    ConsentRecord,
)
from src.shared.utils.errors import ValidationError, AWSServiceError


@pytest.fixture
def mock_consent_table():
    """Mock consent DynamoDB table."""
    return Mock()


@pytest.fixture
def mock_deletion_queue_table():
    """Mock deletion queue DynamoDB table."""
    return Mock()


@pytest.fixture
def mock_s3_client():
    """Mock S3 client."""
    return Mock()


@pytest.fixture
def privacy_manager(mock_consent_table, mock_deletion_queue_table, mock_s3_client):
    """Create privacy manager with mocked dependencies."""
    return PrivacyManager(
        consent_table=mock_consent_table,
        deletion_queue_table=mock_deletion_queue_table,
        s3_client=mock_s3_client,
        deletion_grace_period_days=30,
    )


class TestConsentRecord:
    """Test ConsentRecord class."""

    def test_consent_record_creation(self):
        """Test creating a consent record."""
        consent = ConsentRecord(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
            granted=True,
            metadata={"source": "web"},
        )

        assert consent.user_id == "user123"
        assert consent.consent_type == ConsentType.DATA_PROCESSING
        assert consent.granted is True
        assert consent.metadata["source"] == "web"
        assert isinstance(consent.granted_at, datetime)

    def test_consent_record_to_dict(self):
        """Test converting consent record to dictionary."""
        consent = ConsentRecord(
            user_id="user123",
            consent_type=ConsentType.ANALYTICS,
            granted=True,
        )

        consent_dict = consent.to_dict()

        assert consent_dict["user_id"] == "user123"
        assert consent_dict["consent_type"] == "analytics"
        assert consent_dict["granted"] is True
        assert "granted_at" in consent_dict

    def test_consent_is_valid_granted(self):
        """Test consent is valid when granted and not expired."""
        consent = ConsentRecord(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
            granted=True,
            expires_at=datetime.utcnow() + timedelta(days=365),
        )

        assert consent.is_valid() is True

    def test_consent_is_valid_not_granted(self):
        """Test consent is not valid when not granted."""
        consent = ConsentRecord(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
            granted=False,
        )

        assert consent.is_valid() is False

    def test_consent_is_valid_expired(self):
        """Test consent is not valid when expired."""
        consent = ConsentRecord(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
            granted=True,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )

        assert consent.is_valid() is False


class TestPrivacyManager:
    """Test PrivacyManager class."""

    def test_grant_consent_success(self, privacy_manager, mock_consent_table):
        """Test successful consent granting."""
        consent = privacy_manager.grant_consent(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
            metadata={"source": "web"},
        )

        assert consent.user_id == "user123"
        assert consent.consent_type == ConsentType.DATA_PROCESSING
        assert consent.granted is True
        mock_consent_table.put_item.assert_called_once()

    def test_grant_consent_with_expiration(self, privacy_manager, mock_consent_table):
        """Test granting consent with expiration."""
        expires_at = datetime.utcnow() + timedelta(days=365)

        consent = privacy_manager.grant_consent(
            user_id="user123",
            consent_type=ConsentType.MARKETING,
            expires_at=expires_at,
        )

        assert consent.expires_at == expires_at
        mock_consent_table.put_item.assert_called_once()

    def test_grant_consent_failure(self, privacy_manager, mock_consent_table):
        """Test consent granting failure."""
        mock_consent_table.put_item.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service error"}},
            "PutItem",
        )

        with pytest.raises(AWSServiceError):
            privacy_manager.grant_consent(
                user_id="user123",
                consent_type=ConsentType.DATA_PROCESSING,
            )

    def test_revoke_consent_success(self, privacy_manager, mock_consent_table):
        """Test successful consent revocation."""
        privacy_manager.revoke_consent(
            user_id="user123",
            consent_type=ConsentType.ANALYTICS,
        )

        mock_consent_table.update_item.assert_called_once()
        call_args = mock_consent_table.update_item.call_args
        assert call_args[1]["expression_values"][":granted"] is False

    def test_revoke_consent_failure(self, privacy_manager, mock_consent_table):
        """Test consent revocation failure."""
        mock_consent_table.update_item.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service error"}},
            "UpdateItem",
        )

        with pytest.raises(AWSServiceError):
            privacy_manager.revoke_consent(
                user_id="user123",
                consent_type=ConsentType.ANALYTICS,
            )

    def test_check_consent_granted(self, privacy_manager, mock_consent_table):
        """Test checking granted consent."""
        mock_consent_table.get_item.return_value = {
            "user_id": "user123",
            "consent_type": "data_processing",
            "granted": True,
        }

        result = privacy_manager.check_consent(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
        )

        assert result is True

    def test_check_consent_not_granted(self, privacy_manager, mock_consent_table):
        """Test checking not granted consent."""
        mock_consent_table.get_item.return_value = {
            "user_id": "user123",
            "consent_type": "data_processing",
            "granted": False,
        }

        result = privacy_manager.check_consent(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
        )

        assert result is False

    def test_check_consent_not_found(self, privacy_manager, mock_consent_table):
        """Test checking consent when not found."""
        mock_consent_table.get_item.return_value = None

        result = privacy_manager.check_consent(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
        )

        assert result is False

    def test_check_consent_expired(self, privacy_manager, mock_consent_table):
        """Test checking expired consent."""
        expired_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
        mock_consent_table.get_item.return_value = {
            "user_id": "user123",
            "consent_type": "data_processing",
            "granted": True,
            "expires_at": expired_date,
        }

        result = privacy_manager.check_consent(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
        )

        assert result is False

    def test_require_consent_success(self, privacy_manager, mock_consent_table):
        """Test require consent succeeds when granted."""
        mock_consent_table.get_item.return_value = {
            "user_id": "user123",
            "consent_type": "data_processing",
            "granted": True,
        }

        # Should not raise
        privacy_manager.require_consent(
            user_id="user123",
            consent_type=ConsentType.DATA_PROCESSING,
        )

    def test_require_consent_failure(self, privacy_manager, mock_consent_table):
        """Test require consent raises when not granted."""
        mock_consent_table.get_item.return_value = None

        with pytest.raises(ValidationError) as exc_info:
            privacy_manager.require_consent(
                user_id="user123",
                consent_type=ConsentType.CONTENT_TRAINING,
                purpose="AI model training",
            )

        assert "consent required" in str(exc_info.value).lower()
        assert "content_training" in str(exc_info.value)

    def test_get_user_consents(self, privacy_manager, mock_consent_table):
        """Test getting all user consents."""
        mock_consent_table.query.return_value = [
            {
                "user_id": "user123",
                "consent_type": "data_processing",
                "granted": True,
            },
            {
                "user_id": "user123",
                "consent_type": "analytics",
                "granted": False,
            },
        ]

        results = privacy_manager.get_user_consents("user123")

        assert len(results) == 2
        assert results[0]["consent_type"] == "data_processing"
        assert results[1]["consent_type"] == "analytics"

    def test_request_data_export(self, privacy_manager, mock_consent_table):
        """Test requesting data export."""
        export_id = privacy_manager.request_data_export(
            user_id="user123",
            categories=[DataCategory.PROFILE, DataCategory.CONTENT],
        )

        assert export_id is not None
        mock_consent_table.put_item.assert_called_once()
        call_args = mock_consent_table.put_item.call_args[0][0]
        assert call_args["user_id"] == "user123"
        assert call_args["status"] == "pending"

    def test_request_data_export_all_categories(
        self, privacy_manager, mock_consent_table
    ):
        """Test requesting data export for all categories."""
        export_id = privacy_manager.request_data_export(user_id="user123")

        assert export_id is not None
        call_args = mock_consent_table.put_item.call_args[0][0]
        assert call_args["categories"] == "all"

    def test_request_data_deletion(
        self, privacy_manager, mock_deletion_queue_table
    ):
        """Test requesting data deletion."""
        deletion_id = privacy_manager.request_data_deletion(
            user_id="user123",
            categories=[DataCategory.CONTENT],
        )

        assert deletion_id is not None
        mock_deletion_queue_table.put_item.assert_called_once()
        call_args = mock_deletion_queue_table.put_item.call_args[0][0]
        assert call_args["user_id"] == "user123"
        assert call_args["status"] == "pending"
        assert call_args["immediate"] is False

    def test_request_data_deletion_immediate(
        self, privacy_manager, mock_deletion_queue_table
    ):
        """Test requesting immediate data deletion."""
        deletion_id = privacy_manager.request_data_deletion(
            user_id="user123",
            immediate=True,
        )

        assert deletion_id is not None
        call_args = mock_deletion_queue_table.put_item.call_args[0][0]
        assert call_args["immediate"] is True

    def test_cancel_data_deletion_success(
        self, privacy_manager, mock_deletion_queue_table
    ):
        """Test cancelling data deletion."""
        mock_deletion_queue_table.get_item.return_value = {
            "deletion_id": "del123",
            "user_id": "user123",
            "status": "pending",
        }

        privacy_manager.cancel_data_deletion(
            deletion_id="del123",
            user_id="user123",
        )

        mock_deletion_queue_table.update_item.assert_called_once()
        call_args = mock_deletion_queue_table.update_item.call_args
        assert call_args[1]["expression_values"][":status"] == "cancelled"

    def test_cancel_data_deletion_not_found(
        self, privacy_manager, mock_deletion_queue_table
    ):
        """Test cancelling non-existent deletion request."""
        mock_deletion_queue_table.get_item.return_value = None

        with pytest.raises(ValidationError) as exc_info:
            privacy_manager.cancel_data_deletion(
                deletion_id="del123",
                user_id="user123",
            )

        assert "not found" in str(exc_info.value).lower()

    def test_cancel_data_deletion_wrong_user(
        self, privacy_manager, mock_deletion_queue_table
    ):
        """Test cancelling deletion request by wrong user."""
        mock_deletion_queue_table.get_item.return_value = {
            "deletion_id": "del123",
            "user_id": "user456",
            "status": "pending",
        }

        with pytest.raises(ValidationError) as exc_info:
            privacy_manager.cancel_data_deletion(
                deletion_id="del123",
                user_id="user123",
            )

        assert "does not belong" in str(exc_info.value).lower()

    def test_cancel_data_deletion_already_processed(
        self, privacy_manager, mock_deletion_queue_table
    ):
        """Test cancelling already processed deletion."""
        mock_deletion_queue_table.get_item.return_value = {
            "deletion_id": "del123",
            "user_id": "user123",
            "status": "completed",
        }

        with pytest.raises(ValidationError) as exc_info:
            privacy_manager.cancel_data_deletion(
                deletion_id="del123",
                user_id="user123",
            )

        assert "cannot cancel" in str(exc_info.value).lower()

    def test_process_pending_deletions(
        self, privacy_manager, mock_deletion_queue_table
    ):
        """Test processing pending deletions."""
        past_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
        mock_deletion_queue_table.scan.return_value = [
            {
                "deletion_id": "del123",
                "user_id": "user123",
                "status": "pending",
                "scheduled_deletion_at": past_date,
            },
        ]

        count = privacy_manager.process_pending_deletions()

        assert count == 1
        mock_deletion_queue_table.update_item.assert_called_once()


class TestConsentTypes:
    """Test consent type enumerations."""

    def test_consent_types_exist(self):
        """Test all consent types are defined."""
        assert ConsentType.DATA_PROCESSING.value == "data_processing"
        assert ConsentType.CONTENT_TRAINING.value == "content_training"
        assert ConsentType.ANALYTICS.value == "analytics"
        assert ConsentType.MARKETING.value == "marketing"
        assert ConsentType.THIRD_PARTY_SHARING.value == "third_party_sharing"


class TestDataCategories:
    """Test data category enumerations."""

    def test_data_categories_exist(self):
        """Test all data categories are defined."""
        assert DataCategory.PROFILE.value == "profile"
        assert DataCategory.CONTENT.value == "content"
        assert DataCategory.QUIZ_RESULTS.value == "quiz_results"
        assert DataCategory.LEARNING_PROGRESS.value == "learning_progress"
        assert DataCategory.VOICE_RECORDINGS.value == "voice_recordings"
        assert DataCategory.CODE_SNIPPETS.value == "code_snippets"
        assert DataCategory.AUDIT_LOGS.value == "audit_logs"
