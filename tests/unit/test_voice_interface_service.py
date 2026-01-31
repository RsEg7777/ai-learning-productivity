"""Unit tests for voice interface service."""

import pytest
from unittest.mock import Mock, patch
from io import BytesIO

from src.services.voice_interface import (
    VoiceInterfaceService,
    SpeechToTextService,
    TextToSpeechService,
    AudioProcessor,
    TranscriptionResult,
    SynthesisResult,
)
from src.shared.utils.errors import VoiceProcessingError


class TestVoiceInterfaceService:
    """Test suite for VoiceInterfaceService."""

    @pytest.fixture
    def mock_speech_to_text(self):
        """Create mock SpeechToTextService."""
        mock_service = Mock(spec=SpeechToTextService)
        return mock_service

    @pytest.fixture
    def mock_text_to_speech(self):
        """Create mock TextToSpeechService."""
        mock_service = Mock(spec=TextToSpeechService)
        return mock_service

    @pytest.fixture
    def mock_audio_processor(self):
        """Create mock AudioProcessor."""
        mock_processor = Mock(spec=AudioProcessor)
        return mock_processor

    @pytest.fixture
    def voice_service(self, mock_speech_to_text, mock_text_to_speech, mock_audio_processor):
        """Create VoiceInterfaceService instance."""
        return VoiceInterfaceService(
            speech_to_text_service=mock_speech_to_text,
            text_to_speech_service=mock_text_to_speech,
            audio_processor=mock_audio_processor,
        )

    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data."""
        return b"fake audio data for testing"

    def test_initialization(self, mock_speech_to_text, mock_text_to_speech, mock_audio_processor):
        """Test VoiceInterfaceService initialization."""
        service = VoiceInterfaceService(
            speech_to_text_service=mock_speech_to_text,
            text_to_speech_service=mock_text_to_speech,
            audio_processor=mock_audio_processor,
        )

        assert service.speech_to_text == mock_speech_to_text
        assert service.text_to_speech == mock_text_to_speech
        assert service.audio_processor == mock_audio_processor

    def test_process_voice_input_with_enhancements(
        self,
        voice_service,
        mock_speech_to_text,
        mock_audio_processor,
        sample_audio_data,
    ):
        """Test processing voice input with audio enhancements."""
        # Mock audio enhancement
        enhanced_audio = b"enhanced audio data"
        enhancement_metadata = {
            "noise_reduction_applied": True,
            "quality_enhancement_applied": True,
        }
        mock_audio_processor.enhance_audio.return_value = (
            enhanced_audio,
            enhancement_metadata,
        )

        # Mock transcription
        mock_result = TranscriptionResult(
            text="Hello world",
            confidence=0.95,
            language="en",
            metadata={},
        )
        mock_speech_to_text.transcribe_audio.return_value = mock_result

        result = voice_service.process_voice_input(
            audio_data=sample_audio_data,
            language_code="en-US",
            audio_format="mp3",
            enable_noise_reduction=True,
            enable_quality_enhancement=True,
        )

        assert result.text == "Hello world"
        assert result.confidence == 0.95
        assert result.metadata["noise_reduction_applied"] is True
        assert result.metadata["quality_enhancement_applied"] is True

        mock_audio_processor.enhance_audio.assert_called_once()
        mock_speech_to_text.transcribe_audio.assert_called_once_with(
            audio_data=enhanced_audio,
            language_code="en-US",
            audio_format="mp3",
            enable_noise_reduction=True,
            enable_quality_enhancement=True,
        )

    def test_process_voice_input_without_enhancements(
        self,
        voice_service,
        mock_speech_to_text,
        mock_audio_processor,
        sample_audio_data,
    ):
        """Test processing voice input without audio enhancements."""
        # Mock transcription
        mock_result = TranscriptionResult(
            text="Hello world",
            confidence=0.95,
            language="en",
            metadata={},
        )
        mock_speech_to_text.transcribe_audio.return_value = mock_result

        result = voice_service.process_voice_input(
            audio_data=sample_audio_data,
            language_code="en-US",
            audio_format="mp3",
            enable_noise_reduction=False,
            enable_quality_enhancement=False,
        )

        assert result.text == "Hello world"
        # Audio processor should not be called when both enhancements are disabled
        mock_audio_processor.enhance_audio.assert_not_called()

    def test_process_voice_input_indian_language(
        self,
        voice_service,
        mock_speech_to_text,
        mock_audio_processor,
        sample_audio_data,
    ):
        """Test processing voice input in Indian language."""
        enhanced_audio = b"enhanced audio data"
        enhancement_metadata = {"noise_reduction_applied": True}
        mock_audio_processor.enhance_audio.return_value = (
            enhanced_audio,
            enhancement_metadata,
        )

        mock_result = TranscriptionResult(
            text="नमस्ते दुनिया",  # Hindi: Hello world
            confidence=0.92,
            language="hi",
            metadata={},
        )
        mock_speech_to_text.transcribe_audio.return_value = mock_result

        result = voice_service.process_voice_input(
            audio_data=sample_audio_data,
            language_code="hi-IN",
            audio_format="mp3",
        )

        assert result.text == "नमस्ते दुनिया"
        assert result.confidence >= 0.90  # Meets 90%+ accuracy requirement
        assert result.language == "hi"

    def test_process_voice_input_error(
        self,
        voice_service,
        mock_speech_to_text,
        mock_audio_processor,
        sample_audio_data,
    ):
        """Test processing voice input with error."""
        mock_audio_processor.enhance_audio.return_value = (
            sample_audio_data,
            {},
        )
        mock_speech_to_text.transcribe_audio.side_effect = Exception(
            "Transcription failed"
        )

        with pytest.raises(VoiceProcessingError) as exc_info:
            voice_service.process_voice_input(
                audio_data=sample_audio_data,
                language_code="en-US",
                audio_format="mp3",
            )

        assert "Failed to process voice input" in str(exc_info.value)

    def test_transcribe_audio_stream(
        self,
        voice_service,
        sample_audio_data,
    ):
        """Test transcribing audio from stream."""
        audio_stream = BytesIO(sample_audio_data)

        with patch.object(
            voice_service,
            "process_voice_input",
            return_value=TranscriptionResult(
                text="Test transcription",
                confidence=0.95,
                language="en",
            ),
        ) as mock_process:
            result = voice_service.transcribe_audio_stream(
                audio_stream=audio_stream,
                language_code="en-US",
                audio_format="mp3",
                enable_enhancements=True,
            )

            assert result.text == "Test transcription"
            mock_process.assert_called_once()

    def test_detect_language(
        self,
        voice_service,
        mock_speech_to_text,
        sample_audio_data,
    ):
        """Test language detection."""
        mock_speech_to_text.detect_language.return_value = "hi-IN"

        result = voice_service.detect_language(
            audio_data=sample_audio_data,
            audio_format="mp3",
        )

        assert result == "hi-IN"
        mock_speech_to_text.detect_language.assert_called_once()

    def test_get_supported_languages(
        self,
        voice_service,
        mock_speech_to_text,
    ):
        """Test getting supported languages."""
        mock_speech_to_text.get_supported_languages.return_value = {
            "en": "en-US",
            "hi": "hi-IN",
        }

        languages = voice_service.get_supported_languages()

        assert "en" in languages
        assert "hi" in languages

    def test_is_indian_language(
        self,
        voice_service,
        mock_speech_to_text,
    ):
        """Test checking if language is Indian."""
        mock_speech_to_text.is_indian_language.return_value = True

        result = voice_service.is_indian_language("hi-IN")

        assert result is True
        mock_speech_to_text.is_indian_language.assert_called_once_with("hi-IN")

    def test_validate_audio_quality(
        self,
        voice_service,
        mock_audio_processor,
        sample_audio_data,
    ):
        """Test audio quality validation."""
        mock_audio_processor.assess_audio_quality.return_value = {
            "quality": "good",
            "recommendations": [],
        }

        result = voice_service.validate_audio_quality(
            audio_data=sample_audio_data,
            audio_format="mp3",
        )

        assert result["quality"] == "good"
        mock_audio_processor.assess_audio_quality.assert_called_once()

    def test_validate_audio_quality_error(
        self,
        voice_service,
        mock_audio_processor,
        sample_audio_data,
    ):
        """Test audio quality validation with error."""
        mock_audio_processor.assess_audio_quality.side_effect = Exception(
            "Assessment failed"
        )

        result = voice_service.validate_audio_quality(
            audio_data=sample_audio_data,
            audio_format="mp3",
        )

        assert result["quality"] == "unknown"
        assert "error" in result


    # Text-to-Speech Tests

    def test_generate_audio_response(
        self,
        voice_service,
        mock_text_to_speech,
    ):
        """Test generating audio response."""
        mock_result = SynthesisResult(
            audio_data=b"audio_data",
            voice_id="Joanna",
            language_code="en-US",
            text_length=10,
            audio_format="mp3",
            engine="neural",
            metadata={},
        )
        mock_text_to_speech.synthesize_speech.return_value = mock_result

        result = voice_service.generate_audio_response(
            text="Hello world",
            language_code="en-US",
        )

        assert result.audio_data == b"audio_data"
        assert result.voice_id == "Joanna"
        assert result.language_code == "en-US"
        mock_text_to_speech.synthesize_speech.assert_called_once()

    def test_generate_audio_response_indian_language(
        self,
        voice_service,
        mock_text_to_speech,
    ):
        """Test generating audio response in Indian language."""
        mock_result = SynthesisResult(
            audio_data=b"hindi_audio",
            voice_id="Aditi",
            language_code="hi-IN",
            text_length=15,
            audio_format="mp3",
            engine="neural",
            metadata={"is_bilingual": True},
        )
        mock_text_to_speech.synthesize_speech.return_value = mock_result

        result = voice_service.generate_audio_response(
            text="नमस्ते",
            language_code="hi-IN",
        )

        assert result.voice_id == "Aditi"
        assert result.language_code == "hi-IN"
        assert result.metadata["is_bilingual"] is True

    def test_generate_audio_with_preferences(
        self,
        voice_service,
        mock_text_to_speech,
    ):
        """Test generating audio with user preferences."""
        preferences = {
            "language": "hi",
            "voice_id": "Aditi",
        }

        mock_result = SynthesisResult(
            audio_data=b"audio_data",
            voice_id="Aditi",
            language_code="hi-IN",
            text_length=10,
            audio_format="mp3",
            engine="neural",
            metadata={},
        )
        mock_text_to_speech.synthesize_with_preferences.return_value = mock_result

        result = voice_service.generate_audio_with_preferences(
            text="Hello",
            user_preferences=preferences,
        )

        assert result.voice_id == "Aditi"
        assert result.language_code == "hi-IN"
        mock_text_to_speech.synthesize_with_preferences.assert_called_once()

    def test_process_voice_round_trip(
        self,
        voice_service,
        mock_speech_to_text,
        mock_text_to_speech,
        mock_audio_processor,
        sample_audio_data,
    ):
        """Test complete voice round-trip processing."""
        # Mock audio enhancement
        mock_audio_processor.enhance_audio.return_value = (
            sample_audio_data,
            {},
        )

        # Mock transcription
        mock_transcription = TranscriptionResult(
            text="Hello world",
            confidence=0.95,
            language="en",
            metadata={},
        )
        mock_speech_to_text.transcribe_audio.return_value = mock_transcription

        # Mock synthesis
        mock_synthesis = SynthesisResult(
            audio_data=b"response_audio",
            voice_id="Joanna",
            language_code="en-US",
            text_length=11,
            audio_format="mp3",
            engine="neural",
            metadata={"is_bilingual": False},
        )
        mock_text_to_speech.synthesize_speech.return_value = mock_synthesis

        with patch.object(
            voice_service,
            "process_voice_input",
            return_value=mock_transcription,
        ):
            with patch.object(
                voice_service,
                "generate_audio_response",
                return_value=mock_synthesis,
            ):
                result = voice_service.process_voice_round_trip(
                    audio_input=sample_audio_data,
                    input_language="en-US",
                )

                assert result["transcription"]["text"] == "Hello world"
                assert result["transcription"]["confidence"] == 0.95
                assert result["synthesis"]["voice_id"] == "Joanna"
                assert result["synthesis"]["audio_data"] == b"response_audio"
                assert result["metadata"]["input_language"] == "en-US"
                assert result["metadata"]["output_language"] == "en-US"

    def test_process_voice_round_trip_different_languages(
        self,
        voice_service,
        sample_audio_data,
    ):
        """Test voice round-trip with different input/output languages."""
        mock_transcription = TranscriptionResult(
            text="Hello",
            confidence=0.95,
            language="en",
            metadata={},
        )

        mock_synthesis = SynthesisResult(
            audio_data=b"hindi_audio",
            voice_id="Aditi",
            language_code="hi-IN",
            text_length=5,
            audio_format="mp3",
            engine="neural",
            metadata={"is_bilingual": True},
        )

        with patch.object(
            voice_service,
            "process_voice_input",
            return_value=mock_transcription,
        ):
            with patch.object(
                voice_service,
                "generate_audio_response",
                return_value=mock_synthesis,
            ):
                result = voice_service.process_voice_round_trip(
                    audio_input=sample_audio_data,
                    input_language="en-US",
                    output_language="hi-IN",
                )

                assert result["metadata"]["input_language"] == "en-US"
                assert result["metadata"]["output_language"] == "hi-IN"
                assert result["synthesis"]["voice_id"] == "Aditi"

    def test_get_available_voices(
        self,
        voice_service,
        mock_text_to_speech,
    ):
        """Test getting available voices."""
        mock_voices = [
            {"Id": "Joanna", "LanguageCode": "en-US"},
            {"Id": "Aditi", "LanguageCode": "hi-IN", "IsBilingual": True},
        ]
        mock_text_to_speech.get_available_voices.return_value = mock_voices

        voices = voice_service.get_available_voices()

        assert len(voices) == 2
        assert voices[1]["IsBilingual"] is True
        mock_text_to_speech.get_available_voices.assert_called_once()

    def test_get_indian_language_voices(
        self,
        voice_service,
        mock_text_to_speech,
    ):
        """Test getting Indian language voices."""
        mock_voices = {
            "hi-IN": [{"Id": "Aditi"}],
            "ta-IN": [{"Id": "Kajal"}],
        }
        mock_text_to_speech.get_indian_language_voices.return_value = mock_voices

        voices = voice_service.get_indian_language_voices()

        assert "hi-IN" in voices
        assert "ta-IN" in voices
        mock_text_to_speech.get_indian_language_voices.assert_called_once()

    def test_get_bilingual_voices(
        self,
        voice_service,
        mock_text_to_speech,
    ):
        """Test getting bilingual voices."""
        mock_bilingual = {
            "Aditi": ["en-IN", "hi-IN"],
            "Kajal": ["en-IN", "ta-IN"],
        }
        mock_text_to_speech.get_bilingual_voices.return_value = mock_bilingual

        bilingual = voice_service.get_bilingual_voices()

        assert "Aditi" in bilingual
        assert "Kajal" in bilingual
        mock_text_to_speech.get_bilingual_voices.assert_called_once()

    def test_validate_voice_preference(
        self,
        voice_service,
        mock_text_to_speech,
    ):
        """Test validating voice preference."""
        mock_text_to_speech.validate_voice_for_language.return_value = True

        result = voice_service.validate_voice_preference(
            voice_id="Aditi",
            language_code="hi-IN",
        )

        assert result is True
        mock_text_to_speech.validate_voice_for_language.assert_called_once_with(
            voice_id="Aditi",
            language_code="hi-IN",
        )

    def test_generate_audio_response_error(
        self,
        voice_service,
        mock_text_to_speech,
    ):
        """Test error handling in audio generation."""
        mock_text_to_speech.synthesize_speech.side_effect = Exception(
            "Synthesis failed"
        )

        with pytest.raises(VoiceProcessingError) as exc_info:
            voice_service.generate_audio_response(text="Hello")

        assert "Failed to generate audio response" in str(exc_info.value)
