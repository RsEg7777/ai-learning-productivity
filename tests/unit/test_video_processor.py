"""Unit tests for video processor."""

import pytest
from io import BytesIO
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime
import tempfile
import os

from src.services.content_processing import VideoProcessor, TextProcessor
from src.services.content_processing.video_processor import VideoProcessor as VP
from src.shared.aws_clients.transcribe_client import TranscribeClient
from src.shared.aws_clients.s3_client import S3Client
from src.shared.models.content import ProcessedContent, Summary, SummaryType, Concept
from src.shared.utils.errors import (
    ContentProcessingError,
    ProcessingTimeoutError,
    ValidationError,
)


class TestVideoProcessor:
    """Test suite for VideoProcessor."""

    @pytest.fixture
    def mock_text_processor(self):
        """Create mock TextProcessor."""
        mock_processor = Mock(spec=TextProcessor)
        
        # Mock process_text to return a ProcessedContent
        mock_summary = Summary(
            id="summary123",
            content_id="content123",
            type=SummaryType.BRIEF,
            text="This is a test summary of the video content.",
            key_points=["Point 1", "Point 2", "Point 3"],
            hierarchical_structure=[],
            generated_at=datetime.utcnow(),
        )
        
        mock_processed = ProcessedContent(
            id="processed123",
            original_content="Sample transcribed text content",
            summary=mock_summary,
            key_points=["Point 1", "Point 2", "Point 3"],
            concepts=[
                Concept(
                    name="TestConcept",
                    description="A test concept",
                    importance=0.8,
                    related_concepts=[],
                )
            ],
            language="en",
            processing_time=1.5,
            metadata={"word_count": 100},
        )
        
        mock_processor.process_text.return_value = mock_processed
        return mock_processor

    @pytest.fixture
    def mock_transcribe_client(self):
        """Create mock TranscribeClient."""
        mock_client = Mock(spec=TranscribeClient)
        mock_client.transcribe_audio.return_value = "This is the transcribed text from the video."
        return mock_client

    @pytest.fixture
    def mock_s3_client(self):
        """Create mock S3Client."""
        mock_client = Mock(spec=S3Client)
        mock_client.bucket_name = "test-bucket"
        mock_client.upload_file.return_value = None
        mock_client.delete_file.return_value = None
        return mock_client

    @pytest.fixture
    def video_processor(self, mock_text_processor, mock_transcribe_client, mock_s3_client):
        """Create VideoProcessor instance."""
        return VideoProcessor(
            text_processor=mock_text_processor,
            transcribe_client=mock_transcribe_client,
            s3_client=mock_s3_client,
        )

    @pytest.fixture
    def sample_video_file(self):
        """Create a sample video file (mock BytesIO)."""
        # Create a BytesIO object with some dummy data
        video_data = b"fake video data" * 1000
        return BytesIO(video_data)

    def test_initialization(self, mock_text_processor, mock_transcribe_client, mock_s3_client):
        """Test VideoProcessor initialization."""
        processor = VideoProcessor(
            text_processor=mock_text_processor,
            transcribe_client=mock_transcribe_client,
            s3_client=mock_s3_client,
        )
        
        assert processor.text_processor == mock_text_processor
        assert processor.transcribe_client == mock_transcribe_client
        assert processor.s3_client == mock_s3_client
        assert processor.VIDEO_PROCESSING_TIMEOUT == 300

    def test_get_file_extension_valid(self, video_processor):
        """Test extracting valid file extension."""
        assert video_processor._get_file_extension("video.mp4") == ".mp4"
        assert video_processor._get_file_extension("video.MP4") == ".mp4"
        assert video_processor._get_file_extension("my.video.avi") == ".avi"

    def test_get_file_extension_invalid(self, video_processor):
        """Test extracting file extension from invalid filename."""
        with pytest.raises(ValidationError) as exc_info:
            video_processor._get_file_extension("videofile")
        
        assert "must have an extension" in str(exc_info.value)

    def test_get_audio_format(self, video_processor):
        """Test getting audio format from file path."""
        assert video_processor._get_audio_format("/tmp/audio.mp3") == "mp3"
        assert video_processor._get_audio_format("/tmp/audio.wav") == "wav"
        assert video_processor._get_audio_format("/tmp/audio.m4a") == "m4a"

    def test_convert_language_code(self, video_processor):
        """Test converting Transcribe language codes to standard codes."""
        assert video_processor._convert_language_code("en-US") == "en"
        assert video_processor._convert_language_code("hi-IN") == "hi"
        assert video_processor._convert_language_code("en") == "en"

    def test_check_timeout_not_exceeded(self, video_processor):
        """Test timeout check when not exceeded."""
        import time
        start_time = time.time()
        
        # Should not raise exception
        video_processor._check_timeout(start_time, 10, "video")

    def test_check_timeout_exceeded(self, video_processor):
        """Test timeout check when exceeded."""
        import time
        start_time = time.time() - 11  # 11 seconds ago
        
        with pytest.raises(ProcessingTimeoutError) as exc_info:
            video_processor._check_timeout(start_time, 10, "video")
        
        assert "video" in str(exc_info.value)

    @patch("tempfile.mkstemp")
    @patch("os.write")
    @patch("os.close")
    def test_save_to_temp_file(
        self,
        mock_close,
        mock_write,
        mock_mkstemp,
        video_processor,
        sample_video_file,
    ):
        """Test saving BytesIO to temporary file."""
        mock_mkstemp.return_value = (123, "/tmp/test_video.mp4")
        
        result = video_processor._save_to_temp_file(sample_video_file, ".mp4")
        
        assert result == "/tmp/test_video.mp4"
        mock_mkstemp.assert_called_once_with(suffix=".mp4")
        mock_write.assert_called_once()
        mock_close.assert_called_once_with(123)

    @patch("os.path.exists")
    @patch("os.remove")
    def test_cleanup_temp_file_exists(self, mock_remove, mock_exists, video_processor):
        """Test cleaning up existing temporary file."""
        mock_exists.return_value = True
        
        video_processor._cleanup_temp_file("/tmp/test_file.mp4")
        
        mock_exists.assert_called_once_with("/tmp/test_file.mp4")
        mock_remove.assert_called_once_with("/tmp/test_file.mp4")

    @patch("os.path.exists")
    @patch("os.remove")
    def test_cleanup_temp_file_not_exists(self, mock_remove, mock_exists, video_processor):
        """Test cleaning up non-existent temporary file."""
        mock_exists.return_value = False
        
        video_processor._cleanup_temp_file("/tmp/test_file.mp4")
        
        mock_exists.assert_called_once_with("/tmp/test_file.mp4")
        mock_remove.assert_not_called()

    def test_cleanup_temp_file_none(self, video_processor):
        """Test cleaning up None file path."""
        # Should not raise exception
        video_processor._cleanup_temp_file(None)

    @patch("subprocess.run")
    @patch("tempfile.mkstemp")
    @patch("os.close")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_extract_audio_success(
        self,
        mock_getsize,
        mock_exists,
        mock_close,
        mock_mkstemp,
        mock_run,
        video_processor,
    ):
        """Test successful audio extraction from video."""
        # Setup mocks
        mock_mkstemp.return_value = (456, "/tmp/audio.mp3")
        mock_exists.return_value = True
        mock_getsize.return_value = 50000
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        # Test extraction
        result = video_processor._extract_audio("/tmp/video.mp4")
        
        assert result == "/tmp/audio.mp3"
        mock_run.assert_called_once()
        
        # Verify ffmpeg command
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "ffmpeg"
        assert "-i" in call_args
        assert "/tmp/video.mp4" in call_args

    @patch("subprocess.run")
    @patch("tempfile.mkstemp")
    @patch("os.close")
    def test_extract_audio_ffmpeg_error(
        self,
        mock_close,
        mock_mkstemp,
        mock_run,
        video_processor,
    ):
        """Test audio extraction with ffmpeg error."""
        mock_mkstemp.return_value = (456, "/tmp/audio.mp3")
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "ffmpeg error: invalid input"
        mock_run.return_value = mock_result
        
        with pytest.raises(ContentProcessingError) as exc_info:
            video_processor._extract_audio("/tmp/video.mp4")
        
        assert "Failed to extract audio" in str(exc_info.value)

    @patch("subprocess.run")
    @patch("tempfile.mkstemp")
    @patch("os.close")
    def test_extract_audio_timeout(
        self,
        mock_close,
        mock_mkstemp,
        mock_run,
        video_processor,
    ):
        """Test audio extraction timeout."""
        import subprocess
        
        mock_mkstemp.return_value = (456, "/tmp/audio.mp3")
        mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 60)
        
        with pytest.raises(ContentProcessingError) as exc_info:
            video_processor._extract_audio("/tmp/video.mp4")
        
        assert "timed out" in str(exc_info.value).lower()

    @patch("builtins.open", new_callable=mock_open, read_data=b"audio data")
    def test_upload_audio_to_s3_success(
        self,
        mock_file,
        video_processor,
        mock_s3_client,
    ):
        """Test successful audio upload to S3."""
        result = video_processor._upload_audio_to_s3("/tmp/audio.mp3")
        
        assert result.startswith("temp/transcribe/")
        assert result.endswith(".mp3")
        mock_s3_client.upload_file.assert_called_once()

    @patch("builtins.open", side_effect=IOError("File not found"))
    def test_upload_audio_to_s3_error(
        self,
        mock_file,
        video_processor,
    ):
        """Test audio upload to S3 with error."""
        with pytest.raises(ContentProcessingError) as exc_info:
            video_processor._upload_audio_to_s3("/tmp/audio.mp3")
        
        assert "Failed to upload audio to S3" in str(exc_info.value)

    def test_transcribe_audio_success(
        self,
        video_processor,
        mock_transcribe_client,
    ):
        """Test successful audio transcription."""
        result = video_processor._transcribe_audio(
            s3_audio_uri="s3://bucket/audio.mp3",
            language_code="en-US",
            media_format="mp3",
        )
        
        assert result == "This is the transcribed text from the video."
        mock_transcribe_client.transcribe_audio.assert_called_once_with(
            media_uri="s3://bucket/audio.mp3",
            language_code="en-US",
            media_format="mp3",
            wait_for_completion=True,
        )

    def test_transcribe_audio_timeout(
        self,
        video_processor,
        mock_transcribe_client,
    ):
        """Test audio transcription timeout."""
        mock_transcribe_client.transcribe_audio.side_effect = TimeoutError("Transcription timeout")
        
        with pytest.raises(ContentProcessingError) as exc_info:
            video_processor._transcribe_audio(
                s3_audio_uri="s3://bucket/audio.mp3",
                language_code="en-US",
                media_format="mp3",
            )
        
        assert "timed out" in str(exc_info.value).lower()

    def test_transcribe_audio_error(
        self,
        video_processor,
        mock_transcribe_client,
    ):
        """Test audio transcription with error."""
        mock_transcribe_client.transcribe_audio.side_effect = Exception("Transcription failed")
        
        with pytest.raises(ContentProcessingError) as exc_info:
            video_processor._transcribe_audio(
                s3_audio_uri="s3://bucket/audio.mp3",
                language_code="en-US",
                media_format="mp3",
            )
        
        assert "Failed to transcribe audio" in str(exc_info.value)

    @patch.object(VP, "_save_to_temp_file")
    @patch.object(VP, "_extract_audio")
    @patch.object(VP, "_upload_audio_to_s3")
    @patch.object(VP, "_transcribe_audio")
    @patch.object(VP, "_cleanup_temp_file")
    @patch.object(VP, "_get_audio_format")
    def test_process_video_success(
        self,
        mock_get_audio_format,
        mock_cleanup,
        mock_transcribe,
        mock_upload,
        mock_extract,
        mock_save,
        video_processor,
        sample_video_file,
        mock_text_processor,
        mock_s3_client,
    ):
        """Test successful video processing."""
        # Setup mocks
        mock_save.return_value = "/tmp/video.mp4"
        mock_extract.return_value = "/tmp/audio.mp3"
        mock_upload.return_value = "temp/transcribe/audio123.mp3"
        mock_transcribe.return_value = "This is the transcribed text from the video."
        mock_get_audio_format.return_value = "mp3"
        
        # Process video
        result = video_processor.process_video(
            video_file=sample_video_file,
            filename="test_video.mp4",
            language="en-US",
        )
        
        # Verify result
        assert isinstance(result, ProcessedContent)
        assert result.metadata["source_type"] == "video"
        assert result.metadata["original_filename"] == "test_video.mp4"
        assert result.metadata["video_format"] == ".mp4"
        assert result.metadata["audio_format"] == "mp3"
        
        # Verify method calls
        mock_save.assert_called_once()
        mock_extract.assert_called_once_with("/tmp/video.mp4")
        mock_upload.assert_called_once_with("/tmp/audio.mp3")
        mock_transcribe.assert_called_once()
        mock_text_processor.process_text.assert_called_once()
        
        # Verify cleanup
        assert mock_cleanup.call_count == 2  # video and audio files
        mock_s3_client.delete_file.assert_called_once()

    def test_process_video_unsupported_format(
        self,
        video_processor,
        sample_video_file,
    ):
        """Test processing video with unsupported format."""
        with pytest.raises(ValidationError) as exc_info:
            video_processor.process_video(
                video_file=sample_video_file,
                filename="test_video.xyz",
            )
        
        assert "Unsupported video format" in str(exc_info.value)

    @patch.object(VP, "_save_to_temp_file")
    @patch.object(VP, "_extract_audio")
    @patch.object(VP, "_upload_audio_to_s3")
    @patch.object(VP, "_transcribe_audio")
    @patch.object(VP, "_cleanup_temp_file")
    @patch.object(VP, "_get_audio_format")
    def test_process_video_empty_transcription(
        self,
        mock_get_audio_format,
        mock_cleanup,
        mock_transcribe,
        mock_upload,
        mock_extract,
        mock_save,
        video_processor,
        sample_video_file,
        mock_s3_client,
    ):
        """Test processing video with empty transcription."""
        # Setup mocks
        mock_save.return_value = "/tmp/video.mp4"
        mock_extract.return_value = "/tmp/audio.mp3"
        mock_upload.return_value = "temp/transcribe/audio123.mp3"
        mock_transcribe.return_value = ""  # Empty transcription
        mock_get_audio_format.return_value = "mp3"
        
        with pytest.raises(ContentProcessingError) as exc_info:
            video_processor.process_video(
                video_file=sample_video_file,
                filename="test_video.mp4",
            )
        
        assert "No speech detected" in str(exc_info.value)

    @patch.object(VP, "_save_to_temp_file")
    @patch.object(VP, "_extract_audio")
    @patch.object(VP, "_cleanup_temp_file")
    def test_extract_audio_only_success(
        self,
        mock_cleanup,
        mock_extract,
        mock_save,
        video_processor,
        sample_video_file,
    ):
        """Test extracting audio only without transcription."""
        # Setup mocks
        mock_save.return_value = "/tmp/video.mp4"
        mock_extract.return_value = "/tmp/audio.mp3"
        
        # Mock file reading
        with patch("builtins.open", mock_open(read_data=b"audio data")):
            result = video_processor.extract_audio_only(
                video_file=sample_video_file,
                filename="test_video.mp4",
            )
        
        assert isinstance(result, BytesIO)
        assert result.read() == b"audio data"
        
        # Verify cleanup
        assert mock_cleanup.call_count == 2

    @patch.object(VP, "_save_to_temp_file")
    @patch("subprocess.run")
    @patch.object(VP, "_cleanup_temp_file")
    def test_get_video_metadata_success(
        self,
        mock_cleanup,
        mock_run,
        mock_save,
        video_processor,
        sample_video_file,
    ):
        """Test extracting video metadata."""
        # Setup mocks
        mock_save.return_value = "/tmp/video.mp4"
        
        # Mock ffprobe output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """{
            "format": {
                "duration": "120.5",
                "size": "10485760",
                "bit_rate": "1000000"
            },
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1"
                }
            ]
        }"""
        mock_run.return_value = mock_result
        
        result = video_processor.get_video_metadata(
            video_file=sample_video_file,
            filename="test_video.mp4",
        )
        
        assert result["format"] == ".mp4"
        assert result["filename"] == "test_video.mp4"
        assert result["duration"] == 120.5
        assert result["size"] == 10485760
        assert result["video_codec"] == "h264"
        assert result["width"] == 1920
        assert result["height"] == 1080
        
        mock_cleanup.assert_called_once()

    @patch.object(VP, "_save_to_temp_file")
    @patch("subprocess.run")
    @patch.object(VP, "_cleanup_temp_file")
    def test_get_video_metadata_error(
        self,
        mock_cleanup,
        mock_run,
        mock_save,
        video_processor,
        sample_video_file,
    ):
        """Test video metadata extraction with error."""
        mock_save.return_value = "/tmp/video.mp4"
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        with pytest.raises(ContentProcessingError) as exc_info:
            video_processor.get_video_metadata(
                video_file=sample_video_file,
                filename="test_video.mp4",
            )
        
        assert "Failed to extract video metadata" in str(exc_info.value)


class TestVideoProcessorIntegration:
    """Integration tests for VideoProcessor with edge cases."""

    @pytest.fixture
    def video_processor_integration(self):
        """Create VideoProcessor with real dependencies for integration testing."""
        mock_text_processor = Mock(spec=TextProcessor)
        mock_transcribe_client = Mock(spec=TranscribeClient)
        mock_s3_client = Mock(spec=S3Client)
        
        mock_s3_client.bucket_name = "test-bucket"
        
        return VideoProcessor(
            text_processor=mock_text_processor,
            transcribe_client=mock_transcribe_client,
            s3_client=mock_s3_client,
        )

    def test_supported_video_formats(self, video_processor_integration):
        """Test that all supported video formats are recognized."""
        supported_formats = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
        
        for fmt in supported_formats:
            assert fmt in video_processor_integration.SUPPORTED_VIDEO_FORMATS

    def test_processing_timeout_constant(self, video_processor_integration):
        """Test that video processing timeout is set to 5 minutes (300 seconds)."""
        assert video_processor_integration.VIDEO_PROCESSING_TIMEOUT == 300
