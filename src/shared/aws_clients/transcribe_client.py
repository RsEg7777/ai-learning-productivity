"""Amazon Transcribe client for speech-to-text."""

import logging
import time
from typing import Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class TranscribeClient:
    """Client for Amazon Transcribe operations."""

    def __init__(self, region: Optional[str] = None) -> None:
        """
        Initialize Transcribe client.

        Args:
            region: AWS region (optional)
        """
        self.region = region or "us-east-1"
        self.client = boto3.client("transcribe", region_name=self.region)
        logger.info(f"Initialized TranscribeClient in region: {self.region}")

    def start_transcription_job(
        self,
        job_name: str,
        media_uri: str,
        language_code: str = "en-US",
        media_format: str = "mp4",
        output_bucket: Optional[str] = None,
    ) -> str:
        """
        Start a transcription job.

        Args:
            job_name: Unique job name
            media_uri: S3 URI of media file
            language_code: Language code (e.g., 'en-US', 'hi-IN')
            media_format: Media format (mp3, mp4, wav, flac)
            output_bucket: S3 bucket for output (optional)

        Returns:
            Job name

        Raises:
            ClientError: If job creation fails
        """
        try:
            params = {
                "TranscriptionJobName": job_name,
                "Media": {"MediaFileUri": media_uri},
                "MediaFormat": media_format,
                "LanguageCode": language_code,
            }

            if output_bucket:
                params["OutputBucketName"] = output_bucket

            self.client.start_transcription_job(**params)
            logger.info(f"Started transcription job: {job_name}")
            return job_name

        except ClientError as e:
            logger.error(f"Failed to start transcription job: {e}")
            raise

    def get_transcription_job(self, job_name: str) -> dict:
        """
        Get transcription job status and results.

        Args:
            job_name: Job name

        Returns:
            Job details

        Raises:
            ClientError: If retrieval fails
        """
        try:
            response = self.client.get_transcription_job(TranscriptionJobName=job_name)
            return response["TranscriptionJob"]
        except ClientError as e:
            logger.error(f"Failed to get transcription job: {e}")
            raise

    def wait_for_completion(
        self,
        job_name: str,
        max_wait_seconds: int = 300,
        poll_interval: int = 5,
    ) -> dict:
        """
        Wait for transcription job to complete.

        Args:
            job_name: Job name
            max_wait_seconds: Maximum time to wait in seconds
            poll_interval: Polling interval in seconds

        Returns:
            Completed job details

        Raises:
            TimeoutError: If job doesn't complete in time
            ClientError: If job fails
        """
        start_time = time.time()

        while True:
            job = self.get_transcription_job(job_name)
            status = job["TranscriptionJobStatus"]

            if status == "COMPLETED":
                logger.info(f"Transcription job {job_name} completed successfully")
                return job
            elif status == "FAILED":
                error_msg = f"Transcription job {job_name} failed"
                logger.error(error_msg)
                raise ClientError(
                    {"Error": {"Code": "TranscriptionFailed", "Message": error_msg}},
                    "GetTranscriptionJob",
                )

            elapsed = time.time() - start_time
            if elapsed > max_wait_seconds:
                raise TimeoutError(
                    f"Transcription job {job_name} did not complete within {max_wait_seconds}s"
                )

            time.sleep(poll_interval)

    def delete_transcription_job(self, job_name: str) -> None:
        """
        Delete a transcription job.

        Args:
            job_name: Job name

        Raises:
            ClientError: If deletion fails
        """
        try:
            self.client.delete_transcription_job(TranscriptionJobName=job_name)
            logger.info(f"Deleted transcription job: {job_name}")
        except ClientError as e:
            logger.error(f"Failed to delete transcription job: {e}")
            raise

    def transcribe_audio(
        self,
        media_uri: str,
        language_code: str = "en-US",
        media_format: str = "mp4",
        wait_for_completion: bool = True,
    ) -> str:
        """
        Transcribe audio file and return text.

        Args:
            media_uri: S3 URI of media file
            language_code: Language code
            media_format: Media format
            wait_for_completion: Whether to wait for job completion

        Returns:
            Transcribed text

        Raises:
            ClientError: If transcription fails
        """
        import uuid
        import requests

        job_name = f"transcribe-{uuid.uuid4()}"

        try:
            self.start_transcription_job(
                job_name=job_name,
                media_uri=media_uri,
                language_code=language_code,
                media_format=media_format,
            )

            if wait_for_completion:
                job = self.wait_for_completion(job_name)
                transcript_uri = job["Transcript"]["TranscriptFileUri"]

                # Download and parse transcript
                response = requests.get(transcript_uri)
                response.raise_for_status()
                transcript_data = response.json()

                text = transcript_data["results"]["transcripts"][0]["transcript"]
                logger.info(f"Successfully transcribed audio from {media_uri}")
                return text
            else:
                return job_name

        finally:
            # Clean up job
            if wait_for_completion:
                try:
                    self.delete_transcription_job(job_name)
                except Exception as e:
                    logger.warning(f"Failed to delete transcription job: {e}")
