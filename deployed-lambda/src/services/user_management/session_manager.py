"""Session management for secure user sessions."""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError

from src.shared.aws_clients.dynamodb_client import DynamoDBClient
from src.shared.utils.errors import AuthenticationError, AWSServiceError

logger = logging.getLogger(__name__)


class SessionManager:
    """Manager for user sessions with secure token handling."""

    def __init__(
        self,
        session_table: DynamoDBClient,
        session_timeout_minutes: int = 60,
        refresh_timeout_days: int = 30,
    ) -> None:
        """
        Initialize session manager.

        Args:
            session_table: DynamoDB table for session storage
            session_timeout_minutes: Session timeout in minutes
            refresh_timeout_days: Refresh token timeout in days
        """
        self.session_table = session_table
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.refresh_timeout = timedelta(days=refresh_timeout_days)
        logger.info("Initialized SessionManager")

    def create_session(
        self,
        user_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new user session.

        Args:
            user_id: User identifier
            access_token: Cognito access token
            refresh_token: Cognito refresh token (optional)
            metadata: Additional session metadata (optional)

        Returns:
            Session ID

        Raises:
            AWSServiceError: If session creation fails
        """
        try:
            session_id = self._generate_session_id()
            now = datetime.utcnow()

            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "created_at": now.isoformat(),
                "expires_at": (now + self.session_timeout).isoformat(),
                "last_activity": now.isoformat(),
                "is_active": True,
                "metadata": metadata or {},
            }

            self.session_table.put_item(session_data)
            logger.info(f"Created session for user: {user_id}")
            return session_id

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to create session: {str(e)}",
                service="DynamoDB",
                operation="put_item",
            )

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data if found and valid, None otherwise

        Raises:
            AWSServiceError: If retrieval fails
        """
        try:
            item = self.session_table.get_item({"session_id": session_id})

            if not item:
                return None

            # Check if session is active and not expired
            if not item.get("is_active", False):
                logger.info(f"Session {session_id} is inactive")
                return None

            expires_at = datetime.fromisoformat(item["expires_at"])
            if datetime.utcnow() > expires_at:
                logger.info(f"Session {session_id} has expired")
                self.invalidate_session(session_id)
                return None

            return item

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to retrieve session: {str(e)}",
                service="DynamoDB",
                operation="get_item",
            )

    def validate_session(self, session_id: str) -> bool:
        """
        Validate if session is active and not expired.

        Args:
            session_id: Session identifier

        Returns:
            True if session is valid, False otherwise
        """
        session = self.get_session(session_id)
        return session is not None

    def refresh_session(self, session_id: str) -> None:
        """
        Refresh session expiration time.

        Args:
            session_id: Session identifier

        Raises:
            AuthenticationError: If session is invalid
            AWSServiceError: If update fails
        """
        try:
            session = self.get_session(session_id)
            if not session:
                raise AuthenticationError("Invalid or expired session")

            now = datetime.utcnow()
            self.session_table.update_item(
                key={"session_id": session_id},
                update_expression="SET expires_at = :expires, last_activity = :activity",
                expression_values={
                    ":expires": (now + self.session_timeout).isoformat(),
                    ":activity": now.isoformat(),
                },
            )
            logger.info(f"Refreshed session: {session_id}")

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to refresh session: {str(e)}",
                service="DynamoDB",
                operation="update_item",
            )

    def invalidate_session(self, session_id: str) -> None:
        """
        Invalidate a session (logout).

        Args:
            session_id: Session identifier

        Raises:
            AWSServiceError: If invalidation fails
        """
        try:
            self.session_table.update_item(
                key={"session_id": session_id},
                update_expression="SET is_active = :active",
                expression_values={":active": False},
            )
            logger.info(f"Invalidated session: {session_id}")

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to invalidate session: {str(e)}",
                service="DynamoDB",
                operation="update_item",
            )

    def invalidate_user_sessions(self, user_id: str) -> None:
        """
        Invalidate all sessions for a user.

        Args:
            user_id: User identifier

        Raises:
            AWSServiceError: If invalidation fails
        """
        try:
            # Query all sessions for user
            sessions = self.session_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )

            # Invalidate each session
            for session in sessions:
                self.invalidate_session(session["session_id"])

            logger.info(f"Invalidated all sessions for user: {user_id}")

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to invalidate user sessions: {str(e)}",
                service="DynamoDB",
                operation="query",
            )

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from the database.

        Returns:
            Number of sessions cleaned up

        Raises:
            AWSServiceError: If cleanup fails
        """
        try:
            now = datetime.utcnow()
            
            # Scan for expired sessions
            sessions = self.session_table.scan(
                filter_expression="expires_at < :now OR is_active = :inactive",
                expression_values={
                    ":now": now.isoformat(),
                    ":inactive": False,
                },
            )

            # Delete expired sessions
            count = 0
            for session in sessions:
                self.session_table.delete_item({"session_id": session["session_id"]})
                count += 1

            logger.info(f"Cleaned up {count} expired sessions")
            return count

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to cleanup sessions: {str(e)}",
                service="DynamoDB",
                operation="scan",
            )

    @staticmethod
    def _generate_session_id() -> str:
        """
        Generate a secure random session ID.

        Returns:
            Session ID
        """
        return secrets.token_urlsafe(32)
