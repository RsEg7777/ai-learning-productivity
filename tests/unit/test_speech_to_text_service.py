"""Unit tests for speech-to-text service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from src.services.voice_interface import (
    SpeechToTextService,
    TranscriptionResult,
)
from src.shared.aws_clients.transcribe_client import TranscribeClient
from src.shared.aws_clients.s3_client import S3Client
from src.shared.utils.errors import VoiceProcessingError


class TestSpeechToTextService:
    """Test suite for SpeechToTextService."""

    @pytest.fixture
    def mock_transcribe_client(self):
        """Create mock TranscribeClient."""
        mock_client = Mock(spec=TranscribeClient)
        return mock_client

    @pytest.fixture
    def mock_s3_client(self):
        """Create mock S3Client."""
        mock_client = Mock(spec=S3Client)
        return mock_client

    @pytest.fixture
    def speech_service(self, mock_transcribe_client, mock_s3_client):
        """Create SpeechToTextService instance."""
        return SpeechToTextService(
            transcribe_client=mock_transcribe_client,
            s3_client=mock_s3_client,
            bucket_name="test-bucket",
        )

    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data."""
        return b"fake audio data for testing"

    def test_initialization(self, mock_transcribe_client, mock_s3_client):
        """Test SpeechToTextService initialization."""
        service = SpeechToTextService(
            transcribe_client=mock_transcribe_client,
            s3_client=mock_s3_client,
            bucket_name="test-bucket",
        )

        assert service.transcribe_client == mock_transcribe_client
        assert service.s3_client == mock_s3_client
        assert service.bucket_name == "test-bucket"

    def test_supported_languages(self, speech_service):
        """Test getting supported languages."""
        languages = speech_service.get_supported_languages()

        assert "en" in languages
        assert "hi" in languages
        assert "ta" in languages
        assert languages["en"] == "en-US"
        assert languages["hi"] == "hi-IN"

    def test_is_indian_language(self, speech_service):
        """Test checking if language is Indian."""
        assert speech_service.is_indian_language("hi-IN") is True
        assert speech_service.is_indian_language("ta-IN") is True
        assert speech_service.is_indian_language("en-US") is False
        assert speech_service.is_indian_language("en") is False

    def test_validate_language_code_short_code(self, speech_service):
        """Test validating short language codes."""
        assert speech_service._validate_language_code("en") == "en-US"
        assert speech_service._validate_language_code("hi") == "hi-IN"
        assert speech_service._validate_language_code("ta") == "ta-IN"

    def test_validate_language_code_full_code(self, speech_service):
        """Test validating full language codes."""
        assert speech_service._validate_language_code("en-US") == "en-US"
        assert speech_service._validate_language_code("hi-IN") == "hi-IN"

    def test_convert_to_standard_language_code(self, speech_service):
        """Test converting Transcribe codes to standard codes."""
        assert speech_service._convert_to_standard_language_code("en-US") == "en"
        assert speech_service._convert_to_standard_language_code("hi-IN") == "hi"
        assert speech_service._convert_to_standard_language_code("ta-IN") == "ta"

    @patch("src.services.voice_interface.speech_to_text_service.uuid.uuid4")
    def test_upload_audio_to_s3_success(
        self,
        mock_uuid,
        speech_service,
        mock_s3_client,
        sample_audio_data,
    ):
        """Test successful audio upload to S3."""
        mock_uuid.return_value = "test-uuid-123"
        mock_s3_client.upload_file_obj.return_value = "s3://test-bucket/temp/transcribe/test-uuid-123.mp3"

        result = speech_service._upload_audio_to_s3(sample_audio_data, "mp3")

        assert result == "s3://test-bucket/temp/transcribe/test-uuid-123.mp3"
        mock_s3_client.upload_file_obj.assert_called_once()

    def test_upload_audio_to_s3_failure(
        self,
        speech_service,
        mock_s3_client,
        sample_audio_data,
    ):
        """Test audio upload failure."""
        mock_s3_client.upload_file_obj.side_effect = Exception("S3 upload failed")

        with pytest.raises(VoiceProcessingError) as exc_info:
            speech_service._upload_audio_to_s3(sample_audio_data, "mp3")

        assert "Failed to upload audio to S3" in str(exc_info.value)

    def test_cleanup_s3_audio_success(self, speech_service, mock_s3_client):
        """Test successful S3 audio cleanup."""
        s3_uri = "s3://test-bucket/temp/transcribe/audio123.mp3"

        speech_service._cleanup_s3_audio(s3_uri)

        mock_s3_client.delete_file.assert_called_once_with(
            bucket="test-bucket",
            key="temp/transcribe/audio123.mp3",
        )

    def test_cleanup_s3_audio_failure(self, speech_service, mock_s3_client):
        """Test S3 audio cleanup failure (should not raise)."""
        mock_s3_client.delete_file.side_effect = Exception("Delete failed")
        s3_uri = "s3://test-bucket/temp/transcribe/audio123.mp3"

        # Should not raise exception
        speech_service._cleanup_s3_audio(s3_uri)

    def test_extract_timestamps(self, speech_service):
        """Test extracting timestamps from transcription items."""
        items = [
            {
                "type": "pronunciation",
                "alternatives": [{"content": "hello", "confidence": "0.99"}],
                "start_time": "0.0",
                "end_time": "0.5",
            },
            {
                "type": "pronunciation",
                "alternatives": [{"content": "world", "confidence": "0.98"}],
                "start_time": "0.6",
                "end_time": "1.0",
            },
            {
                "type": "punctuation",
                "alternatives": [{"content": "."}],
            },
        ]

        timestamps = speech_service._extract_timestamps(items)

        assert len(timestamps) == 2
        assert timestamps[0]["word"] == "hello"
        assert timestamps[0]["confidence"] == 0.99
        assert timestamps[1]["word"] == "world"
        assert timestamps[1]["confidence"] == 0.98

    @patch("requests.get")
    @patch("src.services.voice_interface.speech_to_text_service.uuid.uuid4")
    def test_transcribe_audio_success(
        self,
        mock_uuid,
        mock_requests_get,
        speech_service,
        mock_transcribe_client,
        mock_s3_client,
        sample_audio_data,
    ):
        """Test successful audio transcription."""
        mock_uuid.return_value = "test-uuid-123"
        mock_s3_client.upload_file_obj.return_value = "s3://test-bucket/audio.mp3"

        # Mock transcription job result
        mock_transcribe_client.wait_for_completion.return_value = {
            "Transcript": {
                "TranscriptFileUri": "https://example.com/transcript.json"
            }
        }

        # Mock transcript download
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": {
                "transcripts": [{"transcript": "Hello world"}],
                "items": [
                    {
                        "type": "pronunciation",
                        "alternatives": [{"content": "Hello", "confidence": "0.99"}],
                        "start_time": "0.0",
                        "end_time": "0.5",
                    },
                    {
                        "type": "pronunciation",
                        "alternatives": [{"content": "world", "confidence": "0.98"}],
                        "start_time": "0.6",
                        "end_time": "1.0",
                    },
                ],
            }
        }
        mock_requests_get.return_value = mock_response

        result = speech_service.transcribe_audio(
            audio_data=sample_audio_data,
            language_code="en-US",
            audio_format="mp3",
        )

        assert isinstance(result, TranscriptionResult)
        assert result.text == "Hello world"
        assert result.confidence > 0.9
        assert result.language == "en"
        assert len(result.timestamps) == 2

        mock_transcribe_client.start_transcription_job.assert_called_once()
        mock_transcribe_client.wait_for_completion.assert_called_once()
        mock_transcribe_client.delete_transcription_job.assert_called_once()

    @patch("src.services.voice_interface.speech_to_text_service.uuid.uuid4")
    def test_transcribe_audio_unsupported_format(
        self,
        mock_uuid,
        speech_service,
        sample_audio_data,
    ):
        """Test transcription with unsupported format."""
        with pytest.raises(VoiceProcessingError) as exc_info:
            speech_service.transcribe_audio(
                audio_data=sample_audio_data,
                language_code="en-US",
                audio_format="xyz",
            )

        assert "Unsupported audio format" in str(exc_info.value)

    @patch("requests.get")
    @patch("src.services.voice_interface.speech_to_text_service.uuid.uuid4")
    def test_transcribe_audio_empty_result(
        self,
        mock_uuid,
        mock_requests_get,
        speech_service,
        mock_transcribe_client,
        mock_s3_client,
        sample_audio_data,
    ):
        """Test transcription with empty result."""
        mock_uuid.return_value = "test-uuid-123"
        mock_s3_client.upload_file_obj.return_value = "s3://test-bucket/audio.mp3"

        mock_transcribe_client.wait_for_completion.return_value = {
            "Transcript": {
                "TranscriptFileUri": "https://example.com/transcript.json"
            }
        }

        # Mock empty transcript
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": {
                "transcripts": [{"transcript": ""}],
                "items": [],
            }
        }
        mock_requests_get.return_value = mock_response

        with pytest.raises(VoiceProcessingError) as exc_info:
            speech_service.transcribe_audio(
                audio_data=sample_audio_data,
                language_code="en-US",
                audio_format="mp3",
            )

        assert "No transcription generated" in str(exc_info.value)

    def test_transcribe_audio_stream(
        self,
        speech_service,
        sample_audio_data,
    ):
        """Test transcribing audio from stream."""
        audio_stream = BytesIO(sample_audio_data)

        with patch.object(
            speech_service,
            "transcribe_audio",
            return_value=TranscriptionResult(
                text="Test transcription",
                confidence=0.95,
                language="en",
            ),
        ) as mock_transcribe:
            result = speech_service.transcribe_audio_stream(
                audio_stream=audio_stream,
                language_code="en-US",
                audio_format="mp3",
            )

            assert result.text == "Test transcription"
            mock_transcribe.assert_called_once()

    @patch("src.services.voice_interface.speech_to_text_service.uuid.uuid4")
    def test_detect_language(
        self,
        mock_uuid,
        speech_service,
        mock_s3_client,
        sample_audio_data,
    ):
        """Test language detection from audio."""
        mock_uuid.return_value = "test-uuid-123"
        mock_s3_client.upload_file_obj.return_value = "s3://test-bucket/audio.mp3"

        result = speech_service.detect_language(
            audio_data=sample_audio_data,
            audio_format="mp3",
        )

        # Currently returns default language
        assert result == "en-US"
        mock_s3_client.delete_file.assert_called_once()


class TestTranscriptionResult:
    """Test suite for TranscriptionResult."""

    def test_initialization(self):
        """Test TranscriptionResult initialization."""
        result = TranscriptionResult(
            text="Hello world",
            confidence=0.95,
            language="en",
            timestamps=[{"word": "Hello", "start_time": 0.0}],
            metadata={"duration": 1.5},
        )

        assert result.text == "Hello world"
        assert result.confidence == 0.95
        assert result.language == "en"
        assert len(result.timestamps) == 1
        assert result.metadata["duration"] == 1.5

    def test_to_dict(self):
        """Test converting TranscriptionResult to dictionary."""
        result = TranscriptionResult(
            text="Hello world",
            confidence=0.95,
            language="en",
        )

        result_dict = result.to_dict()

        assert result_dict["text"] == "Hello world"
        assert result_dict["confidence"] == 0.95
        assert result_dict["language"] == "en"
        assert "timestamps" in result_dict
        assert "metadata" in result_dict
