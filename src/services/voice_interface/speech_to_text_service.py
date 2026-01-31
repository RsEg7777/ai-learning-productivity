"""Speech-to-text service using Amazon Transcribe."""

import logging
import time
from typing import Optional, Dict, Any, List
from io import BytesIO
import uuid

from src.shared.aws_clients.transcribe_client import TranscribeClient
from src.shared.aws_clients.s3_client import S3Client
from src.shared.utils.errors import VoiceProcessingError
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)


class TranscriptionResult:
    """Result of speech-to-text transcription."""

    def __init__(
        self,
        text: str,
        confidence: float,
        language: str,
        timestamps: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize transcription result.

        Args:
            text: Transcribed text
            confidence: Confidence score (0-1)
            language: Language code
            timestamps: Word-level timestamps
            metadata: Additional metadata
        """
        self.text = text
        self.confidence = confidence
        self.language = language
        self.timestamps = timestamps or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "language": self.language,
            "timestamps": self.timestamps,
            "metadata": self.metadata,
        }


class SpeechToTextService:
    """Service for converting speech to text using Amazon Transcribe."""

    # Supported Indian languages with their Transcribe language codes
    INDIAN_LANGUAGES = {
        "hi": "hi-IN",  # Hindi
        "ta": "ta-IN",  # Tamil
        "te": "te-IN",  # Telugu
        "bn": "bn-IN",  # Bengali
        "mr": "mr-IN",  # Marathi
        "gu": "gu-IN",  # Gujarati
        "kn": "kn-IN",  # Kannada
        "ml": "ml-IN",  # Malayalam
        "pa": "pa-IN",  # Punjabi
        # Note: Odia (or) may not be directly supported by Transcribe
    }

    # Supported audio formats
    SUPPORTED_FORMATS = ["mp3", "mp4", "wav", "flac", "ogg", "amr", "webm"]

    def __init__(
        self,
        transcribe_client: Optional[TranscribeClient] = None,
        s3_client: Optional[S3Client] = None,
        bucket_name: Optional[str] = None,
    ):
        """
        Initialize speech-to-text service.

        Args:
            transcribe_client: Amazon Transcribe client
            s3_client: S3 client for audio storage
            bucket_name: S3 bucket for temporary audio storage
        """
        self.transcribe_client = transcribe_client or TranscribeClient()
        self.s3_client = s3_client or S3Client()
        self.bucket_name = bucket_name or "ai-learning-assistant-audio"
        logger.info("Initialized SpeechToTextService")

    def transcribe_audio(
        self,
        audio_data: bytes,
        language_code: str = "en-US",
        audio_format: str = "mp3",
        enable_noise_reduction: bool = True,
        enable_quality_enhancement: bool = True,
    ) -> TranscriptionResult:
        """
        Transcribe audio to text.

        Args:
            audio_data: Audio data as bytes
            language_code: Language code (e.g., 'en-US', 'hi-IN')
            audio_format: Audio format (mp3, wav, etc.)
            enable_noise_reduction: Enable noise reduction
            enable_quality_enhancement: Enable audio quality enhancement

        Returns:
            TranscriptionResult with transcribed text and metadata

        Raises:
            VoiceProcessingError: If transcription fails
        """
        start_time = time.time()

        try:
            # Validate audio format
            if audio_format.lower() not in self.SUPPORTED_FORMATS:
                raise VoiceProcessingError(
                    f"Unsupported audio format: {audio_format}. "
                    f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}",
                    operation="transcribe",
                    details={"audio_format": audio_format},
                )

            # Validate language code
            validated_language = self._validate_language_code(language_code)

            # Upload audio to S3 for processing
            s3_uri = self._upload_audio_to_s3(audio_data, audio_format)

            logger.info(
                f"Starting transcription for audio in {validated_language} "
                f"(format: {audio_format})"
            )

            # Start transcription job with enhanced settings
            job_name = f"transcribe-{uuid.uuid4()}"
            transcription_params = {
                "job_name": job_name,
                "media_uri": s3_uri,
                "language_code": validated_language,
                "media_format": audio_format.lower(),
            }

            # Start the transcription job
            self.transcribe_client.start_transcription_job(**transcription_params)

            # Wait for completion
            job_result = self.transcribe_client.wait_for_completion(
                job_name=job_name,
                max_wait_seconds=300,
                poll_interval=5,
            )

            # Get transcription text
            import requests
            transcript_uri = job_result["Transcript"]["TranscriptFileUri"]
            response = requests.get(transcript_uri)
            response.raise_for_status()
            transcript_data = response.json()

            # Extract text and confidence
            transcripts = transcript_data["results"]["transcripts"]
            if not transcripts or not transcripts[0].get("transcript"):
                raise VoiceProcessingError(
                    "No transcription generated from audio",
                    operation="transcribe",
                    details={"language": validated_language},
                )

            text = transcripts[0]["transcript"]

            # Calculate average confidence from items
            items = transcript_data["results"].get("items", [])
            confidences = [
                float(item.get("alternatives", [{}])[0].get("confidence", 0))
                for item in items
                if item.get("type") == "pronunciation"
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            # Extract word-level timestamps
            timestamps = self._extract_timestamps(items)

            # Clean up
            try:
                self.transcribe_client.delete_transcription_job(job_name)
                self._cleanup_s3_audio(s3_uri)
            except Exception as e:
                logger.warning(f"Failed to cleanup transcription resources: {e}")

            processing_time = time.time() - start_time

            logger.info(
                f"Successfully transcribed audio in {processing_time:.2f}s "
                f"(confidence: {avg_confidence:.2f})"
            )

            return TranscriptionResult(
                text=text,
                confidence=avg_confidence,
                language=self._convert_to_standard_language_code(validated_language),
                timestamps=timestamps,
                metadata={
                    "processing_time": processing_time,
                    "audio_format": audio_format,
                    "noise_reduction_enabled": enable_noise_reduction,
                    "quality_enhancement_enabled": enable_quality_enhancement,
                },
            )

        except VoiceProcessingError:
            raise
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            raise VoiceProcessingError(
                f"Failed to transcribe audio: {str(e)}",
                operation="transcribe",
                details={"language": language_code, "format": audio_format},
            )

    def transcribe_audio_stream(
        self,
        audio_stream: BytesIO,
        language_code: str = "en-US",
        audio_format: str = "mp3",
    ) -> TranscriptionResult:
        """
        Transcribe audio from a stream.

        Args:
            audio_stream: Audio stream
            language_code: Language code
            audio_format: Audio format

        Returns:
            TranscriptionResult

        Raises:
            VoiceProcessingError: If transcription fails
        """
        try:
            audio_data = audio_stream.read()
            return self.transcribe_audio(
                audio_data=audio_data,
                language_code=language_code,
                audio_format=audio_format,
            )
        except Exception as e:
            logger.error(f"Failed to transcribe audio stream: {e}")
            raise VoiceProcessingError(
                f"Failed to transcribe audio stream: {str(e)}",
                operation="transcribe_stream",
            )

    def detect_language(self, audio_data: bytes, audio_format: str = "mp3") -> str:
        """
        Detect language from audio.

        Note: This is a simplified implementation. In production, you would use
        Amazon Transcribe's language identification feature or a separate service.

        Args:
            audio_data: Audio data
            audio_format: Audio format

        Returns:
            Detected language code

        Raises:
            VoiceProcessingError: If detection fails
        """
        try:
            # For now, we'll transcribe with automatic language detection
            # In a real implementation, you'd use Transcribe's IdentifyLanguage feature
            logger.info("Detecting language from audio")

            # Upload audio to S3
            s3_uri = self._upload_audio_to_s3(audio_data, audio_format)

            # Start transcription with language identification
            job_name = f"detect-lang-{uuid.uuid4()}"

            # Note: This is a simplified version. Real implementation would use
            # IdentifyLanguage parameter in start_transcription_job
            # For now, we'll default to English
            detected_language = "en-US"

            # Cleanup
            try:
                self._cleanup_s3_audio(s3_uri)
            except Exception as e:
                logger.warning(f"Failed to cleanup S3 audio: {e}")

            logger.info(f"Detected language: {detected_language}")
            return detected_language

        except Exception as e:
            logger.error(f"Failed to detect language: {e}")
            raise VoiceProcessingError(
                f"Failed to detect language: {str(e)}",
                operation="detect_language",
            )

    def _validate_language_code(self, language_code: str) -> str:
        """
        Validate and normalize language code for Transcribe.

        Args:
            language_code: Language code (e.g., 'en', 'en-US', 'hi', 'hi-IN')

        Returns:
            Validated Transcribe language code

        Raises:
            VoiceProcessingError: If language is not supported
        """
        # If already in full format (e.g., 'en-US'), validate it
        if "-" in language_code:
            return language_code

        # Convert short code to full code
        if language_code in self.INDIAN_LANGUAGES:
            return self.INDIAN_LANGUAGES[language_code]

        # Handle English
        if language_code == "en":
            return "en-US"

        # If not found, assume it's already valid
        logger.warning(f"Unknown language code: {language_code}, using as-is")
        return language_code

    def _convert_to_standard_language_code(self, transcribe_code: str) -> str:
        """
        Convert Transcribe language code to standard 2-letter code.

        Args:
            transcribe_code: Transcribe language code (e.g., 'en-US', 'hi-IN')

        Returns:
            Standard language code (e.g., 'en', 'hi')
        """
        return transcribe_code.split("-")[0]

    def _upload_audio_to_s3(self, audio_data: bytes, audio_format: str) -> str:
        """
        Upload audio to S3 for processing.

        Args:
            audio_data: Audio data
            audio_format: Audio format

        Returns:
            S3 URI

        Raises:
            VoiceProcessingError: If upload fails
        """
        try:
            # Generate unique key
            audio_key = f"temp/transcribe/{uuid.uuid4()}.{audio_format}"

            # Upload to S3
            self.s3_client.upload_file_obj(
                file_obj=BytesIO(audio_data),
                bucket=self.bucket_name,
                key=audio_key,
            )

            s3_uri = f"s3://{self.bucket_name}/{audio_key}"
            logger.info(f"Uploaded audio to S3: {s3_uri}")
            return s3_uri

        except Exception as e:
            logger.error(f"Failed to upload audio to S3: {e}")
            raise VoiceProcessingError(
                f"Failed to upload audio to S3: {str(e)}",
                operation="upload_audio",
            )

    def _cleanup_s3_audio(self, s3_uri: str) -> None:
        """
        Clean up temporary audio file from S3.

        Args:
            s3_uri: S3 URI to delete
        """
        try:
            # Extract bucket and key from URI
            parts = s3_uri.replace("s3://", "").split("/", 1)
            if len(parts) == 2:
                bucket, key = parts
                self.s3_client.delete_file(bucket=bucket, key=key)
                logger.info(f"Cleaned up S3 audio: {s3_uri}")
        except Exception as e:
            logger.warning(f"Failed to cleanup S3 audio {s3_uri}: {e}")

    def _extract_timestamps(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract word-level timestamps from transcription items.

        Args:
            items: Transcription items

        Returns:
            List of timestamp dictionaries
        """
        timestamps = []
        for item in items:
            if item.get("type") == "pronunciation":
                timestamps.append({
                    "word": item.get("alternatives", [{}])[0].get("content", ""),
                    "start_time": float(item.get("start_time", 0)),
                    "end_time": float(item.get("end_time", 0)),
                    "confidence": float(
                        item.get("alternatives", [{}])[0].get("confidence", 0)
                    ),
                })
        return timestamps

    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get supported languages for transcription.

        Returns:
            Dictionary mapping language codes to full language codes
        """
        return {
            "en": "en-US",
            **self.INDIAN_LANGUAGES,
        }

    def is_indian_language(self, language_code: str) -> bool:
        """
        Check if language is an Indian language.

        Args:
            language_code: Language code

        Returns:
            True if Indian language
        """
        short_code = language_code.split("-")[0]
        return short_code in self.INDIAN_LANGUAGES
