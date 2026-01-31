"""Unit tests for user management service."""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from botocore.exceptions import ClientError

from src.services.user_management import UserService
from src.shared.models.user import (
    User,
    UserRegistration,
    LoginCredentials,
    UserPreferences,
    LearningProgress,
)
from src.shared.utils.errors import (
    AuthenticationError,
    ValidationError,
    AWSServiceError,
)


@pytest.fixture
def mock_cognito_client():
    """Mock Cognito client."""
    return Mock()


@pytest.fixture
def mock_user_table():
    """Mock user DynamoDB table."""
    return Mock()


@pytest.fixture
def mock_progress_table():
    """Mock progress DynamoDB table."""
    return Mock()


@pytest.fixture
def user_service(mock_cognito_client, mock_user_table, mock_progress_table):
    """Create user service with mocked dependencies."""
    return UserService(
        cognito_client=mock_cognito_client,
        user_table=mock_user_table,
        progress_table=mock_progress_table,
    )


@pytest.fixture
def sample_registration():
    """Sample user registration data."""
    return UserRegistration(
        email="test@example.com",
        password="SecurePass123!",
        username="testuser",
        full_name="Test User",
        preferred_language="en",
    )


class TestUserRegistration:
    """Tests for user registration."""

    def test_register_user_success(
        self,
        user_service,
        mock_cognito_client,
        mock_user_table,
        mock_progress_table,
        sample_registration,
    ):
        """Test successful user registration."""
        # Mock Cognito response
        mock_cognito_client.sign_up.return_value = {
            "UserSub": "test-user-id-123",
        }

        # Register user
        user = user_service.register_user(sample_registration)

        # Verify Cognito was called
        mock_cognito_client.sign_up.assert_called_once()
        call_args = mock_cognito_client.sign_up.call_args
        assert call_args.kwargs["username"] == sample_registration.email
        assert call_args.kwargs["email"] == sample_registration.email

        # Verify user profile was created
        assert user.id == "test-user-id-123"
        assert user.email == sample_registration.email
        assert user.username == sample_registration.username
        assert user.preferences.language == "en"

        # Verify database calls
        mock_user_table.put_item.assert_called_once()
        mock_progress_table.put_item.assert_called_once()

    def test_register_user_duplicate_email(
        self,
        user_service,
        mock_cognito_client,
        sample_registration,
    ):
        """Test registration with duplicate email."""
        # Mock Cognito error
        error_response = {
            "Error": {
                "Code": "UsernameExistsException",
                "Message": "User already exists",
            }
        }
        mock_cognito_client.sign_up.side_effect = ClientError(
            error_response, "SignUp"
        )

        # Attempt registration
        with pytest.raises(ValidationError) as exc_info:
            user_service.register_user(sample_registration)

        assert "already exists" in str(exc_info.value.message).lower()
        assert exc_info.value.details.get("field") == "email"

    def test_register_user_invalid_password(
        self,
        user_service,
        mock_cognito_client,
        sample_registration,
    ):
        """Test registration with invalid password."""
        # Mock Cognito error
        error_response = {
            "Error": {
                "Code": "InvalidPasswordException",
                "Message": "Password does not meet requirements",
            }
        }
        mock_cognito_client.sign_up.side_effect = ClientError(
            error_response, "SignUp"
        )

        # Attempt registration
        with pytest.raises(ValidationError) as exc_info:
            user_service.register_user(sample_registration)

        assert "password" in str(exc_info.value.message).lower()
        assert exc_info.value.details.get("field") == "password"


class TestUserAuthentication:
    """Tests for user authentication."""

    def test_authenticate_user_success(
        self,
        user_service,
        mock_cognito_client,
        mock_user_table,
    ):
        """Test successful user authentication."""
        credentials = LoginCredentials(
            email="test@example.com",
            password="SecurePass123!",
        )

        # Mock Cognito responses
        mock_cognito_client.initiate_auth.return_value = {
            "AuthenticationResult": {
                "AccessToken": "access-token-123",
                "RefreshToken": "refresh-token-456",
                "ExpiresIn": 3600,
            }
        }
        mock_cognito_client.get_user.return_value = {
            "Username": "test-user-id-123",
        }

        # Authenticate
        result = user_service.authenticate_user(credentials)

        # Verify result
        assert result.success is True
        assert result.user_id == "test-user-id-123"
        assert result.access_token == "access-token-123"
        assert result.refresh_token == "refresh-token-456"
        assert result.expires_in == 3600
        assert result.requires_mfa is False

        # Verify Cognito was called
        mock_cognito_client.initiate_auth.assert_called_once()
        mock_cognito_client.get_user.assert_called_once_with("access-token-123")

    def test_authenticate_user_mfa_required(
        self,
        user_service,
        mock_cognito_client,
    ):
        """Test authentication when MFA is required."""
        credentials = LoginCredentials(
            email="test@example.com",
            password="SecurePass123!",
        )

        # Mock Cognito response with MFA challenge
        mock_cognito_client.initiate_auth.return_value = {
            "ChallengeName": "SMS_MFA",
            "Session": "mfa-session-123",
        }

        # Authenticate
        result = user_service.authenticate_user(credentials)

        # Verify MFA is required
        assert result.success is False
        assert result.requires_mfa is True
        assert "MFA" in result.error_message

    def test_authenticate_user_invalid_credentials(
        self,
        user_service,
        mock_cognito_client,
    ):
        """Test authentication with invalid credentials."""
        credentials = LoginCredentials(
            email="test@example.com",
            password="WrongPassword",
        )

        # Mock Cognito error
        error_response = {
            "Error": {
                "Code": "NotAuthorizedException",
                "Message": "Incorrect username or password",
            }
        }
        mock_cognito_client.initiate_auth.side_effect = ClientError(
            error_response, "InitiateAuth"
        )

        # Attempt authentication
        with pytest.raises(AuthenticationError) as exc_info:
            user_service.authenticate_user(credentials)

        assert "invalid" in str(exc_info.value.message).lower()

    def test_verify_mfa_success(
        self,
        user_service,
        mock_cognito_client,
        mock_user_table,
    ):
        """Test successful MFA verification."""
        # Mock Cognito responses
        mock_cognito_client.respond_to_auth_challenge.return_value = {
            "AuthenticationResult": {
                "AccessToken": "access-token-123",
                "RefreshToken": "refresh-token-456",
                "ExpiresIn": 3600,
            }
        }
        mock_cognito_client.get_user.return_value = {
            "Username": "test-user-id-123",
        }

        # Verify MFA
        result = user_service.verify_mfa(
            session="mfa-session-123",
            mfa_code="123456",
            username="test@example.com",
        )

        # Verify result
        assert result.success is True
        assert result.user_id == "test-user-id-123"
        assert result.access_token == "access-token-123"


class TestUserProfile:
    """Tests for user profile management."""

    def test_get_user_success(self, user_service, mock_user_table):
        """Test getting user profile."""
        # Mock database response
        mock_user_table.get_item.return_value = {
            "id": "test-user-id-123",
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "preferences": {
                "language": "en",
                "voice_enabled": False,
                "theme": "light",
                "notification_enabled": True,
                "spaced_repetition_enabled": True,
                "daily_goal_minutes": 30,
            },
            "created_at": "2024-01-01T00:00:00",
            "last_active": "2024-01-01T00:00:00",
            "is_active": True,
            "metadata": {},
        }

        # Get user
        user = user_service.get_user("test-user-id-123")

        # Verify user
        assert user is not None
        assert user.id == "test-user-id-123"
        assert user.email == "test@example.com"
        assert user.username == "testuser"

    def test_get_user_not_found(self, user_service, mock_user_table):
        """Test getting non-existent user."""
        mock_user_table.get_item.return_value = None

        user = user_service.get_user("non-existent-id")

        assert user is None

    def test_update_preferences_success(self, user_service, mock_user_table):
        """Test updating user preferences."""
        preferences = UserPreferences(
            language="hi",
            voice_enabled=True,
            theme="dark",
        )

        # Update preferences
        user_service.update_preferences("test-user-id-123", preferences)

        # Verify database was called
        mock_user_table.update_item.assert_called_once()
        call_args = mock_user_table.update_item.call_args
        assert call_args.kwargs["key"] == {"id": "test-user-id-123"}


class TestLearningProgress:
    """Tests for learning progress tracking."""

    def test_get_progress_success(self, user_service, mock_progress_table):
        """Test getting learning progress."""
        # Mock database response
        mock_progress_table.get_item.return_value = {
            "user_id": "test-user-id-123",
            "total_study_time": 120,
            "content_processed": 5,
            "quizzes_completed": 3,
            "average_score": 85.5,
            "streak_days": 7,
            "achievements": [],
            "last_active": "2024-01-01T00:00:00",
        }

        # Get progress
        progress = user_service.get_progress("test-user-id-123")

        # Verify progress
        assert progress is not None
        assert progress.user_id == "test-user-id-123"
        assert progress.total_study_time == 120
        assert progress.quizzes_completed == 3
        assert progress.average_score == 85.5

    def test_update_progress_study_time(
        self,
        user_service,
        mock_progress_table,
    ):
        """Test updating study time."""
        # Mock existing progress
        mock_progress_table.get_item.return_value = {
            "user_id": "test-user-id-123",
            "total_study_time": 100,
            "content_processed": 5,
            "quizzes_completed": 3,
            "average_score": 85.0,
            "streak_days": 7,
            "achievements": [],
            "last_active": "2024-01-01T00:00:00",
        }

        # Update progress
        user_service.update_progress(
            user_id="test-user-id-123",
            study_time_minutes=30,
        )

        # Verify database was called
        mock_progress_table.update_item.assert_called_once()

    def test_update_progress_quiz_score(
        self,
        user_service,
        mock_progress_table,
    ):
        """Test updating quiz score and calculating average."""
        # Mock existing progress
        mock_progress_table.get_item.return_value = {
            "user_id": "test-user-id-123",
            "total_study_time": 100,
            "content_processed": 5,
            "quizzes_completed": 2,
            "average_score": 80.0,
            "streak_days": 7,
            "achievements": [],
            "last_active": "2024-01-01T00:00:00",
        }

        # Update progress with new quiz score
        user_service.update_progress(
            user_id="test-user-id-123",
            quiz_completed=True,
            quiz_score=90.0,
        )

        # Verify database was called
        mock_progress_table.update_item.assert_called_once()
        call_args = mock_progress_table.update_item.call_args
        
        # Verify average score calculation
        # (80 * 2 + 90) / 3 = 83.33
        assert ":avg_score" in call_args.kwargs["expression_values"]
        avg_score = call_args.kwargs["expression_values"][":avg_score"]
        assert abs(avg_score - 83.33) < 0.01


class TestUserDataDeletion:
    """Tests for user data deletion."""

    def test_delete_user_data_success(
        self,
        user_service,
        mock_cognito_client,
        mock_user_table,
        mock_progress_table,
    ):
        """Test successful user data deletion."""
        # Delete user data
        user_service.delete_user_data(
            user_id="test-user-id-123",
            access_token="access-token-123",
        )

        # Verify all deletions
        mock_cognito_client.delete_user.assert_called_once_with("access-token-123")
        mock_user_table.delete_item.assert_called_once_with({"id": "test-user-id-123"})
        mock_progress_table.delete_item.assert_called_once_with(
            {"user_id": "test-user-id-123"}
        )
