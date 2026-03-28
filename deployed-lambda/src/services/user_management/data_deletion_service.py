"""Complete data deletion service for user data across all systems."""

import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError

from src.shared.aws_clients.dynamodb_client import DynamoDBClient
from src.shared.aws_clients.s3_client import S3Client
from src.shared.aws_clients.cognito_client import CognitoClient
from src.services.user_management.privacy_manager import DataCategory
from src.shared.utils.errors import AWSServiceError

logger = logging.getLogger(__name__)


class DataDeletionService:
    """Service for complete user data deletion across all systems."""

    def __init__(
        self,
        # User data tables
        user_table: DynamoDBClient,
        progress_table: DynamoDBClient,
        
        # Content data tables
        content_table: DynamoDBClient,
        summary_table: DynamoDBClient,
        
        # Quiz data tables
        quiz_table: DynamoDBClient,
        flashcard_table: DynamoDBClient,
        quiz_result_table: DynamoDBClient,
        
        # Code analysis table
        code_snippet_table: DynamoDBClient,
        
        # Voice recordings table
        voice_recording_table: DynamoDBClient,
        
        # Audit logs table
        audit_table: DynamoDBClient,
        
        # S3 client for file deletion
        s3_client: S3Client,
        content_bucket: str,
        
        # Cognito client for account deletion
        cognito_client: Optional[CognitoClient] = None,
    ) -> None:
        """
        Initialize data deletion service.

        Args:
            user_table: User profile table
            progress_table: Learning progress table
            content_table: Content table
            summary_table: Summary table
            quiz_table: Quiz table
            flashcard_table: Flashcard table
            quiz_result_table: Quiz result table
            code_snippet_table: Code snippet table
            voice_recording_table: Voice recording table
            audit_table: Audit log table
            s3_client: S3 client for file deletion
            content_bucket: S3 bucket for content
            cognito_client: Cognito client for account deletion
        """
        self.user_table = user_table
        self.progress_table = progress_table
        self.content_table = content_table
        self.summary_table = summary_table
        self.quiz_table = quiz_table
        self.flashcard_table = flashcard_table
        self.quiz_result_table = quiz_result_table
        self.code_snippet_table = code_snippet_table
        self.voice_recording_table = voice_recording_table
        self.audit_table = audit_table
        self.s3_client = s3_client
        self.content_bucket = content_bucket
        self.cognito_client = cognito_client
        logger.info("Initialized DataDeletionService")

    def delete_all_user_data(
        self,
        user_id: str,
        categories: Optional[List[DataCategory]] = None,
    ) -> Dict[str, Any]:
        """
        Delete all user data or specific categories.

        Args:
            user_id: User identifier
            categories: Data categories to delete (all if None)

        Returns:
            Deletion summary with counts per category

        Raises:
            AWSServiceError: If deletion fails
        """
        logger.info(f"Starting complete data deletion for user: {user_id}")
        
        # Determine which categories to delete
        categories_to_delete = categories or list(DataCategory)
        
        deletion_summary = {
            "user_id": user_id,
            "deleted_at": datetime.utcnow().isoformat(),
            "categories": {},
            "errors": [],
        }

        # Delete each category
        for category in categories_to_delete:
            try:
                if category == DataCategory.PROFILE:
                    count = self._delete_profile_data(user_id)
                    deletion_summary["categories"]["profile"] = count
                    
                elif category == DataCategory.CONTENT:
                    count = self._delete_content_data(user_id)
                    deletion_summary["categories"]["content"] = count
                    
                elif category == DataCategory.QUIZ_RESULTS:
                    count = self._delete_quiz_data(user_id)
                    deletion_summary["categories"]["quiz_results"] = count
                    
                elif category == DataCategory.LEARNING_PROGRESS:
                    count = self._delete_progress_data(user_id)
                    deletion_summary["categories"]["learning_progress"] = count
                    
                elif category == DataCategory.VOICE_RECORDINGS:
                    count = self._delete_voice_data(user_id)
                    deletion_summary["categories"]["voice_recordings"] = count
                    
                elif category == DataCategory.CODE_SNIPPETS:
                    count = self._delete_code_data(user_id)
                    deletion_summary["categories"]["code_snippets"] = count
                    
                elif category == DataCategory.AUDIT_LOGS:
                    count = self._anonymize_audit_logs(user_id)
                    deletion_summary["categories"]["audit_logs"] = count
                    
            except Exception as e:
                error_msg = f"Failed to delete {category.value}: {str(e)}"
                logger.error(error_msg)
                deletion_summary["errors"].append(error_msg)

        logger.info(f"Completed data deletion for user: {user_id}")
        return deletion_summary

    def _delete_profile_data(self, user_id: str) -> int:
        """
        Delete user profile data.

        Args:
            user_id: User identifier

        Returns:
            Number of items deleted
        """
        logger.info(f"Deleting profile data for user: {user_id}")
        count = 0

        try:
            # Delete user profile
            self.user_table.delete_item({"id": user_id})
            count += 1
            logger.info(f"Deleted user profile for: {user_id}")
        except ClientError as e:
            logger.error(f"Failed to delete user profile: {e}")
            raise

        return count

    def _delete_content_data(self, user_id: str) -> int:
        """
        Delete all content uploaded by user.

        Args:
            user_id: User identifier

        Returns:
            Number of items deleted
        """
        logger.info(f"Deleting content data for user: {user_id}")
        count = 0

        try:
            # Query all content for user
            content_items = self.content_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )

            for content in content_items:
                content_id = content.get("id")
                
                # Delete S3 files if they exist
                s3_location = content.get("s3_location")
                if s3_location:
                    try:
                        # Extract key from S3 URI (s3://bucket/key)
                        key = s3_location.replace(f"s3://{self.content_bucket}/", "")
                        self.s3_client.delete_file(key=key, bucket=self.content_bucket)
                        logger.info(f"Deleted S3 file: {s3_location}")
                    except Exception as e:
                        logger.warning(f"Failed to delete S3 file {s3_location}: {e}")

                # Delete summaries associated with this content
                try:
                    summaries = self.summary_table.query(
                        key_condition_expression="content_id = :content_id",
                        expression_values={":content_id": content_id},
                    )
                    for summary in summaries:
                        self.summary_table.delete_item({"id": summary["id"]})
                        count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete summaries for content {content_id}: {e}")

                # Delete the content record
                self.content_table.delete_item({"id": content_id})
                count += 1

            logger.info(f"Deleted {count} content items for user: {user_id}")
        except ClientError as e:
            logger.error(f"Failed to delete content data: {e}")
            raise

        return count

    def _delete_quiz_data(self, user_id: str) -> int:
        """
        Delete all quiz-related data for user.

        Args:
            user_id: User identifier

        Returns:
            Number of items deleted
        """
        logger.info(f"Deleting quiz data for user: {user_id}")
        count = 0

        try:
            # Delete quiz results
            quiz_results = self.quiz_result_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )
            for result in quiz_results:
                self.quiz_result_table.delete_item({
                    "user_id": user_id,
                    "quiz_id": result["quiz_id"],
                })
                count += 1

            # Delete flashcards (query by user's content)
            # First get user's content IDs
            content_items = self.content_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )
            
            for content in content_items:
                content_id = content.get("id")
                
                # Delete flashcards for this content
                flashcards = self.flashcard_table.query(
                    key_condition_expression="content_id = :content_id",
                    expression_values={":content_id": content_id},
                )
                for flashcard in flashcards:
                    self.flashcard_table.delete_item({"id": flashcard["id"]})
                    count += 1

                # Delete quizzes for this content
                quizzes = self.quiz_table.query(
                    key_condition_expression="content_id = :content_id",
                    expression_values={":content_id": content_id},
                )
                for quiz in quizzes:
                    self.quiz_table.delete_item({"id": quiz["id"]})
                    count += 1

            logger.info(f"Deleted {count} quiz items for user: {user_id}")
        except ClientError as e:
            logger.error(f"Failed to delete quiz data: {e}")
            raise

        return count

    def _delete_progress_data(self, user_id: str) -> int:
        """
        Delete learning progress data.

        Args:
            user_id: User identifier

        Returns:
            Number of items deleted
        """
        logger.info(f"Deleting progress data for user: {user_id}")
        count = 0

        try:
            self.progress_table.delete_item({"user_id": user_id})
            count += 1
            logger.info(f"Deleted progress data for user: {user_id}")
        except ClientError as e:
            logger.error(f"Failed to delete progress data: {e}")
            raise

        return count

    def _delete_voice_data(self, user_id: str) -> int:
        """
        Delete voice recordings.

        Args:
            user_id: User identifier

        Returns:
            Number of items deleted
        """
        logger.info(f"Deleting voice data for user: {user_id}")
        count = 0

        try:
            # Query voice recordings
            recordings = self.voice_recording_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )

            for recording in recordings:
                # Delete S3 file if exists
                s3_location = recording.get("s3_location")
                if s3_location:
                    try:
                        key = s3_location.replace(f"s3://{self.content_bucket}/", "")
                        self.s3_client.delete_file(key=key, bucket=self.content_bucket)
                    except Exception as e:
                        logger.warning(f"Failed to delete voice file {s3_location}: {e}")

                # Delete recording record
                self.voice_recording_table.delete_item({"id": recording["id"]})
                count += 1

            logger.info(f"Deleted {count} voice recordings for user: {user_id}")
        except ClientError as e:
            logger.error(f"Failed to delete voice data: {e}")
            raise

        return count

    def _delete_code_data(self, user_id: str) -> int:
        """
        Delete code snippets.

        Args:
            user_id: User identifier

        Returns:
            Number of items deleted
        """
        logger.info(f"Deleting code data for user: {user_id}")
        count = 0

        try:
            # Query code snippets
            snippets = self.code_snippet_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )

            for snippet in snippets:
                self.code_snippet_table.delete_item({"id": snippet["id"]})
                count += 1

            logger.info(f"Deleted {count} code snippets for user: {user_id}")
        except ClientError as e:
            logger.error(f"Failed to delete code data: {e}")
            raise

        return count

    def _anonymize_audit_logs(self, user_id: str) -> int:
        """
        Anonymize audit logs (keep for compliance but remove PII).

        Args:
            user_id: User identifier

        Returns:
            Number of items anonymized
        """
        logger.info(f"Anonymizing audit logs for user: {user_id}")
        count = 0

        try:
            # Query audit logs for user
            logs = self.audit_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )

            for log in logs:
                # Anonymize by replacing user_id with hashed version
                # and removing PII from metadata
                self.audit_table.update_item(
                    key={"id": log["id"]},
                    update_expression="SET user_id = :anon_id, anonymized = :anon, anonymized_at = :anon_at REMOVE ip_address, user_agent",
                    expression_values={
                        ":anon_id": f"DELETED_USER_{hash(user_id) % 1000000}",
                        ":anon": True,
                        ":anon_at": datetime.utcnow().isoformat(),
                    },
                )
                count += 1

            logger.info(f"Anonymized {count} audit logs for user: {user_id}")
        except ClientError as e:
            logger.error(f"Failed to anonymize audit logs: {e}")
            raise

        return count

    def delete_cognito_account(self, user_id: str, access_token: str) -> None:
        """
        Delete user's Cognito account.

        Args:
            user_id: User identifier
            access_token: User's access token

        Raises:
            AWSServiceError: If deletion fails
        """
        if not self.cognito_client:
            logger.warning("Cognito client not configured, skipping account deletion")
            return

        try:
            self.cognito_client.delete_user(access_token)
            logger.info(f"Deleted Cognito account for user: {user_id}")
        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to delete Cognito account: {str(e)}",
                service="Cognito",
                operation="delete_user",
            )
