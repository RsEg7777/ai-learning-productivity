"""Data export service for user data portability."""

import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from io import BytesIO
from botocore.exceptions import ClientError

from src.shared.aws_clients.dynamodb_client import DynamoDBClient
from src.shared.aws_clients.s3_client import S3Client
from src.services.user_management.privacy_manager import DataCategory
from src.shared.utils.errors import AWSServiceError

logger = logging.getLogger(__name__)


class DataExportService:
    """Service for exporting user data in portable format."""

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
        
        # S3 client for export storage
        s3_client: S3Client,
        export_bucket: str,
    ) -> None:
        """
        Initialize data export service.

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
            s3_client: S3 client for export storage
            export_bucket: S3 bucket for exports
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
        self.export_bucket = export_bucket
        logger.info("Initialized DataExportService")

    def export_user_data(
        self,
        user_id: str,
        categories: Optional[List[DataCategory]] = None,
    ) -> str:
        """
        Export all user data or specific categories to JSON.

        Args:
            user_id: User identifier
            categories: Data categories to export (all if None)

        Returns:
            S3 URI of the export file

        Raises:
            AWSServiceError: If export fails
        """
        logger.info(f"Starting data export for user: {user_id}")
        
        # Determine which categories to export
        categories_to_export = categories or list(DataCategory)
        
        export_data = {
            "user_id": user_id,
            "exported_at": datetime.utcnow().isoformat(),
            "format_version": "1.0",
            "data": {},
        }

        # Export each category
        for category in categories_to_export:
            try:
                if category == DataCategory.PROFILE:
                    export_data["data"]["profile"] = self._export_profile_data(user_id)
                    
                elif category == DataCategory.CONTENT:
                    export_data["data"]["content"] = self._export_content_data(user_id)
                    
                elif category == DataCategory.QUIZ_RESULTS:
                    export_data["data"]["quiz_results"] = self._export_quiz_data(user_id)
                    
                elif category == DataCategory.LEARNING_PROGRESS:
                    export_data["data"]["learning_progress"] = self._export_progress_data(user_id)
                    
                elif category == DataCategory.VOICE_RECORDINGS:
                    export_data["data"]["voice_recordings"] = self._export_voice_data(user_id)
                    
                elif category == DataCategory.CODE_SNIPPETS:
                    export_data["data"]["code_snippets"] = self._export_code_data(user_id)
                    
                elif category == DataCategory.AUDIT_LOGS:
                    export_data["data"]["audit_logs"] = self._export_audit_logs(user_id)
                    
            except Exception as e:
                logger.error(f"Failed to export {category.value}: {e}")
                export_data["data"][category.value] = {
                    "error": str(e),
                    "status": "failed",
                }

        # Convert to JSON and upload to S3
        try:
            json_data = json.dumps(export_data, indent=2, default=str)
            json_bytes = BytesIO(json_data.encode('utf-8'))
            
            # Create export file key
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            export_key = f"exports/{user_id}/data_export_{timestamp}.json"
            
            # Upload to S3
            s3_uri = self.s3_client.upload_file(
                file_obj=json_bytes,
                key=export_key,
                content_type="application/json",
                metadata={
                    "user_id": user_id,
                    "export_date": datetime.utcnow().isoformat(),
                },
                bucket=self.export_bucket,
            )
            
            logger.info(f"Completed data export for user {user_id}: {s3_uri}")
            return s3_uri
            
        except Exception as e:
            raise AWSServiceError(
                message=f"Failed to upload export file: {str(e)}",
                service="S3",
                operation="upload_file",
            )

    def _export_profile_data(self, user_id: str) -> Dict[str, Any]:
        """Export user profile data."""
        logger.info(f"Exporting profile data for user: {user_id}")
        
        try:
            user = self.user_table.get_item({"id": user_id})
            if user:
                # Remove sensitive fields
                user_copy = dict(user)
                # Keep all data for export
                return user_copy
            return {}
        except ClientError as e:
            logger.error(f"Failed to export profile data: {e}")
            raise

    def _export_content_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Export content data."""
        logger.info(f"Exporting content data for user: {user_id}")
        
        try:
            content_items = self.content_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )
            
            # Include summaries for each content
            for content in content_items:
                content_id = content.get("id")
                summaries = self.summary_table.query(
                    key_condition_expression="content_id = :content_id",
                    expression_values={":content_id": content_id},
                )
                content["summaries"] = summaries
            
            return content_items
        except ClientError as e:
            logger.error(f"Failed to export content data: {e}")
            raise

    def _export_quiz_data(self, user_id: str) -> Dict[str, Any]:
        """Export quiz-related data."""
        logger.info(f"Exporting quiz data for user: {user_id}")
        
        try:
            quiz_data = {
                "quiz_results": [],
                "flashcards": [],
                "quizzes": [],
            }
            
            # Export quiz results
            quiz_results = self.quiz_result_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )
            quiz_data["quiz_results"] = quiz_results
            
            # Export flashcards and quizzes for user's content
            content_items = self.content_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )
            
            for content in content_items:
                content_id = content.get("id")
                
                # Get flashcards
                flashcards = self.flashcard_table.query(
                    key_condition_expression="content_id = :content_id",
                    expression_values={":content_id": content_id},
                )
                quiz_data["flashcards"].extend(flashcards)
                
                # Get quizzes
                quizzes = self.quiz_table.query(
                    key_condition_expression="content_id = :content_id",
                    expression_values={":content_id": content_id},
                )
                quiz_data["quizzes"].extend(quizzes)
            
            return quiz_data
        except ClientError as e:
            logger.error(f"Failed to export quiz data: {e}")
            raise

    def _export_progress_data(self, user_id: str) -> Dict[str, Any]:
        """Export learning progress data."""
        logger.info(f"Exporting progress data for user: {user_id}")
        
        try:
            progress = self.progress_table.get_item({"user_id": user_id})
            return progress or {}
        except ClientError as e:
            logger.error(f"Failed to export progress data: {e}")
            raise

    def _export_voice_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Export voice recordings metadata."""
        logger.info(f"Exporting voice data for user: {user_id}")
        
        try:
            recordings = self.voice_recording_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )
            
            # Note: Actual audio files remain in S3, export includes metadata and S3 locations
            return recordings
        except ClientError as e:
            logger.error(f"Failed to export voice data: {e}")
            raise

    def _export_code_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Export code snippets."""
        logger.info(f"Exporting code data for user: {user_id}")
        
        try:
            snippets = self.code_snippet_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )
            return snippets
        except ClientError as e:
            logger.error(f"Failed to export code data: {e}")
            raise

    def _export_audit_logs(self, user_id: str) -> List[Dict[str, Any]]:
        """Export audit logs."""
        logger.info(f"Exporting audit logs for user: {user_id}")
        
        try:
            logs = self.audit_table.query(
                key_condition_expression="user_id = :user_id",
                expression_values={":user_id": user_id},
            )
            return logs
        except ClientError as e:
            logger.error(f"Failed to export audit logs: {e}")
            raise

    def get_export_download_url(
        self,
        user_id: str,
        export_key: str,
        expiration: int = 3600,
    ) -> str:
        """
        Generate a presigned URL for downloading an export.

        Args:
            user_id: User identifier (for verification)
            export_key: S3 key of the export file
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned download URL

        Raises:
            AWSServiceError: If URL generation fails
        """
        # Verify the export belongs to the user
        if not export_key.startswith(f"exports/{user_id}/"):
            raise ValueError("Export does not belong to user")
        
        try:
            url = self.s3_client.get_presigned_url(
                key=export_key,
                expiration=expiration,
            )
            logger.info(f"Generated download URL for export: {export_key}")
            return url
        except ClientError as e:
            raise AWSServiceError(
                message=f"Failed to generate download URL: {str(e)}",
                service="S3",
                operation="get_presigned_url",
            )
