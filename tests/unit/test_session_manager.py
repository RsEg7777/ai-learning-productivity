"""Unit tests for session manager."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from botocore.exceptions import ClientError

from src.services.user_management import SessionManager
from src.shared.utils.errors import AuthenticationError, AWSServiceError


@pytest.fixture
def mock_session_table():
    """Mock session DynamoDB table."""
    return Mock()


@pytest.fixture
def session_manager(mock_session_table):
    """Create session manager with mocked dependencies."""
    return SessionManager(
        session_table=mock_session_table,
        session_timeout_minutes=60,
        refresh_timeout_days=30,
    )


class TestSessionCreation:
    """Tests for session creation."""

    def test_create_session_success(self, session_manager, mock_session_table):
        """Test successful session creation."""
        # Create session
        session_id = session_manager.create_session(
            user_id="test-user-id-123",
            access_token="access-token-123",
            refresh_token="refresh-token-456",
            metadata={"ip": "192.168.1.1"},
        )

        # Verify session ID is generated
        assert session_id is not None
        assert len(session_id) > 0

        # Verify database was called
        mock_session_table.put_item.assert_called_once()
        call_args = mock_session_table.put_item.call_args
        session_data = call_args.args[0]

        assert session_data["session_id"] == session_id
        assert session_data["user_id"] == "test-user-id-123"
        assert session_data["access_token"] == "access-token-123"
        assert session_data["refresh_token"] == "refresh-token-456"
        assert session_data["is_active"] is True
        assert session_data["metadata"]["ip"] == "192.168.1.1"

    def test_create_session_without_refresh_token(
        self,
        session_manager,
        mock_session_table,
    ):
        """Test session creation without refresh token."""
        session_id = session_manager.create_session(
            user_id="test-user-id-123",
            access_token="access-token-123",
        )

        assert session_id is not None
        mock_session_table.put_item.assert_called_once()


class TestSessionRetrieval:
    """Tests for session retrieval."""

    def test_get_session_success(self, session_manager, mock_session_table):
        """Test getting valid session."""
        # Mock database response
        now = datetime.utcnow()
        mock_session_table.get_item.return_value = {
            "session_id": "session-123",
            "user_id": "test-user-id-123",
            "access_token": "access-token-123",
            "is_active": True,
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "last_activity": now.isoformat(),
        }

        # Get session
        session = session_manager.get_session("session-123")

        # Verify session
        assert session is not None
        assert session["session_id"] == "session-123"
        assert session["user_id"] == "test-user-id-123"
        assert session["is_active"] is True

    def test_get_session_not_found(self, session_manager, mock_session_table):
        """Test getting non-existent session."""
        mock_session_table.get_item.return_value = None

        session = session_manager.get_session("non-existent-session")

        assert session is None

    def test_get_session_inactive(self, session_manager, mock_session_table):
        """Test getting inactive session."""
        now = datetime.utcnow()
        mock_session_table.get_item.return_value = {
            "session_id": "session-123",
            "user_id": "test-user-id-123",
            "is_active": False,
            "expires_at": (now + timedelta(hours=1)).isoformat(),
        }

        session = session_manager.get_session("session-123")

        assert session is None

    def test_get_session_expired(self, session_manager, mock_session_table):
        """Test getting expired session."""
        now = datetime.utcnow()
        mock_session_table.get_item.return_value = {
            "session_id": "session-123",
            "user_id": "test-user-id-123",
            "is_active": True,
            "expires_at": (now - timedelta(hours=1)).isoformat(),
        }

        session = session_manager.get_session("session-123")

        assert session is None
        # Verify session was invalidated
        mock_session_table.update_item.assert_called_once()


class TestSessionValidation:
    """Tests for session validation."""

    def test_validate_session_valid(self, session_manager, mock_session_table):
        """Test validating valid session."""
        now = datetime.utcnow()
        mock_session_table.get_item.return_value = {
            "session_id": "session-123",
            "user_id": "test-user-id-123",
            "is_active": True,
            "expires_at": (now + timedelta(hours=1)).isoformat(),
        }

        is_valid = session_manager.validate_session("session-123")

        assert is_valid is True

    def test_validate_session_invalid(self, session_manager, mock_session_table):
        """Test validating invalid session."""
        mock_session_table.get_item.return_value = None

        is_valid = session_manager.validate_session("invalid-session")

        assert is_valid is False


class TestSessionRefresh:
    """Tests for session refresh."""

    def test_refresh_session_success(self, session_manager, mock_session_table):
        """Test successful session refresh."""
        now = datetime.utcnow()
        mock_session_table.get_item.return_value = {
            "session_id": "session-123",
            "user_id": "test-user-id-123",
            "is_active": True,
            "expires_at": (now + timedelta(minutes=30)).isoformat(),
        }

        # Refresh session
        session_manager.refresh_session("session-123")

        # Verify database was updated
        mock_session_table.update_item.assert_called_once()
        call_args = mock_session_table.update_item.call_args
        assert call_args.kwargs["key"] == {"session_id": "session-123"}

    def test_refresh_session_invalid(self, session_manager, mock_session_table):
        """Test refreshing invalid session."""
        mock_session_table.get_item.return_value = None

        with pytest.raises(AuthenticationError):
            session_manager.refresh_session("invalid-session")


class TestSessionInvalidation:
    """Tests for session invalidation."""

    def test_invalidate_session_success(self, session_manager, mock_session_table):
        """Test successful session invalidation."""
        session_manager.invalidate_session("session-123")

        # Verify database was updated
        mock_session_table.update_item.assert_called_once()
        call_args = mock_session_table.update_item.call_args
        assert call_args.kwargs["key"] == {"session_id": "session-123"}
        assert call_args.kwargs["expression_values"][":active"] is False

    def test_invalidate_user_sessions_success(
        self,
        session_manager,
        mock_session_table,
    ):
        """Test invalidating all user sessions."""
        # Mock query response
        mock_session_table.query.return_value = [
            {"session_id": "session-1"},
            {"session_id": "session-2"},
            {"session_id": "session-3"},
        ]

        # Invalidate all sessions
        session_manager.invalidate_user_sessions("test-user-id-123")

        # Verify query was called
        mock_session_table.query.assert_called_once()

        # Verify all sessions were invalidated
        assert mock_session_table.update_item.call_count == 3


class TestSessionCleanup:
    """Tests for session cleanup."""

    def test_cleanup_expired_sessions(self, session_manager, mock_session_table):
        """Test cleaning up expired sessions."""
        now = datetime.utcnow()
        
        # Mock scan response with expired sessions
        mock_session_table.scan.return_value = [
            {"session_id": "expired-1"},
            {"session_id": "expired-2"},
            {"session_id": "inactive-1"},
        ]

        # Cleanup sessions
        count = session_manager.cleanup_expired_sessions()

        # Verify cleanup
        assert count == 3
        mock_session_table.scan.assert_called_once()
        assert mock_session_table.delete_item.call_count == 3

    def test_cleanup_no_expired_sessions(self, session_manager, mock_session_table):
        """Test cleanup when no expired sessions exist."""
        mock_session_table.scan.return_value = []

        count = session_manager.cleanup_expired_sessions()

        assert count == 0
        mock_session_table.delete_item.assert_not_called()


class TestSessionIDGeneration:
    """Tests for session ID generation."""

    def test_generate_unique_session_ids(self, session_manager):
        """Test that generated session IDs are unique."""
        session_ids = set()
        
        for _ in range(100):
            session_id = session_manager._generate_session_id()
            assert session_id not in session_ids
            session_ids.add(session_id)

        assert len(session_ids) == 100

    def test_session_id_format(self, session_manager):
        """Test session ID format."""
        session_id = session_manager._generate_session_id()
        
        # Should be URL-safe base64 string
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        # URL-safe characters only
        assert all(c.isalnum() or c in "-_" for c in session_id)
