"""Unit tests for text-to-speech service."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from io import BytesIO

from src.services.voice_interface.text_to_speech_service import (
    TextToSpeechService,
    SynthesisResult,
)
from src.shared.utils.errors import VoiceProcessingError


class TestTextToSpeechService:
    """Test cases for TextToSpeechService."""

    @pytest.fixture
    def mock_polly_client(self):
        """Create mock Polly client."""
        client = Mock()
        client.synthesize_speech.return_value = b"mock_audio_data"
        client.get_available_voices.return_value = [
            {
                "Id": "Joanna",
                "LanguageCode": "en-US",
                "Gender": "Female",
            },
            {
                "Id": "Aditi",
                "LanguageCode": "hi-IN",
                "Gender": "Female",
            },
        ]
        return client

    @pytest.fixture
    def tts_service(self, mock_polly_client):
        """Create TextToSpeechService instance."""
        return TextToSpeechService(polly_client=mock_polly_client)

    def test_initialization(self, tts_service):
        """Test service initialization."""
        assert tts_service is not None
        assert tts_service.polly_client is not None

    def test_synthesize_speech_basic(self, tts_service, mock_polly_client):
        """Test basic speech synthesis."""
        text = "Hello, world!"
        result = tts_service.synthesize_speech(text=text)

        assert isinstance(result, SynthesisResult)
        assert result.audio_data == b"mock_audio_data"
        assert result.voice_id == "Joanna"
        assert result.language_code == "en-US"
        assert result.text_length == len(text)
        assert result.audio_format == "mp3"

        mock_polly_client.synthesize_speech.assert_called_once()

    def test_synthesize_speech_with_language(self, tts_service, mock_polly_client):
        """Test speech synthesis with specific language."""
        text = "नमस्ते"
        result = tts_service.synthesize_speech(
            text=text,
            language_code="hi-IN",
        )

        assert result.voice_id == "Aditi"
        assert result.language_code == "hi-IN"
        assert result.metadata["is_indian_language"] is True

    def test_synthesize_speech_with_custom_voice(self, tts_service, mock_polly_client):
        """Test speech synthesis with custom voice."""
        text = "Hello"
        result = tts_service.synthesize_speech(
            text=text,
            voice_id="Emma",
            language_code="en-GB",
        )

        assert result.voice_id == "Emma"
        assert result.language_code == "en-GB"

    def test_synthesize_speech_bilingual_voice(self, tts_service, mock_polly_client):
        """Test synthesis with bilingual voice."""
        text = "Hello from India"
        result = tts_service.synthesize_speech(
            text=text,
            language_code="hi-IN",
            voice_id="Aditi",
        )

        assert result.voice_id == "Aditi"
        assert result.metadata["is_bilingual"] is True

    def test_synthesize_speech_empty_text(self, tts_service):
        """Test synthesis with empty text."""
        with pytest.raises(VoiceProcessingError) as exc_info:
            tts_service.synthesize_speech(text="")

        assert "Text cannot be empty" in str(exc_info.value)

    def test_synthesize_speech_error_handling(self, tts_service, mock_polly_client):
        """Test error handling during synthesis."""
        mock_polly_client.synthesize_speech.side_effect = Exception("Polly error")

        with pytest.raises(VoiceProcessingError) as exc_info:
            tts_service.synthesize_speech(text="Hello")

        assert "Failed to synthesize speech" in str(exc_info.value)

    def test_synthesize_with_preferences(self, tts_service, mock_polly_client):
        """Test synthesis with user preferences."""
        preferences = {
            "language": "hi",
            "voice_id": "Aditi",
        }

        result = tts_service.synthesize_with_preferences(
            text="Hello",
            user_preferences=preferences,
        )

        assert result.voice_id == "Aditi"
        assert result.language_code == "hi-IN"

    def test_synthesize_with_preferences_default(self, tts_service, mock_polly_client):
        """Test synthesis with default preferences."""
        preferences = {}

        result = tts_service.synthesize_with_preferences(
            text="Hello",
            user_preferences=preferences,
        )

        assert result.language_code == "en-US"

    def test_synthesize_to_stream(self, tts_service, mock_polly_client):
        """Test synthesis to stream."""
        stream = tts_service.synthesize_to_stream(text="Hello")

        assert isinstance(stream, BytesIO)
        assert stream.read() == b"mock_audio_data"

    def test_get_available_voices(self, tts_service, mock_polly_client):
        """Test getting available voices."""
        voices = tts_service.get_available_voices()

        assert len(voices) == 2
        assert voices[0]["Id"] == "Joanna"
        assert voices[1]["Id"] == "Aditi"
        assert voices[1]["IsBilingual"] is True

    def test_get_available_voices_filtered(self, tts_service, mock_polly_client):
        """Test getting available voices with language filter."""
        voices = tts_service.get_available_voices(language_code="hi-IN")

        mock_polly_client.get_available_voices.assert_called_with(
            language_code="hi-IN"
        )

    def test_get_indian_language_voices(self, tts_service, mock_polly_client):
        """Test getting Indian language voices."""
        mock_polly_client.get_available_voices.return_value = [
            {"Id": "Aditi", "LanguageCode": "hi-IN"}
        ]

        voices = tts_service.get_indian_language_voices()

        assert isinstance(voices, dict)
        # Should have attempted to get voices for multiple Indian languages
        assert mock_polly_client.get_available_voices.call_count > 0

    def test_get_bilingual_voices(self, tts_service):
        """Test getting bilingual voices."""
        bilingual = tts_service.get_bilingual_voices()

        assert "Aditi" in bilingual
        assert "Kajal" in bilingual
        assert "en-IN" in bilingual["Aditi"]
        assert "hi-IN" in bilingual["Aditi"]

    def test_select_voice_direct_mapping(self, tts_service):
        """Test voice selection with direct mapping."""
        voice = tts_service._select_voice("en-US")
        assert voice == "Joanna"

        voice = tts_service._select_voice("hi-IN")
        assert voice == "Aditi"

    def test_select_voice_prefix_matching(self, tts_service):
        """Test voice selection with prefix matching."""
        voice = tts_service._select_voice("en-CA")
        assert voice in ["Joanna", "Emma"]  # Should match 'en' prefix

    def test_select_voice_default(self, tts_service):
        """Test voice selection with unknown language."""
        voice = tts_service._select_voice("xx-XX")
        assert voice == "Joanna"  # Default voice

    def test_is_indian_language(self, tts_service):
        """Test Indian language detection."""
        assert tts_service._is_indian_language("hi-IN") is True
        assert tts_service._is_indian_language("ta-IN") is True
        assert tts_service._is_indian_language("en-US") is False

    def test_expand_language_code(self, tts_service):
        """Test language code expansion."""
        assert tts_service._expand_language_code("en") == "en-US"
        assert tts_service._expand_language_code("hi") == "hi-IN"
        assert tts_service._expand_language_code("ta") == "ta-IN"
        assert tts_service._expand_language_code("es") == "es-ES"

    def test_validate_voice_for_language_bilingual(self, tts_service):
        """Test voice validation for bilingual voices."""
        # Aditi supports both en-IN and hi-IN
        assert tts_service.validate_voice_for_language("Aditi", "en-IN") is True
        assert tts_service.validate_voice_for_language("Aditi", "hi-IN") is True
        assert tts_service.validate_voice_for_language("Aditi", "ta-IN") is False

    def test_validate_voice_for_language_standard(self, tts_service):
        """Test voice validation for standard voices."""
        assert tts_service.validate_voice_for_language("Joanna", "en-US") is True
        assert tts_service.validate_voice_for_language("Joanna", "hi-IN") is False

    def test_synthesis_result_metadata(self, tts_service, mock_polly_client):
        """Test synthesis result contains proper metadata."""
        result = tts_service.synthesize_speech(
            text="Test",
            language_code="hi-IN",
        )

        assert "is_bilingual" in result.metadata
        assert "is_indian_language" in result.metadata
        assert "audio_size_bytes" in result.metadata
        assert result.metadata["is_indian_language"] is True

    def test_different_audio_formats(self, tts_service, mock_polly_client):
        """Test synthesis with different audio formats."""
        formats = ["mp3", "ogg_vorbis", "pcm"]

        for fmt in formats:
            result = tts_service.synthesize_speech(
                text="Hello",
                audio_format=fmt,
            )
            assert result.audio_format == fmt

    def test_different_engines(self, tts_service, mock_polly_client):
        """Test synthesis with different engines."""
        result = tts_service.synthesize_speech(
            text="Hello",
            engine="neural",
        )
        assert result.engine == "neural"

        result = tts_service.synthesize_speech(
            text="Hello",
            engine="standard",
        )
        assert result.engine == "standard"

    def test_tamil_bilingual_voice(self, tts_service, mock_polly_client):
        """Test Tamil bilingual voice (Kajal)."""
        result = tts_service.synthesize_speech(
            text="வணக்கம்",
            language_code="ta-IN",
        )

        assert result.voice_id == "Kajal"
        assert result.metadata["is_bilingual"] is True

    def test_long_text_synthesis(self, tts_service, mock_polly_client):
        """Test synthesis with long text."""
        long_text = "Hello " * 1000
        result = tts_service.synthesize_speech(text=long_text)

        assert result.text_length == len(long_text)
        assert result.audio_data == b"mock_audio_data"


class TestSynthesisResult:
    """Test cases for SynthesisResult dataclass."""

    def test_synthesis_result_creation(self):
        """Test creating SynthesisResult."""
        result = SynthesisResult(
            audio_data=b"test_audio",
            voice_id="Joanna",
            language_code="en-US",
            text_length=100,
            audio_format="mp3",
            engine="neural",
            metadata={"test": "value"},
        )

        assert result.audio_data == b"test_audio"
        assert result.voice_id == "Joanna"
        assert result.language_code == "en-US"
        assert result.text_length == 100
        assert result.audio_format == "mp3"
        assert result.engine == "neural"
        assert result.metadata["test"] == "value"
