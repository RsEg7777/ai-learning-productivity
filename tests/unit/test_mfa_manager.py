"""Unit tests for MFA manager."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from botocore.exceptions import ClientError

from src.services.user_management import MFAManager
from src.shared.utils.errors import ValidationError, AWSServiceError


@pytest.fixture
def mock_cognito_client():
    """Mock Cognito client."""
    return Mock()


@pytest.fixture
def mock_mfa_table():
    """Mock MFA DynamoDB table."""
    return Mock()


@pytest.fixture
def mfa_manager(mock_cognito_client, mock_mfa_table):
    """Create MFA manager with mocked dependencies."""
    return MFAManager(
        cognito_client=mock_cognito_client,
        mfa_table=mock_mfa_table,
        code_expiry_minutes=5,
    )


class TestMFAEnableDisable:
    """Tests for enabling and disabling MFA."""

    def test_enable_mfa_success(
        self,
        mfa_manager,
        mock_cognito_client,
        mock_mfa_table,
    ):
        """Test successful MFA enablement."""
        # Enable MFA
        mfa_manager.enable_mfa(
            user_id="test-user-id-123",
            access_token="access-token-123",
            phone_number="+1234567890",
        )

        # Verify Cognito was called
        mock_cognito_client.update_user_attributes.assert_called_once()
        call_args = mock_cognito_client.update_user_attributes.call_args
        assert call_args.kwargs["access_token"] == "access-token-123"
        assert call_args.kwargs["attributes"]["phone_number"] == "+1234567890"

        # Verify database was updated
        mock_mfa_table.put_item.assert_called_once()
        call_args = mock_mfa_table.put_item.call_args
        mfa_data = call_args.args[0]
        assert mfa_data["user_id"] == "test-user-id-123"
        assert mfa_data["mfa_enabled"] is True
        assert mfa_data["phone_number"] == "+1234567890"

    def test_enable_mfa_invalid_phone_format(
        self,
        mfa_manager,
        mock_cognito_client,
    ):
        """Test MFA enablement with invalid phone format."""
        with pytest.raises(ValidationError) as exc_info:
            mfa_manager.enable_mfa(
                user_id="test-user-id-123",
                access_token="access-token-123",
                phone_number="1234567890",  # Missing + prefix
            )

        assert "E.164" in str(exc_info.value.message)
        assert exc_info.value.details.get("field") == "phone_number"

    def test_disable_mfa_success(self, mfa_manager, mock_mfa_table):
        """Test successful MFA disablement."""
        mfa_manager.disable_mfa(user_id="test-user-id-123")

        # Verify database was updated
        mock_mfa_table.update_item.assert_called_once()
        call_args = mock_mfa_table.update_item.call_args
        assert call_args.kwargs["key"] == {"user_id": "test-user-id-123"}
        assert call_args.kwargs["expression_values"][":enabled"] is False

    def test_is_mfa_enabled_true(self, mfa_manager, mock_mfa_table):
        """Test checking MFA status when enabled."""
        mock_mfa_table.get_item.return_value = {
            "user_id": "test-user-id-123",
            "mfa_enabled": True,
        }

        is_enabled = mfa_manager.is_mfa_enabled("test-user-id-123")

        assert is_enabled is True

    def test_is_mfa_enabled_false(self, mfa_manager, mock_mfa_table):
        """Test checking MFA status when disabled."""
        mock_mfa_table.get_item.return_value = {
            "user_id": "test-user-id-123",
            "mfa_enabled": False,
        }

        is_enabled = mfa_manager.is_mfa_enabled("test-user-id-123")

        assert is_enabled is False

    def test_is_mfa_enabled_no_record(self, mfa_manager, mock_mfa_table):
        """Test checking MFA status when no record exists."""
        mock_mfa_table.get_item.return_value = None

        is_enabled = mfa_manager.is_mfa_enabled("test-user-id-123")

        assert is_enabled is False


class TestBackupCodes:
    """Tests for backup code generation and verification."""

    def test_generate_backup_codes_default_count(
        self,
        mfa_manager,
        mock_mfa_table,
    ):
        """Test generating default number of backup codes."""
        codes = mfa_manager.generate_backup_codes(user_id="test-user-id-123")

        # Verify 10 codes generated
        assert len(codes) == 10
        
        # Verify all codes are unique
        assert len(set(codes)) == 10

        # Verify codes are uppercase hex strings
        for code in codes:
            assert isinstance(code, str)
            assert len(code) == 8
            assert all(c in "0123456789ABCDEF" for c in code)

        # Verify database was updated
        mock_mfa_table.update_item.assert_called_once()

    def test_generate_backup_codes_custom_count(
        self,
        mfa_manager,
        mock_mfa_table,
    ):
        """Test generating custom number of backup codes."""
        codes = mfa_manager.generate_backup_codes(
            user_id="test-user-id-123",
            count=5,
        )

        assert len(codes) == 5

    def test_verify_backup_code_valid(self, mfa_manager, mock_mfa_table):
        """Test verifying valid backup code."""
        # Generate a code and its hash
        test_code = "ABCD1234"
        hashed_code = mfa_manager._hash_code(test_code)

        # Mock database response
        mock_mfa_table.get_item.return_value = {
            "user_id": "test-user-id-123",
            "backup_codes": [hashed_code, "other-hash-1", "other-hash-2"],
        }

        # Verify code
        is_valid = mfa_manager.verify_backup_code(
            user_id="test-user-id-123",
            code=test_code,
        )

        assert is_valid is True

        # Verify code was removed from database
        mock_mfa_table.update_item.assert_called_once()
        call_args = mock_mfa_table.update_item.call_args
        updated_codes = call_args.kwargs["expression_values"][":codes"]
        assert hashed_code not in updated_codes
        assert len(updated_codes) == 2

    def test_verify_backup_code_invalid(self, mfa_manager, mock_mfa_table):
        """Test verifying invalid backup code."""
        mock_mfa_table.get_item.return_value = {
            "user_id": "test-user-id-123",
            "backup_codes": ["hash-1", "hash-2"],
        }

        is_valid = mfa_manager.verify_backup_code(
            user_id="test-user-id-123",
            code="INVALID",
        )

        assert is_valid is False
        mock_mfa_table.update_item.assert_not_called()

    def test_verify_backup_code_no_codes(self, mfa_manager, mock_mfa_table):
        """Test verifying backup code when no codes exist."""
        mock_mfa_table.get_item.return_value = {
            "user_id": "test-user-id-123",
        }

        is_valid = mfa_manager.verify_backup_code(
            user_id="test-user-id-123",
            code="ABCD1234",
        )

        assert is_valid is False


class TestVerificationCodes:
    """Tests for verification code generation and verification."""

    def test_send_verification_code(self, mfa_manager, mock_mfa_table):
        """Test sending verification code."""
        code_id = mfa_manager.send_verification_code(
            user_id="test-user-id-123",
            phone_number="+1234567890",
        )

        # Verify code ID is generated
        assert code_id is not None
        assert len(code_id) > 0

        # Verify database was called
        mock_mfa_table.put_item.assert_called_once()
        call_args = mock_mfa_table.put_item.call_args
        code_data = call_args.args[0]

        assert code_data["code_id"] == code_id
        assert code_data["user_id"] == "test-user-id-123"
        assert code_data["phone_number"] == "+1234567890"
        assert code_data["verified"] is False
        assert "code" in code_data
        assert "expires_at" in code_data

    def test_verify_code_valid(self, mfa_manager, mock_mfa_table):
        """Test verifying valid verification code."""
        # Generate a code and its hash
        test_code = "123456"
        hashed_code = mfa_manager._hash_code(test_code)

        # Mock database response
        now = datetime.utcnow()
        mock_mfa_table.get_item.return_value = {
            "code_id": "code-123",
            "user_id": "test-user-id-123",
            "code": hashed_code,
            "verified": False,
            "expires_at": (now + timedelta(minutes=5)).isoformat(),
        }

        # Verify code
        is_valid = mfa_manager.verify_code(
            code_id="code-123",
            code=test_code,
        )

        assert is_valid is True

        # Verify code was marked as verified
        mock_mfa_table.update_item.assert_called_once()
        call_args = mock_mfa_table.update_item.call_args
        assert call_args.kwargs["expression_values"][":verified"] is True

    def test_verify_code_invalid(self, mfa_manager, mock_mfa_table):
        """Test verifying invalid verification code."""
        now = datetime.utcnow()
        mock_mfa_table.get_item.return_value = {
            "code_id": "code-123",
            "code": "wrong-hash",
            "verified": False,
            "expires_at": (now + timedelta(minutes=5)).isoformat(),
        }

        is_valid = mfa_manager.verify_code(
            code_id="code-123",
            code="123456",
        )

        assert is_valid is False
        mock_mfa_table.update_item.assert_not_called()

    def test_verify_code_expired(self, mfa_manager, mock_mfa_table):
        """Test verifying expired verification code."""
        test_code = "123456"
        hashed_code = mfa_manager._hash_code(test_code)

        # Mock database response with expired code
        now = datetime.utcnow()
        mock_mfa_table.get_item.return_value = {
            "code_id": "code-123",
            "code": hashed_code,
            "verified": False,
            "expires_at": (now - timedelta(minutes=1)).isoformat(),
        }

        is_valid = mfa_manager.verify_code(
            code_id="code-123",
            code=test_code,
        )

        assert is_valid is False

    def test_verify_code_already_used(self, mfa_manager, mock_mfa_table):
        """Test verifying already used verification code."""
        test_code = "123456"
        hashed_code = mfa_manager._hash_code(test_code)

        now = datetime.utcnow()
        mock_mfa_table.get_item.return_value = {
            "code_id": "code-123",
            "code": hashed_code,
            "verified": True,  # Already verified
            "expires_at": (now + timedelta(minutes=5)).isoformat(),
        }

        is_valid = mfa_manager.verify_code(
            code_id="code-123",
            code=test_code,
        )

        assert is_valid is False


class TestCodeGeneration:
    """Tests for code generation utilities."""

    def test_generate_verification_code_format(self, mfa_manager):
        """Test verification code format."""
        code = mfa_manager._generate_verification_code()

        # Should be 6-digit string
        assert isinstance(code, str)
        assert len(code) == 6
        assert code.isdigit()

    def test_generate_verification_code_unique(self, mfa_manager):
        """Test that verification codes are unique."""
        codes = set()
        
        for _ in range(100):
            code = mfa_manager._generate_verification_code()
            codes.add(code)

        # Should have high uniqueness (allow some collisions due to randomness)
        assert len(codes) > 90

    def test_generate_backup_code_format(self, mfa_manager):
        """Test backup code format."""
        code = mfa_manager._generate_backup_code()

        # Should be 8-character uppercase hex string
        assert isinstance(code, str)
        assert len(code) == 8
        assert all(c in "0123456789ABCDEF" for c in code)

    def test_hash_code_consistency(self, mfa_manager):
        """Test that code hashing is consistent."""
        code = "123456"
        
        hash1 = mfa_manager._hash_code(code)
        hash2 = mfa_manager._hash_code(code)

        assert hash1 == hash2

    def test_hash_code_different_inputs(self, mfa_manager):
        """Test that different codes produce different hashes."""
        hash1 = mfa_manager._hash_code("123456")
        hash2 = mfa_manager._hash_code("654321")

        assert hash1 != hash2
