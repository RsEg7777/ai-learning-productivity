"""User management service with Cognito integration."""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError

from src.shared.aws_clients.cognito_client import CognitoClient
from src.shared.aws_clients.dynamodb_client import DynamoDBClient
from src.shared.models.user import (
    User,
    UserRegistration,
    LoginCredentials,
    AuthResult,
    UserPreferences,
    LearningProgress,
)
from src.shared.utils.errors import (
    AuthenticationError,
    ValidationError,
    AWSServiceError,
)

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations."""

    def __init__(
        self,
        cognito_client: CognitoClient,
        user_table: DynamoDBClient,
        progress_table: DynamoDBClient,
    ) -> None:
        """
        Initialize user service.

        Args:
            cognito_client: Cognito client for authentication
            user_table: DynamoDB table for user profiles
            progress_table: DynamoDB table for learning progress
        """
        self.cognito = cognito_client
        self.user_table = user_table
        self.progress_table = progress_table
        logger.info("Initialized UserService")

    def register_user(self, registration: UserRegistration) -> User:
        """
        Register a new user with Cognito and create profile.

        Args:
            registration: User registration data

        Returns:
            Created user

        Raises:
            ValidationError: If registration data is invalid
            AuthenticationError: If Cognito registration fails
            AWSServiceError: If database operation fails
        """
        try:
            # Register with Cognito
            username = registration.email  # Use email as username
            cognito_response = self.cognito.sign_up(
                username=username,
                password=registration.password,
                email=registration.email,
                attributes={
                    "name": registration.full_name or "",
                    "preferred_username": registration.username or username,
                },
            )

            # Extract user ID from Cognito response
            user_id = cognito_response.get("UserSub")

            # Create user profile
            user = User(
                id=user_id,
                email=registration.email,
                username=registration.username,
                full_name=registration.full_name,
                preferences=UserPreferences(
                    language=registration.preferred_language
                ),
                created_at=datetime.utcnow(),
                last_active=datetime.utcnow(),
            )

            # Store user profile in DynamoDB
            self.user_table.put_item(self._user_to_dict(user))

            # Initialize learning progress
            progress = LearningProgress(
                user_id=user_id,
                last_active=datetime.utcnow(),
            )
            self.progress_table.put_item(self._progress_to_dict(progress))

            logger.info(f"Successfully registered user: {user_id}")
            return user

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            if error_code == "UsernameExistsException":
                raise ValidationError(
                    message="User with this email already exists",
                    field="email",
                )
            elif error_code == "InvalidPasswordException":
                raise ValidationError(
                    message="Password does not meet requirements",
                    field="password",
                )
            else:
                raise AuthenticationError(
                    message=f"Registration failed: {error_message}",
                    details={"error_code": error_code},
                )

    def authenticate_user(self, credentials: LoginCredentials) -> AuthResult:
        """
        Authenticate user with Cognito.

        Args:
            credentials: Login credentials

        Returns:
            Authentication result with tokens

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Authenticate with Cognito
            response = self.cognito.initiate_auth(
                username=credentials.email,
                password=credentials.password,
            )

            # Check if MFA is required
            if response.get("ChallengeName") == "SMS_MFA":
                return AuthResult(
                    success=False,
                    requires_mfa=True,
                    error_message="MFA code required",
                )

            # Extract tokens
            auth_result = response.get("AuthenticationResult", {})
            access_token = auth_result.get("AccessToken")

            # Get user info
            user_info = self.cognito.get_user(access_token)
            user_id = user_info.get("Username")

            # Update last active timestamp
            self._update_last_active(user_id)

            logger.info(f"Successfully authenticated user: {user_id}")

            return AuthResult(
                success=True,
                user_id=user_id,
                access_token=access_token,
                refresh_token=auth_result.get("RefreshToken"),
                expires_in=auth_result.get("ExpiresIn"),
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            if error_code in ["NotAuthorizedException", "UserNotFoundException"]:
                raise AuthenticationError(
                    message="Invalid email or password",
                    details={"error_code": error_code},
                )
            else:
                raise AuthenticationError(
                    message=f"Authentication failed: {error_message}",
                    details={"error_code": error_code},
                )

    def verify_mfa(
        self,
        session: str,
        mfa_code: str,
        username: str,
    ) -> AuthResult:
        """
        Verify MFA code and complete authentication.

        Args:
            session: Session from initial auth
            mfa_code: MFA verification code
            username: Username

        Returns:
            Authentication result with tokens

        Raises:
            AuthenticationError: If MFA verification fails
        """
        try:
            response = self.cognito.respond_to_auth_challenge(
                session=session,
                challenge_name="SMS_MFA",
                challenge_responses={
                    "USERNAME": username,
                    "SMS_MFA_CODE": mfa_code,
                },
            )

            auth_result = response.get("AuthenticationResult", {})
            access_token = auth_result.get("AccessToken")

            # Get user info
            user_info = self.cognito.get_user(access_token)
            user_id = user_info.get("Username")

            # Update last active timestamp
            self._update_last_active(user_id)

            logger.info(f"Successfully verified MFA for user: {user_id}")

            return AuthResult(
                success=True,
                user_id=user_id,
                access_token=access_token,
                refresh_token=auth_result.get("RefreshToken"),
                expires_in=auth_result.get("ExpiresIn"),
            )

        except ClientError as e:
            error_message = e.response.get("Error", {}).get("Message", str(e))
            raise AuthenticationError(
                message=f"MFA verification failed: {error_message}",
            )

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get user profile by ID.

        Args:
            user_id: User identifier

        Returns:
            User profile if found, None otherwise

        Raises:
            AWSServiceError: If database operation fails
        """
        try:
            item = self.user_table.get_item({"id": user_id})
            if item:
                return self._dict_to_user(item)
            return None
        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to retrieve user: {str(e)}",
                service="DynamoDB",
                operation="get_item",
            )

    def update_preferences(
        self,
        user_id: str,
        preferences: UserPreferences,
    ) -> None:
        """
        Update user preferences.

        Args:
            user_id: User identifier
            preferences: Updated preferences

        Raises:
            AWSServiceError: If database operation fails
        """
        try:
            self.user_table.update_item(
                key={"id": user_id},
                update_expression="SET preferences = :prefs, last_active = :last_active",
                expression_values={
                    ":prefs": preferences.model_dump(),
                    ":last_active": datetime.utcnow().isoformat(),
                },
            )
            logger.info(f"Updated preferences for user: {user_id}")
        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to update preferences: {str(e)}",
                service="DynamoDB",
                operation="update_item",
            )

    def get_progress(self, user_id: str) -> Optional[LearningProgress]:
        """
        Get user's learning progress.

        Args:
            user_id: User identifier

        Returns:
            Learning progress if found, None otherwise

        Raises:
            AWSServiceError: If database operation fails
        """
        try:
            item = self.progress_table.get_item({"user_id": user_id})
            if item:
                return self._dict_to_progress(item)
            return None
        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to retrieve progress: {str(e)}",
                service="DynamoDB",
                operation="get_item",
            )

    def update_progress(
        self,
        user_id: str,
        study_time_minutes: Optional[int] = None,
        content_processed: Optional[int] = None,
        quiz_completed: Optional[bool] = None,
        quiz_score: Optional[float] = None,
    ) -> None:
        """
        Update user's learning progress.

        Args:
            user_id: User identifier
            study_time_minutes: Minutes to add to total study time
            content_processed: Number of content items processed
            quiz_completed: Whether a quiz was completed
            quiz_score: Quiz score (0-100)

        Raises:
            AWSServiceError: If database operation fails
        """
        try:
            # Get current progress
            current = self.get_progress(user_id)
            if not current:
                # Initialize if doesn't exist
                current = LearningProgress(user_id=user_id)
                self.progress_table.put_item(self._progress_to_dict(current))

            # Build update expression
            updates = []
            values = {}

            if study_time_minutes is not None:
                updates.append("total_study_time = total_study_time + :study_time")
                values[":study_time"] = study_time_minutes

            if content_processed is not None:
                updates.append("content_processed = content_processed + :content")
                values[":content"] = content_processed

            if quiz_completed:
                updates.append("quizzes_completed = quizzes_completed + :quiz")
                values[":quiz"] = 1

                if quiz_score is not None:
                    # Calculate new average score
                    total_quizzes = current.quizzes_completed + 1
                    new_avg = (
                        (current.average_score * current.quizzes_completed + quiz_score)
                        / total_quizzes
                    )
                    updates.append("average_score = :avg_score")
                    values[":avg_score"] = round(new_avg, 2)

            updates.append("last_active = :last_active")
            values[":last_active"] = datetime.utcnow().isoformat()

            if updates:
                self.progress_table.update_item(
                    key={"user_id": user_id},
                    update_expression=f"SET {', '.join(updates)}",
                    expression_values=values,
                )
                logger.info(f"Updated progress for user: {user_id}")

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to update progress: {str(e)}",
                service="DynamoDB",
                operation="update_item",
            )

    def delete_user_data(self, user_id: str, access_token: str) -> None:
        """
        Delete all user data including Cognito account.

        Args:
            user_id: User identifier
            access_token: User's access token

        Raises:
            AWSServiceError: If deletion fails
        """
        try:
            # Delete from Cognito
            self.cognito.delete_user(access_token)

            # Delete user profile
            self.user_table.delete_item({"id": user_id})

            # Delete learning progress
            self.progress_table.delete_item({"user_id": user_id})

            logger.info(f"Deleted all data for user: {user_id}")

        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to delete user data: {str(e)}",
                service="Multiple",
                operation="delete",
            )

    def _update_last_active(self, user_id: str) -> None:
        """Update user's last active timestamp."""
        try:
            self.user_table.update_item(
                key={"id": user_id},
                update_expression="SET last_active = :last_active",
                expression_values={
                    ":last_active": datetime.utcnow().isoformat(),
                },
            )
        except ClientError as e:
            logger.warning(f"Failed to update last active: {e}")

    @staticmethod
    def _user_to_dict(user: User) -> Dict[str, Any]:
        """Convert User model to DynamoDB item."""
        data = user.model_dump()
        # Convert datetime objects to ISO format strings
        data["created_at"] = user.created_at.isoformat()
        data["last_active"] = user.last_active.isoformat()
        return data

    @staticmethod
    def _dict_to_user(item: Dict[str, Any]) -> User:
        """Convert DynamoDB item to User model."""
        # Convert ISO format strings back to datetime
        if isinstance(item.get("created_at"), str):
            item["created_at"] = datetime.fromisoformat(item["created_at"])
        if isinstance(item.get("last_active"), str):
            item["last_active"] = datetime.fromisoformat(item["last_active"])
        return User(**item)

    @staticmethod
    def _progress_to_dict(progress: LearningProgress) -> Dict[str, Any]:
        """Convert LearningProgress model to DynamoDB item."""
        data = progress.model_dump()
        # Convert datetime to ISO format string
        data["last_active"] = progress.last_active.isoformat()
        # Convert achievements to dicts
        data["achievements"] = [
            {
                **ach.model_dump(),
                "earned_at": ach.earned_at.isoformat(),
            }
            for ach in progress.achievements
        ]
        return data

    @staticmethod
    def _dict_to_progress(item: Dict[str, Any]) -> LearningProgress:
        """Convert DynamoDB item to LearningProgress model."""
        # Convert ISO format string back to datetime
        if isinstance(item.get("last_active"), str):
            item["last_active"] = datetime.fromisoformat(item["last_active"])
        # Convert achievement dicts back to models
        if "achievements" in item:
            for ach in item["achievements"]:
                if isinstance(ach.get("earned_at"), str):
                    ach["earned_at"] = datetime.fromisoformat(ach["earned_at"])
        return LearningProgress(**item)
