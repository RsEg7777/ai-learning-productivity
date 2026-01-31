"""Unit tests for audit logger module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from src.services.user_management.audit_logger import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
)
from src.shared.utils.errors import AWSServiceError


@pytest.fixture
def mock_audit_table():
    """Mock audit DynamoDB table."""
    return Mock()


@pytest.fixture
def audit_logger(mock_audit_table):
    """Create audit logger with mocked dependencies."""
    return AuditLogger(audit_table=mock_audit_table)


class TestAuditEvent:
    """Test AuditEvent class."""

    def test_audit_event_creation(self):
        """Test creating an audit event."""
        event = AuditEvent(
            event_type=AuditEventType.USER_LOGIN,
            user_id="user123",
            resource_type="session",
            resource_id="session456",
            action="login",
            result="success",
            severity=AuditSeverity.INFO,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            metadata={"device": "mobile"},
        )

        assert event.event_type == AuditEventType.USER_LOGIN
        assert event.user_id == "user123"
        assert event.resource_type == "session"
        assert event.resource_id == "session456"
        assert event.action == "login"
        assert event.result == "success"
        assert event.severity == AuditSeverity.INFO
        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "Mozilla/5.0"
        assert event.metadata["device"] == "mobile"
        assert event.event_id is not None
        assert isinstance(event.timestamp, datetime)

    def test_audit_event_to_dict(self):
        """Test converting audit event to dictionary."""
        event = AuditEvent(
            event_type=AuditEventType.CONTENT_UPLOADED,
            user_id="user123",
            resource_type="content",
            resource_id="content456",
        )

        event_dict = event.to_dict()

        assert event_dict["event_type"] == "content.uploaded"
        assert event_dict["user_id"] == "user123"
        assert event_dict["resource_type"] == "content"
        assert event_dict["resource_id"] == "content456"
        assert "event_id" in event_dict
        assert "timestamp" in event_dict


class TestAuditLogger:
    """Test AuditLogger class."""

    def test_log_event_success(self, audit_logger, mock_audit_table):
        """Test successful event logging."""
        event = AuditEvent(
            event_type=AuditEventType.USER_LOGIN,
            user_id="user123",
            action="login",
        )

        audit_logger.log_event(event)

        mock_audit_table.put_item.assert_called_once()
        call_args = mock_audit_table.put_item.call_args[0][0]
        assert call_args["event_type"] == "user.login"
        assert call_args["user_id"] == "user123"

    def test_log_event_failure_non_critical(self, audit_logger, mock_audit_table):
        """Test event logging failure for non-critical event."""
        mock_audit_table.put_item.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service error"}},
            "PutItem",
        )

        event = AuditEvent(
            event_type=AuditEventType.CONTENT_VIEWED,
            user_id="user123",
            severity=AuditSeverity.INFO,
        )

        # Should not raise for non-critical events
        audit_logger.log_event(event)

    def test_log_event_failure_critical(self, audit_logger, mock_audit_table):
        """Test event logging failure for critical event."""
        mock_audit_table.put_item.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service error"}},
            "PutItem",
        )

        event = AuditEvent(
            event_type=AuditEventType.DATA_DELETION_REQUESTED,
            user_id="user123",
            severity=AuditSeverity.CRITICAL,
        )

        # Should raise for critical events
        with pytest.raises(AWSServiceError):
            audit_logger.log_event(event)

    def test_log_authentication_success(self, audit_logger, mock_audit_table):
        """Test logging successful authentication."""
        audit_logger.log_authentication(
            user_id="user123",
            success=True,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            metadata={"method": "password"},
        )

        mock_audit_table.put_item.assert_called_once()
        call_args = mock_audit_table.put_item.call_args[0][0]
        assert call_args["event_type"] == "user.login"
        assert call_args["result"] == "success"
        assert call_args["severity"] == "info"

    def test_log_authentication_failure(self, audit_logger, mock_audit_table):
        """Test logging failed authentication."""
        audit_logger.log_authentication(
            user_id="user123",
            success=False,
            ip_address="192.168.1.1",
        )

        mock_audit_table.put_item.assert_called_once()
        call_args = mock_audit_table.put_item.call_args[0][0]
        assert call_args["event_type"] == "user.login.failed"
        assert call_args["result"] == "failure"
        assert call_args["severity"] == "warning"

    def test_log_access_control_granted(self, audit_logger, mock_audit_table):
        """Test logging access granted."""
        audit_logger.log_access_control(
            user_id="user123",
            resource_type="content",
            resource_id="content456",
            permission="content:delete",
            granted=True,
            ip_address="192.168.1.1",
        )

        mock_audit_table.put_item.assert_called_once()
        call_args = mock_audit_table.put_item.call_args[0][0]
        assert call_args["event_type"] == "access.granted"
        assert call_args["result"] == "granted"
        assert call_args["severity"] == "info"

    def test_log_access_control_denied(self, audit_logger, mock_audit_table):
        """Test logging access denied."""
        audit_logger.log_access_control(
            user_id="user123",
            resource_type="content",
            resource_id="content456",
            permission="content:delete",
            granted=False,
        )

        mock_audit_table.put_item.assert_called_once()
        call_args = mock_audit_table.put_item.call_args[0][0]
        assert call_args["event_type"] == "access.denied"
        assert call_args["result"] == "denied"
        assert call_args["severity"] == "warning"

    def test_log_data_access_read(self, audit_logger, mock_audit_table):
        """Test logging data read access."""
        audit_logger.log_data_access(
            user_id="user123",
            resource_type="content",
            resource_id="content456",
            action="read",
            ip_address="192.168.1.1",
        )

        mock_audit_table.put_item.assert_called_once()
        call_args = mock_audit_table.put_item.call_args[0][0]
        assert call_args["event_type"] == "content.viewed"
        assert call_args["action"] == "read"

    def test_log_data_access_write(self, audit_logger, mock_audit_table):
        """Test logging data write access."""
        audit_logger.log_data_access(
            user_id="user123",
            resource_type="content",
            resource_id="content456",
            action="write",
        )

        mock_audit_table.put_item.assert_called_once()
        call_args = mock_audit_table.put_item.call_args[0][0]
        assert call_args["event_type"] == "content.updated"

    def test_log_data_access_delete(self, audit_logger, mock_audit_table):
        """Test logging data delete access."""
        audit_logger.log_data_access(
            user_id="user123",
            resource_type="content",
            resource_id="content456",
            action="delete",
        )

        mock_audit_table.put_item.assert_called_once()
        call_args = mock_audit_table.put_item.call_args[0][0]
        assert call_args["event_type"] == "content.deleted"

    def test_log_privacy_event(self, audit_logger, mock_audit_table):
        """Test logging privacy event."""
        audit_logger.log_privacy_event(
            user_id="user123",
            event_type=AuditEventType.CONSENT_GRANTED,
            metadata={"consent_type": "data_processing"},
        )

        mock_audit_table.put_item.assert_called_once()
        call_args = mock_audit_table.put_item.call_args[0][0]
        assert call_args["event_type"] == "consent.granted"
        assert call_args["metadata"]["consent_type"] == "data_processing"

    def test_log_error(self, audit_logger, mock_audit_table):
        """Test logging system error."""
        audit_logger.log_error(
            error_message="Database connection failed",
            user_id="user123",
            resource_type="database",
            severity=AuditSeverity.ERROR,
            metadata={"error_code": "DB_CONN_FAILED"},
        )

        mock_audit_table.put_item.assert_called_once()
        call_args = mock_audit_table.put_item.call_args[0][0]
        assert call_args["event_type"] == "system.error"
        assert call_args["severity"] == "error"
        assert "Database connection failed" in call_args["metadata"]["error_message"]

    def test_query_user_activity(self, audit_logger, mock_audit_table):
        """Test querying user activity."""
        mock_audit_table.query.return_value = [
            {
                "event_id": "event1",
                "event_type": "user.login",
                "user_id": "user123",
            },
            {
                "event_id": "event2",
                "event_type": "content.uploaded",
                "user_id": "user123",
            },
        ]

        start_time = datetime.utcnow() - timedelta(days=7)
        end_time = datetime.utcnow()

        results = audit_logger.query_user_activity(
            user_id="user123",
            start_time=start_time,
            end_time=end_time,
            event_types=[AuditEventType.USER_LOGIN, AuditEventType.CONTENT_UPLOADED],
            limit=100,
        )

        assert len(results) == 2
        assert results[0]["event_type"] == "user.login"
        assert results[1]["event_type"] == "content.uploaded"
        mock_audit_table.query.assert_called_once()

    def test_query_user_activity_failure(self, audit_logger, mock_audit_table):
        """Test query user activity failure."""
        mock_audit_table.query.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service error"}},
            "Query",
        )

        with pytest.raises(AWSServiceError):
            audit_logger.query_user_activity(user_id="user123")

    def test_query_resource_access(self, audit_logger, mock_audit_table):
        """Test querying resource access."""
        mock_audit_table.query.return_value = [
            {
                "event_id": "event1",
                "event_type": "content.viewed",
                "resource_type": "content",
                "resource_id": "content456",
            },
        ]

        results = audit_logger.query_resource_access(
            resource_type="content",
            resource_id="content456",
            limit=50,
        )

        assert len(results) == 1
        assert results[0]["resource_id"] == "content456"
        mock_audit_table.query.assert_called_once()

    def test_query_resource_access_failure(self, audit_logger, mock_audit_table):
        """Test query resource access failure."""
        mock_audit_table.query.side_effect = ClientError(
            {"Error": {"Code": "ServiceUnavailable", "Message": "Service error"}},
            "Query",
        )

        with pytest.raises(AWSServiceError):
            audit_logger.query_resource_access(
                resource_type="content",
                resource_id="content456",
            )


class TestAuditEventTypes:
    """Test audit event type enumerations."""

    def test_authentication_event_types(self):
        """Test authentication event types exist."""
        assert AuditEventType.USER_LOGIN.value == "user.login"
        assert AuditEventType.USER_LOGOUT.value == "user.logout"
        assert AuditEventType.USER_LOGIN_FAILED.value == "user.login.failed"
        assert AuditEventType.MFA_ENABLED.value == "user.mfa.enabled"

    def test_content_event_types(self):
        """Test content event types exist."""
        assert AuditEventType.CONTENT_UPLOADED.value == "content.uploaded"
        assert AuditEventType.CONTENT_VIEWED.value == "content.viewed"
        assert AuditEventType.CONTENT_DELETED.value == "content.deleted"

    def test_privacy_event_types(self):
        """Test privacy event types exist."""
        assert AuditEventType.CONSENT_GRANTED.value == "consent.granted"
        assert AuditEventType.CONSENT_REVOKED.value == "consent.revoked"
        assert AuditEventType.DATA_DELETION_REQUESTED.value == "data.deletion.requested"

    def test_access_control_event_types(self):
        """Test access control event types exist."""
        assert AuditEventType.ACCESS_GRANTED.value == "access.granted"
        assert AuditEventType.ACCESS_DENIED.value == "access.denied"
