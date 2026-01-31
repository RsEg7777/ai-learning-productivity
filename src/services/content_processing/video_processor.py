"""Video content processing service with Amazon Transcribe."""

import logging
import time
import uuid
import subprocess
import tempfile
import os
from io import BytesIO
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

from .text_processor import TextProcessor
from ...shared.aws_clients.transcribe_client import TranscribeClient
from ...shared.aws_clients.s3_client import S3Client
from ...shared.models.content import (
    ProcessedContent,
    SummaryType,
)
from ...shared.utils.errors import (
    ContentProcessingError,
    ProcessingTimeoutError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Service for processing video content with Amazon Transcribe."""

    # Processing time limits (in seconds)
    VIDEO_PROCESSING_TIMEOUT = 300  # 5 minutes

    # Supported video formats
    SUPPORTED_VIDEO_FORMATS = [".mp4", ".avi", ".mov", ".mkv", ".webm"]

    # Supported audio formats for extraction
    AUDIO_FORMATS = ["mp3", "wav", "m4a", "flac"]

    def __init__(
        self,
        text_processor: TextProcessor,
        transcribe_client: TranscribeClient,
        s3_client: S3Client,
    ) -> None:
        """
        Initialize video processor.

        Args:
            text_processor: TextProcessor instance for text analysis
            transcribe_client: TranscribeClient for speech-to-text
            s3_client: S3Client for temporary file storage
        """
        self.text_processor = text_processor
        self.transcribe_client = transcribe_client
        self.s3_client = s3_client
        logger.info("Initialized VideoProcessor")

    def process_video(
        self,
        video_file: BytesIO,
        filename: str,
        language: str = "en-US",
        summary_type: Optional[SummaryType] = None,
    ) -> ProcessedContent:
        """
        Process video content with audio extraction and transcription.

        This method:
        1. Validates video file format
        2. Extracts audio from video
        3. Uploads audio to S3 for Transcribe processing
        4. Transcribes audio using Amazon Transcribe
        5. Generates summary from transcribed text
        6. Returns ProcessedContent within 5-minute timeout

        Args:
            video_file: Video file as BytesIO object
            filename: Original filename
            language: Language code (default: "en-US")
            summary_type: Type of summary to generate (auto-detected if None)

        Returns:
            ProcessedContent with summary, key points, and concepts

        Raises:
            ContentProcessingError: If processing fails
            ProcessingTimeoutError: If processing exceeds 5 minutes
            ValidationError: If video format is invalid
        """
        start_time = time.time()
        temp_video_path = None
        temp_audio_path = None
        s3_audio_key = None

        try:
            logger.info(f"Starting video processing: {filename}, language: {language}")

            # Validate video format
            file_extension = self._get_file_extension(filename)
            if file_extension not in self.SUPPORTED_VIDEO_FORMATS:
                raise ValidationError(
                    message=f"Unsupported video format: {file_extension}",
                    field="video_format",
                    details={
                        "supported_formats": self.SUPPORTED_VIDEO_FORMATS,
                    },
                )

            # Check timeout
            self._check_timeout(start_time, self.VIDEO_PROCESSING_TIMEOUT, "video")

            # Save video to temporary file
            temp_video_path = self._save_to_temp_file(video_file, file_extension)
            logger.info(f"Saved video to temporary file: {temp_video_path}")

            # Extract audio from video
            temp_audio_path = self._extract_audio(temp_video_path)
            logger.info(f"Extracted audio to: {temp_audio_path}")

            # Check timeout after audio extraction
            self._check_timeout(start_time, self.VIDEO_PROCESSING_TIMEOUT, "video")

            # Upload audio to S3 for Transcribe
            s3_audio_key = self._upload_audio_to_s3(temp_audio_path)
            s3_audio_uri = f"s3://{self.s3_client.bucket_name}/{s3_audio_key}"
            logger.info(f"Uploaded audio to S3: {s3_audio_uri}")

            # Check timeout before transcription
            self._check_timeout(start_time, self.VIDEO_PROCESSING_TIMEOUT, "video")

            # Transcribe audio using Amazon Transcribe
            audio_format = self._get_audio_format(temp_audio_path)
            transcribed_text = self._transcribe_audio(
                s3_audio_uri=s3_audio_uri,
                language_code=language,
                media_format=audio_format,
            )
            logger.info(f"Transcribed {len(transcribed_text)} characters of text")

            # Check timeout after transcription
            self._check_timeout(start_time, self.VIDEO_PROCESSING_TIMEOUT, "video")

            # Validate transcribed text
            if not transcribed_text or not transcribed_text.strip():
                raise ContentProcessingError(
                    message="No speech detected in video",
                    content_type="video",
                )

            # Process transcribed text using TextProcessor
            # Calculate remaining time for text processing
            remaining_time = self.VIDEO_PROCESSING_TIMEOUT - (time.time() - start_time)
            if remaining_time < 10:
                raise ProcessingTimeoutError(
                    content_type="video",
                    time_limit=self.VIDEO_PROCESSING_TIMEOUT,
                    time_elapsed=int(time.time() - start_time),
                )

            processed_content = self.text_processor.process_text(
                text=transcribed_text,
                language=self._convert_language_code(language),
                summary_type=summary_type,
            )

            # Add video-specific metadata
            processed_content.metadata.update({
                "source_type": "video",
                "original_filename": filename,
                "video_format": file_extension,
                "audio_format": audio_format,
                "transcription_language": language,
                "transcribed_text_length": len(transcribed_text),
            })

            # Calculate final processing time
            processing_time = time.time() - start_time
            processed_content.processing_time = processing_time

            logger.info(
                f"Successfully processed video in {processing_time:.2f}s "
                f"(transcribed: {len(transcribed_text)} chars)"
            )

            return processed_content

        except (ProcessingTimeoutError, ValidationError):
            raise
        except ContentProcessingError:
            raise
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Error processing video: {e}")
            raise ContentProcessingError(
                message=f"Failed to process video: {str(e)}",
                content_type="video",
                details={"elapsed_time": elapsed_time},
            )

        finally:
            # Clean up temporary files
            self._cleanup_temp_file(temp_video_path)
            self._cleanup_temp_file(temp_audio_path)

            # Clean up S3 audio file
            if s3_audio_key:
                try:
                    self.s3_client.delete_file(s3_audio_key)
                    logger.debug(f"Cleaned up S3 audio file: {s3_audio_key}")
                except Exception as e:
                    logger.warning(f"Failed to clean up S3 audio file: {e}")

    def _extract_audio(self, video_path: str) -> str:
        """
        Extract audio from video file using ffmpeg.

        Args:
            video_path: Path to video file

        Returns:
            Path to extracted audio file

        Raises:
            ContentProcessingError: If extraction fails
        """
        try:
            # Create temporary file for audio
            audio_fd, audio_path = tempfile.mkstemp(suffix=".mp3")
            os.close(audio_fd)

            # Use ffmpeg to extract audio
            # -i: input file
            # -vn: disable video
            # -acodec: audio codec
            # -ar: audio sample rate
            # -ac: audio channels
            # -ab: audio bitrate
            # -y: overwrite output file
            command = [
                "ffmpeg",
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "libmp3lame",  # MP3 codec
                "-ar", "16000",  # 16kHz sample rate (good for speech)
                "-ac", "1",  # Mono
                "-ab", "64k",  # 64kbps bitrate
                "-y",  # Overwrite
                audio_path,
            ]

            # Run ffmpeg
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60,  # 1 minute timeout for extraction
            )

            if result.returncode != 0:
                logger.error(f"ffmpeg error: {result.stderr}")
                raise ContentProcessingError(
                    message="Failed to extract audio from video",
                    content_type="video",
                    details={"ffmpeg_error": result.stderr},
                )

            # Verify audio file was created
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                raise ContentProcessingError(
                    message="Audio extraction produced empty file",
                    content_type="video",
                )

            logger.info(f"Successfully extracted audio: {os.path.getsize(audio_path)} bytes")
            return audio_path

        except subprocess.TimeoutExpired:
            raise ContentProcessingError(
                message="Audio extraction timed out",
                content_type="video",
            )
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise ContentProcessingError(
                message=f"Failed to extract audio: {str(e)}",
                content_type="video",
            )

    def _upload_audio_to_s3(self, audio_path: str) -> str:
        """
        Upload audio file to S3 for Transcribe processing.

        Args:
            audio_path: Path to audio file

        Returns:
            S3 key of uploaded file

        Raises:
            ContentProcessingError: If upload fails
        """
        try:
            # Generate unique S3 key
            audio_id = str(uuid.uuid4())
            s3_key = f"temp/transcribe/{audio_id}.mp3"

            # Upload file to S3
            with open(audio_path, "rb") as audio_file:
                self.s3_client.upload_file(
                    file_obj=audio_file,
                    key=s3_key,
                    content_type="audio/mpeg",
                )

            logger.info(f"Uploaded audio to S3: {s3_key}")
            return s3_key

        except Exception as e:
            logger.error(f"Error uploading audio to S3: {e}")
            raise ContentProcessingError(
                message=f"Failed to upload audio to S3: {str(e)}",
                content_type="video",
            )

    def _transcribe_audio(
        self,
        s3_audio_uri: str,
        language_code: str,
        media_format: str,
    ) -> str:
        """
        Transcribe audio using Amazon Transcribe.

        Args:
            s3_audio_uri: S3 URI of audio file
            language_code: Language code (e.g., 'en-US', 'hi-IN')
            media_format: Audio format (mp3, wav, etc.)

        Returns:
            Transcribed text

        Raises:
            ContentProcessingError: If transcription fails
        """
        try:
            # Transcribe audio
            transcribed_text = self.transcribe_client.transcribe_audio(
                media_uri=s3_audio_uri,
                language_code=language_code,
                media_format=media_format,
                wait_for_completion=True,
            )

            return transcribed_text

        except TimeoutError as e:
            logger.error(f"Transcription timeout: {e}")
            raise ContentProcessingError(
                message="Transcription timed out",
                content_type="video",
            )
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise ContentProcessingError(
                message=f"Failed to transcribe audio: {str(e)}",
                content_type="video",
            )

    def _save_to_temp_file(self, file_obj: BytesIO, extension: str) -> str:
        """
        Save BytesIO object to temporary file.

        Args:
            file_obj: File object
            extension: File extension

        Returns:
            Path to temporary file
        """
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix=extension)

        try:
            # Write file content
            file_obj.seek(0)
            os.write(fd, file_obj.read())
            os.close(fd)

            return temp_path

        except Exception as e:
            os.close(fd)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    def _cleanup_temp_file(self, file_path: Optional[str]) -> None:
        """
        Clean up temporary file.

        Args:
            file_path: Path to temporary file
        """
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {file_path}: {e}")

    def _get_file_extension(self, filename: str) -> str:
        """
        Extract file extension from filename.

        Args:
            filename: Filename with extension

        Returns:
            File extension (e.g., '.mp4')
        """
        if "." not in filename:
            raise ValidationError(
                message="Filename must have an extension",
                field="filename",
            )

        extension = "." + filename.rsplit(".", 1)[1].lower()
        return extension

    def _get_audio_format(self, audio_path: str) -> str:
        """
        Get audio format from file path.

        Args:
            audio_path: Path to audio file

        Returns:
            Audio format (e.g., 'mp3')
        """
        extension = Path(audio_path).suffix.lower()
        # Remove leading dot
        return extension[1:] if extension.startswith(".") else extension

    def _convert_language_code(self, transcribe_language_code: str) -> str:
        """
        Convert Transcribe language code to standard language code.

        Transcribe uses codes like 'en-US', 'hi-IN'
        TextProcessor uses codes like 'en', 'hi'

        Args:
            transcribe_language_code: Transcribe language code

        Returns:
            Standard language code
        """
        # Extract base language code (before hyphen)
        if "-" in transcribe_language_code:
            return transcribe_language_code.split("-")[0]
        return transcribe_language_code

    def _check_timeout(
        self,
        start_time: float,
        timeout: int,
        content_type: str,
    ) -> None:
        """
        Check if processing has exceeded timeout.

        Args:
            start_time: Processing start time
            timeout: Timeout in seconds
            content_type: Content type for error message

        Raises:
            ProcessingTimeoutError: If timeout exceeded
        """
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            raise ProcessingTimeoutError(
                content_type=content_type,
                time_limit=timeout,
                time_elapsed=int(elapsed_time),
            )

    def extract_audio_only(
        self,
        video_file: BytesIO,
        filename: str,
    ) -> BytesIO:
        """
        Extract audio from video without transcription.

        Useful for getting audio file for other purposes.

        Args:
            video_file: Video file as BytesIO object
            filename: Original filename

        Returns:
            Audio file as BytesIO object

        Raises:
            ContentProcessingError: If extraction fails
        """
        temp_video_path = None
        temp_audio_path = None

        try:
            # Validate video format
            file_extension = self._get_file_extension(filename)
            if file_extension not in self.SUPPORTED_VIDEO_FORMATS:
                raise ValidationError(
                    message=f"Unsupported video format: {file_extension}",
                    field="video_format",
                )

            # Save video to temporary file
            temp_video_path = self._save_to_temp_file(video_file, file_extension)

            # Extract audio
            temp_audio_path = self._extract_audio(temp_video_path)

            # Read audio file into BytesIO
            with open(temp_audio_path, "rb") as audio_file:
                audio_data = BytesIO(audio_file.read())

            return audio_data

        finally:
            # Clean up temporary files
            self._cleanup_temp_file(temp_video_path)
            self._cleanup_temp_file(temp_audio_path)

    def get_video_metadata(
        self,
        video_file: BytesIO,
        filename: str,
    ) -> Dict[str, Any]:
        """
        Extract metadata from video file.

        Args:
            video_file: Video file as BytesIO object
            filename: Original filename

        Returns:
            Dictionary with video metadata

        Raises:
            ContentProcessingError: If metadata extraction fails
        """
        temp_video_path = None

        try:
            # Validate video format
            file_extension = self._get_file_extension(filename)
            if file_extension not in self.SUPPORTED_VIDEO_FORMATS:
                raise ValidationError(
                    message=f"Unsupported video format: {file_extension}",
                    field="video_format",
                )

            # Save video to temporary file
            temp_video_path = self._save_to_temp_file(video_file, file_extension)

            # Use ffprobe to get metadata
            command = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                temp_video_path,
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise ContentProcessingError(
                    message="Failed to extract video metadata",
                    content_type="video",
                )

            # Parse JSON output
            import json
            metadata = json.loads(result.stdout)

            # Extract relevant information
            video_info = {
                "format": file_extension,
                "filename": filename,
            }

            if "format" in metadata:
                format_info = metadata["format"]
                if "duration" in format_info:
                    video_info["duration"] = float(format_info["duration"])
                if "size" in format_info:
                    video_info["size"] = int(format_info["size"])
                if "bit_rate" in format_info:
                    video_info["bit_rate"] = int(format_info["bit_rate"])

            # Extract video stream info
            if "streams" in metadata:
                for stream in metadata["streams"]:
                    if stream.get("codec_type") == "video":
                        video_info["video_codec"] = stream.get("codec_name")
                        video_info["width"] = stream.get("width")
                        video_info["height"] = stream.get("height")
                        video_info["fps"] = stream.get("r_frame_rate")
                        break

            return video_info

        except subprocess.TimeoutExpired:
            raise ContentProcessingError(
                message="Metadata extraction timed out",
                content_type="video",
            )
        except Exception as e:
            logger.error(f"Error extracting video metadata: {e}")
            raise ContentProcessingError(
                message=f"Failed to extract video metadata: {str(e)}",
                content_type="video",
            )

        finally:
            # Clean up temporary file
            self._cleanup_temp_file(temp_video_path)
