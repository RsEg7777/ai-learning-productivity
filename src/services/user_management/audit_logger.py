"""Comprehensive audit logging for user actions and system events."""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from botocore.exceptions import ClientError

from src.shared.aws_clients.dynamodb_client import DynamoDBClient
from src.shared.utils.errors import AWSServiceError

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Authentication events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login.failed"
    MFA_ENABLED = "user.mfa.enabled"
    MFA_DISABLED = "user.mfa.disabled"
    MFA_VERIFIED = "user.mfa.verified"
    
    # User management events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_ROLE_CHANGED = "user.role.changed"
    USER_PREFERENCES_UPDATED = "user.preferences.updated"
    
    # Content events
    CONTENT_UPLOADED = "content.uploaded"
    CONTENT_PROCESSED = "content.processed"
    CONTENT_VIEWED = "content.viewed"
    CONTENT_UPDATED = "content.updated"
    CONTENT_DELETED = "content.deleted"
    CONTENT_SHARED = "content.shared"
    
    # Quiz events
    QUIZ_CREATED = "quiz.created"
    QUIZ_STARTED = "quiz.started"
    QUIZ_COMPLETED = "quiz.completed"
    QUIZ_DELETED = "quiz.deleted"
    FLASHCARD_REVIEWED = "flashcard.reviewed"
    
    # Code analysis events
    CODE_ANALYZED = "code.analyzed"
    CODE_EXPLANATION_GENERATED = "code.explanation.generated"
    
    # Voice interface events
    VOICE_TRANSCRIPTION = "voice.transcription"
    VOICE_SYNTHESIS = "voice.synthesis"
    
    # Data privacy events
    DATA_EXPORT_REQUESTED = "data.export.requested"
    DATA_DELETION_REQUESTED = "data.deletion.requested"
    CONSENT_GRANTED = "consent.granted"
    CONSENT_REVOKED = "consent.revoked"
    
    # Access control events
    ACCESS_GRANTED = "access.granted"
    ACCESS_DENIED = "access.denied"
    PERMISSION_CHECKED = "permission.checked"
    
    # System events
    SYSTEM_ERROR = "system.error"
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent:
    """Audit event data structure."""

    def __init__(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        result: str = "success",
        severity: AuditSeverity = AuditSeverity.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize audit event.

        Args:
            event_type: Type of event
            user_id: User who performed the action
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            action: Action performed
            result: Result of action (success, failure, denied)
            severity: Event severity
            ip_address: IP address of request
            user_agent: User agent string
            metadata: Additional event metadata
        """
        self.event_id = self._generate_event_id()
        self.timestamp = datetime.utcnow()
        self.event_type = event_type
        self.user_id = user_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.action = action
        self.result = result
        self.severity = severity
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "result": self.result,
            "severity": self.severity.value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata,
        }

    @staticmethod
    def _generate_event_id() -> str:
        """Generate unique event ID."""
        import uuid
        return str(uuid.uuid4())


class AuditLogger:
    """Comprehensive audit logging service."""

    def __init__(self, audit_table: DynamoDBClient) -> None:
        """
        Initialize audit logger.

        Args:
            audit_table: DynamoDB table for audit logs
        """
        self.audit_table = audit_table
        logger.info("Initialized AuditLogger")

    def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        Args:
            event: Audit event to log

        Raises:
            AWSServiceError: If logging fails
        """
        try:
            # Store in DynamoDB
            self.audit_table.put_item(event.to_dict())

            # Also log to CloudWatch for real-time monitoring
            log_level = self._severity_to_log_level(event.severity)
            logger.log(
                log_level,
                f"Audit: {event.event_type.value} - User: {event.user_id} - "
                f"Result: {event.result}",
                extra={
                    "audit_event": event.to_dict(),
                },
            )

        except ClientError as e:
            # Don't fail the operation if audit logging fails
            logger.error(f"Failed to log audit event: {str(e)}")
            # But do raise for critical events
            if event.severity == AuditSeverity.CRITICAL:
                raise AWSServiceError(
                    message=f"Failed to log critical audit event: {str(e)}",
                    service="DynamoDB",
                    operation="put_item",
                )

    def log_authentication(
        self,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log authentication event.

        Args:
            user_id: User identifier
            success: Whether authentication succeeded
            ip_address: IP address of request
            user_agent: User agent string
            metadata: Additional metadata
        """
        event_type = (
            AuditEventType.USER_LOGIN if success
            else AuditEventType.USER_LOGIN_FAILED
        )
        severity = (
            AuditSeverity.INFO if success
            else AuditSeverity.WARNING
        )

        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            action="authenticate",
            result="success" if success else "failure",
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
        )
        self.log_event(event)

    def log_access_control(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permission: str,
        granted: bool,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log access control decision.

        Args:
            user_id: User identifier
            resource_type: Type of resource
            resource_id: Resource identifier
            permission: Permission checked
            granted: Whether access was granted
            ip_address: IP address of request
            metadata: Additional metadata
        """
        event_type = (
            AuditEventType.ACCESS_GRANTED if granted
            else AuditEventType.ACCESS_DENIED
        )
        severity = (
            AuditSeverity.INFO if granted
            else AuditSeverity.WARNING
        )

        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=f"check_permission:{permission}",
            result="granted" if granted else "denied",
            severity=severity,
            ip_address=ip_address,
            metadata=metadata,
        )
        self.log_event(event)

    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log data access event.

        Args:
            user_id: User identifier
            resource_type: Type of resource
            resource_id: Resource identifier
            action: Action performed (read, write, delete)
            ip_address: IP address of request
            metadata: Additional metadata
        """
        # Map action to event type
        event_type_map = {
            "read": AuditEventType.CONTENT_VIEWED,
            "write": AuditEventType.CONTENT_UPDATED,
            "delete": AuditEventType.CONTENT_DELETED,
            "create": AuditEventType.CONTENT_UPLOADED,
        }
        event_type = event_type_map.get(action, AuditEventType.API_REQUEST)

        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result="success",
            severity=AuditSeverity.INFO,
            ip_address=ip_address,
            metadata=metadata,
        )
        self.log_event(event)

    def log_privacy_event(
        self,
        user_id: str,
        event_type: AuditEventType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log data privacy event.

        Args:
            user_id: User identifier
            event_type: Type of privacy event
            metadata: Additional metadata
        """
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            action=event_type.value,
            result="success",
            severity=AuditSeverity.INFO,
            metadata=metadata,
        )
        self.log_event(event)

    def log_error(
        self,
        error_message: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.ERROR,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log system error.

        Args:
            error_message: Error message
            user_id: User identifier (if applicable)
            resource_type: Type of resource (if applicable)
            resource_id: Resource identifier (if applicable)
            severity: Error severity
            metadata: Additional metadata
        """
        event = AuditEvent(
            event_type=AuditEventType.SYSTEM_ERROR,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action="error",
            result="failure",
            severity=severity,
            metadata={
                **(metadata or {}),
                "error_message": error_message,
            },
        )
        self.log_event(event)

    def query_user_activity(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query audit logs for user activity.

        Args:
            user_id: User identifier
            start_time: Start of time range
            end_time: End of time range
            event_types: Filter by event types
            limit: Maximum number of results

        Returns:
            List of audit events

        Raises:
            AWSServiceError: If query fails
        """
        try:
            # Build filter expression
            filter_parts = []
            expression_values = {"#user_id": user_id}

            if start_time:
                filter_parts.append("timestamp >= :start_time")
                expression_values[":start_time"] = start_time.isoformat()

            if end_time:
                filter_parts.append("timestamp <= :end_time")
                expression_values[":end_time"] = end_time.isoformat()

            if event_types:
                event_type_values = [et.value for et in event_types]
                filter_parts.append("event_type IN (:event_types)")
                expression_values[":event_types"] = event_type_values

            # Query DynamoDB
            results = self.audit_table.query(
                key_condition_expression="user_id = #user_id",
                filter_expression=" AND ".join(filter_parts) if filter_parts else None,
                expression_values=expression_values,
                limit=limit,
            )

            return results

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to query audit logs: {str(e)}",
                service="DynamoDB",
                operation="query",
            )

    def query_resource_access(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query audit logs for resource access.

        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
            limit: Maximum number of results

        Returns:
            List of audit events

        Raises:
            AWSServiceError: If query fails
        """
        try:
            results = self.audit_table.query(
                index_name="resource-index",
                key_condition_expression="resource_type = :type AND resource_id = :id",
                expression_values={
                    ":type": resource_type,
                    ":id": resource_id,
                },
                limit=limit,
            )

            return results

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to query resource access logs: {str(e)}",
                service="DynamoDB",
                operation="query",
            )

    @staticmethod
    def _severity_to_log_level(severity: AuditSeverity) -> int:
        """Convert audit severity to logging level."""
        severity_map = {
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL,
        }
        return severity_map.get(severity, logging.INFO)
