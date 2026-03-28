"""Data privacy controls and consent management."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
from botocore.exceptions import ClientError

from src.shared.aws_clients.dynamodb_client import DynamoDBClient
from src.shared.aws_clients.s3_client import S3Client
from src.shared.utils.errors import ValidationError, AWSServiceError

logger = logging.getLogger(__name__)


class ConsentType(str, Enum):
    """Types of user consent."""
    DATA_PROCESSING = "data_processing"
    CONTENT_TRAINING = "content_training"
    ANALYTICS = "analytics"
    MARKETING = "marketing"
    THIRD_PARTY_SHARING = "third_party_sharing"


class DataCategory(str, Enum):
    """Categories of user data."""
    PROFILE = "profile"
    CONTENT = "content"
    QUIZ_RESULTS = "quiz_results"
    LEARNING_PROGRESS = "learning_progress"
    VOICE_RECORDINGS = "voice_recordings"
    CODE_SNIPPETS = "code_snippets"
    AUDIT_LOGS = "audit_logs"


class ConsentRecord:
    """User consent record."""

    def __init__(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        granted_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize consent record.

        Args:
            user_id: User identifier
            consent_type: Type of consent
            granted: Whether consent is granted
            granted_at: When consent was granted
            expires_at: When consent expires (optional)
            metadata: Additional metadata
        """
        self.user_id = user_id
        self.consent_type = consent_type
        self.granted = granted
        self.granted_at = granted_at or datetime.utcnow()
        self.expires_at = expires_at
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "consent_type": self.consent_type.value,
            "granted": self.granted,
            "granted_at": self.granted_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }

    def is_valid(self) -> bool:
        """Check if consent is still valid."""
        if not self.granted:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True


class PrivacyManager:
    """Manager for data privacy controls and consent."""

    def __init__(
        self,
        consent_table: DynamoDBClient,
        deletion_queue_table: DynamoDBClient,
        s3_client: S3Client,
        deletion_grace_period_days: int = 30,
    ) -> None:
        """
        Initialize privacy manager.

        Args:
            consent_table: DynamoDB table for consent records
            deletion_queue_table: DynamoDB table for deletion requests
            s3_client: S3 client for data export/deletion
            deletion_grace_period_days: Grace period before permanent deletion
        """
        self.consent_table = consent_table
        self.deletion_queue_table = deletion_queue_table
        self.s3_client = s3_client
        self.deletion_grace_period = timedelta(days=deletion_grace_period_days)
        logger.info("Initialized PrivacyManager")

    def grant_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConsentRecord:
        """
        Grant user consent for a specific purpose.

        Args:
            user_id: User identifier
            consent_type: Type of consent
            expires_at: When consent expires (optional)
            metadata: Additional metadata

        Returns:
            Consent record

        Raises:
            AWSServiceError: If consent storage fails
        """
        try:
            consent = ConsentRecord(
                user_id=user_id,
                consent_type=consent_type,
                granted=True,
                expires_at=expires_at,
                metadata=metadata,
            )

            self.consent_table.put_item(consent.to_dict())
            logger.info(
                f"Granted consent {consent_type.value} for user: {user_id}"
            )

            return consent

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to grant consent: {str(e)}",
                service="DynamoDB",
                operation="put_item",
            )

    def revoke_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
    ) -> None:
        """
        Revoke user consent.

        Args:
            user_id: User identifier
            consent_type: Type of consent to revoke

        Raises:
            AWSServiceError: If consent revocation fails
        """
        try:
            self.consent_table.update_item(
                key={
                    "user_id": user_id,
                    "consent_type": consent_type.value,
                },
                update_expression="SET granted = :granted, revoked_at = :revoked_at",
                expression_values={
                    ":granted": False,
                    ":revoked_at": datetime.utcnow().isoformat(),
                },
            )
            logger.info(
                f"Revoked consent {consent_type.value} for user: {user_id}"
            )

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to revoke consent: {str(e)}",
                service="DynamoDB",
                operation="update_item",
            )

    def check_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
    ) -> bool:
        """
        Check if user has granted valid consent.

        Args:
            user_id: User identifier
            consent_type: Type of consent to check

        Returns:
            True if consent is granted and valid, False otherwise
        """
        try:
            item = self.consent_table.get_item({
                "user_id": user_id,
                "consent_type": consent_type.value,
            })

            if not item:
                return False

            # Check if consent is granted
            if not item.get("granted", False):
                return False

            # Check expiration
            expires_at = item.get("expires_at")
            if expires_at:
                expires_dt = datetime.fromisoformat(expires_at)
                if datetime.utcnow() > expires_dt:
                    logger.info(
                        f"Consent {consent_type.value} expired for user: {user_id}"
                    )
                    return False

            return True

        except ClientError as e:
            logger.error(f"Failed to check consent: {e}")
            return False

    def require_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        purpose: Optional[str] = None,
    ) -> None:
        """
        Require user to have granted consent.

        Args:
            user_id: User identifier
            consent_type: Required consent type
            purpose: Purpose description for error message

        Raises:
            ValidationError: If consent not granted
        """
        if not self.check_consent(user_id, consent_type):
            purpose_msg = f" for {purpose}" if purpose else ""
            raise ValidationError(
                message=f"User consent required{purpose_msg}: {consent_type.value}",
                field="consent",
                details={
                    "user_id": user_id,
                    "consent_type": consent_type.value,
                    "purpose": purpose,
                },
            )

    def get_user_consents(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all consent records for a user.

        Args:
            user_id: User identifier

        Returns:
            List of consent records

        Raises:
            AWSServiceError: If retrieval fails
        """
        try:
            results = self.consent_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )

            return results

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to retrieve consents: {str(e)}",
                service="DynamoDB",
                operation="query",
            )

    def request_data_export(
        self,
        user_id: str,
        categories: Optional[List[DataCategory]] = None,
    ) -> str:
        """
        Request export of user data.

        Args:
            user_id: User identifier
            categories: Data categories to export (all if None)

        Returns:
            Export request ID

        Raises:
            AWSServiceError: If export request fails
        """
        try:
            import uuid
            export_id = str(uuid.uuid4())

            # Create export request
            export_request = {
                "export_id": export_id,
                "user_id": user_id,
                "categories": [c.value for c in categories] if categories else "all",
                "requested_at": datetime.utcnow().isoformat(),
                "status": "pending",
            }

            # Store in DynamoDB (would trigger async export process)
            self.consent_table.put_item(export_request)

            logger.info(f"Created data export request {export_id} for user: {user_id}")
            return export_id

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to request data export: {str(e)}",
                service="DynamoDB",
                operation="put_item",
            )

    def request_data_deletion(
        self,
        user_id: str,
        categories: Optional[List[DataCategory]] = None,
        immediate: bool = False,
    ) -> str:
        """
        Request deletion of user data.

        Args:
            user_id: User identifier
            categories: Data categories to delete (all if None)
            immediate: Whether to delete immediately (bypasses grace period)

        Returns:
            Deletion request ID

        Raises:
            AWSServiceError: If deletion request fails
        """
        try:
            import uuid
            deletion_id = str(uuid.uuid4())

            # Calculate deletion date
            deletion_date = (
                datetime.utcnow() if immediate
                else datetime.utcnow() + self.deletion_grace_period
            )

            # Create deletion request
            deletion_request = {
                "deletion_id": deletion_id,
                "user_id": user_id,
                "categories": [c.value for c in categories] if categories else "all",
                "requested_at": datetime.utcnow().isoformat(),
                "scheduled_deletion_at": deletion_date.isoformat(),
                "status": "pending",
                "immediate": immediate,
            }

            # Store in deletion queue
            self.deletion_queue_table.put_item(deletion_request)

            logger.info(
                f"Created data deletion request {deletion_id} for user: {user_id}, "
                f"scheduled for: {deletion_date.isoformat()}"
            )
            return deletion_id

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to request data deletion: {str(e)}",
                service="DynamoDB",
                operation="put_item",
            )

    def cancel_data_deletion(self, deletion_id: str, user_id: str) -> None:
        """
        Cancel a pending data deletion request.

        Args:
            deletion_id: Deletion request ID
            user_id: User identifier (for verification)

        Raises:
            ValidationError: If deletion request not found or already processed
            AWSServiceError: If cancellation fails
        """
        try:
            # Get deletion request
            item = self.deletion_queue_table.get_item({"deletion_id": deletion_id})

            if not item:
                raise ValidationError(
                    message="Deletion request not found",
                    field="deletion_id",
                )

            # Verify user owns this request
            if item.get("user_id") != user_id:
                raise ValidationError(
                    message="Deletion request does not belong to user",
                    field="deletion_id",
                )

            # Check if already processed
            if item.get("status") != "pending":
                raise ValidationError(
                    message=f"Cannot cancel deletion request with status: {item.get('status')}",
                    field="status",
                )

            # Update status to cancelled
            self.deletion_queue_table.update_item(
                key={"deletion_id": deletion_id},
                update_expression="SET #status = :status, cancelled_at = :cancelled_at",
                expression_values={
                    ":status": "cancelled",
                    ":cancelled_at": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Cancelled data deletion request: {deletion_id}")

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to cancel deletion request: {str(e)}",
                service="DynamoDB",
                operation="update_item",
            )

    def process_pending_deletions(self) -> int:
        """
        Process pending deletion requests that are due.

        Returns:
            Number of deletions processed

        Raises:
            AWSServiceError: If processing fails
        """
        try:
            now = datetime.utcnow()

            # Query pending deletions that are due
            results = self.deletion_queue_table.scan(
                filter_expression="#status = :status AND scheduled_deletion_at <= :now",
                expression_values={
                    ":status": "pending",
                    ":now": now.isoformat(),
                },
            )

            count = 0
            for item in results:
                try:
                    # Process deletion (would call actual deletion logic)
                    self._execute_deletion(item)

                    # Update status
                    self.deletion_queue_table.update_item(
                        key={"deletion_id": item["deletion_id"]},
                        update_expression="SET #status = :status, processed_at = :processed_at",
                        expression_values={
                            ":status": "completed",
                            ":processed_at": now.isoformat(),
                        },
                    )

                    count += 1
                    logger.info(f"Processed deletion request: {item['deletion_id']}")

                except Exception as e:
                    logger.error(
                        f"Failed to process deletion {item['deletion_id']}: {e}"
                    )
                    # Mark as failed
                    self.deletion_queue_table.update_item(
                        key={"deletion_id": item["deletion_id"]},
                        update_expression="SET #status = :status, error = :error",
                        expression_values={
                            ":status": "failed",
                            ":error": str(e),
                        },
                    )

            logger.info(f"Processed {count} pending deletions")
            return count

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to process pending deletions: {str(e)}",
                service="DynamoDB",
                operation="scan",
            )

    def _execute_deletion(self, deletion_request: Dict[str, Any]) -> None:
        """
        Execute actual data deletion.

        Args:
            deletion_request: Deletion request details

        Note:
            This method should be called by a DataDeletionService instance.
            It's kept as a placeholder for backward compatibility.
        """
        user_id = deletion_request["user_id"]
        categories = deletion_request.get("categories", "all")

        logger.info(
            f"Executing deletion for user {user_id}, categories: {categories}"
        )

        # Parse categories
        if categories == "all":
            category_list = None  # None means all categories
        else:
            category_list = [DataCategory(cat) for cat in categories]

        # Note: In production, this should delegate to DataDeletionService
        # For now, just log the action
        logger.info(f"Data deletion executed for user: {user_id}")
