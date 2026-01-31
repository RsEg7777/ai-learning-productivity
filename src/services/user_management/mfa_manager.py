"""Multi-factor authentication manager."""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError

from src.shared.aws_clients.cognito_client import CognitoClient
from src.shared.aws_clients.dynamodb_client import DynamoDBClient
from src.shared.utils.errors import AuthenticationError, ValidationError, AWSServiceError

logger = logging.getLogger(__name__)


class MFAManager:
    """Manager for multi-factor authentication operations."""

    def __init__(
        self,
        cognito_client: CognitoClient,
        mfa_table: DynamoDBClient,
        code_expiry_minutes: int = 5,
    ) -> None:
        """
        Initialize MFA manager.

        Args:
            cognito_client: Cognito client for MFA operations
            mfa_table: DynamoDB table for MFA code storage
            code_expiry_minutes: MFA code expiry time in minutes
        """
        self.cognito = cognito_client
        self.mfa_table = mfa_table
        self.code_expiry = timedelta(minutes=code_expiry_minutes)
        logger.info("Initialized MFAManager")

    def enable_mfa(self, user_id: str, access_token: str, phone_number: str) -> None:
        """
        Enable MFA for a user.

        Args:
            user_id: User identifier
            access_token: User's access token
            phone_number: Phone number for SMS MFA

        Raises:
            ValidationError: If phone number is invalid
            AWSServiceError: If MFA setup fails
        """
        try:
            # Validate phone number format (E.164 format)
            if not phone_number.startswith("+"):
                raise ValidationError(
                    message="Phone number must be in E.164 format (e.g., +1234567890)",
                    field="phone_number",
                )

            # Update user attributes with phone number
            self.cognito.update_user_attributes(
                access_token=access_token,
                attributes={"phone_number": phone_number},
            )

            # Store MFA preference
            self.mfa_table.put_item({
                "user_id": user_id,
                "mfa_enabled": True,
                "phone_number": phone_number,
                "enabled_at": datetime.utcnow().isoformat(),
            })

            logger.info(f"Enabled MFA for user: {user_id}")

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to enable MFA: {str(e)}",
                service="Cognito",
                operation="update_user_attributes",
            )

    def disable_mfa(self, user_id: str) -> None:
        """
        Disable MFA for a user.

        Args:
            user_id: User identifier

        Raises:
            AWSServiceError: If MFA disable fails
        """
        try:
            self.mfa_table.update_item(
                key={"user_id": user_id},
                update_expression="SET mfa_enabled = :enabled",
                expression_values={":enabled": False},
            )
            logger.info(f"Disabled MFA for user: {user_id}")

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to disable MFA: {str(e)}",
                service="DynamoDB",
                operation="update_item",
            )

    def is_mfa_enabled(self, user_id: str) -> bool:
        """
        Check if MFA is enabled for a user.

        Args:
            user_id: User identifier

        Returns:
            True if MFA is enabled, False otherwise
        """
        try:
            item = self.mfa_table.get_item({"user_id": user_id})
            return item.get("mfa_enabled", False) if item else False

        except ClientError as e:
            logger.error(f"Failed to check MFA status: {e}")
            return False

    def generate_backup_codes(self, user_id: str, count: int = 10) -> list[str]:
        """
        Generate backup codes for MFA recovery.

        Args:
            user_id: User identifier
            count: Number of backup codes to generate

        Returns:
            List of backup codes

        Raises:
            AWSServiceError: If code generation fails
        """
        try:
            # Generate secure random codes
            codes = [self._generate_backup_code() for _ in range(count)]

            # Store hashed codes in database
            self.mfa_table.update_item(
                key={"user_id": user_id},
                update_expression="SET backup_codes = :codes, codes_generated_at = :timestamp",
                expression_values={
                    ":codes": [self._hash_code(code) for code in codes],
                    ":timestamp": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Generated {count} backup codes for user: {user_id}")
            return codes

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to generate backup codes: {str(e)}",
                service="DynamoDB",
                operation="update_item",
            )

    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """
        Verify a backup code and mark it as used.

        Args:
            user_id: User identifier
            code: Backup code to verify

        Returns:
            True if code is valid, False otherwise

        Raises:
            AWSServiceError: If verification fails
        """
        try:
            item = self.mfa_table.get_item({"user_id": user_id})
            if not item or "backup_codes" not in item:
                return False

            hashed_code = self._hash_code(code)
            backup_codes = item.get("backup_codes", [])

            if hashed_code in backup_codes:
                # Remove used code
                backup_codes.remove(hashed_code)
                self.mfa_table.update_item(
                    key={"user_id": user_id},
                    update_expression="SET backup_codes = :codes",
                    expression_values={":codes": backup_codes},
                )
                logger.info(f"Verified backup code for user: {user_id}")
                return True

            return False

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to verify backup code: {str(e)}",
                service="DynamoDB",
                operation="get_item",
            )

    def send_verification_code(self, user_id: str, phone_number: str) -> str:
        """
        Send a verification code via SMS (simulated for development).

        Args:
            user_id: User identifier
            phone_number: Phone number to send code to

        Returns:
            Verification code ID

        Raises:
            AWSServiceError: If sending fails
        """
        try:
            # Generate verification code
            code = self._generate_verification_code()
            code_id = secrets.token_urlsafe(16)

            # Store code in database
            self.mfa_table.put_item({
                "code_id": code_id,
                "user_id": user_id,
                "code": self._hash_code(code),
                "phone_number": phone_number,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + self.code_expiry).isoformat(),
                "verified": False,
            })

            # In production, this would send SMS via SNS
            logger.info(f"Generated verification code for user: {user_id}")
            logger.debug(f"Verification code (dev only): {code}")

            return code_id

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to send verification code: {str(e)}",
                service="DynamoDB",
                operation="put_item",
            )

    def verify_code(self, code_id: str, code: str) -> bool:
        """
        Verify a verification code.

        Args:
            code_id: Code identifier
            code: Verification code

        Returns:
            True if code is valid, False otherwise

        Raises:
            AWSServiceError: If verification fails
        """
        try:
            item = self.mfa_table.get_item({"code_id": code_id})
            if not item:
                return False

            # Check if already verified
            if item.get("verified", False):
                logger.warning(f"Code {code_id} already used")
                return False

            # Check expiration
            expires_at = datetime.fromisoformat(item["expires_at"])
            if datetime.utcnow() > expires_at:
                logger.warning(f"Code {code_id} has expired")
                return False

            # Verify code
            hashed_code = self._hash_code(code)
            if hashed_code == item.get("code"):
                # Mark as verified
                self.mfa_table.update_item(
                    key={"code_id": code_id},
                    update_expression="SET verified = :verified",
                    expression_values={":verified": True},
                )
                logger.info(f"Verified code: {code_id}")
                return True

            return False

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to verify code: {str(e)}",
                service="DynamoDB",
                operation="get_item",
            )

    @staticmethod
    def _generate_verification_code() -> str:
        """
        Generate a 6-digit verification code.

        Returns:
            Verification code
        """
        return f"{secrets.randbelow(1000000):06d}"

    @staticmethod
    def _generate_backup_code() -> str:
        """
        Generate a backup code.

        Returns:
            Backup code (8 characters)
        """
        return secrets.token_hex(4).upper()

    @staticmethod
    def _hash_code(code: str) -> str:
        """
        Hash a code for secure storage.

        Args:
            code: Code to hash

        Returns:
            Hashed code
        """
        import hashlib
        return hashlib.sha256(code.encode()).hexdigest()
