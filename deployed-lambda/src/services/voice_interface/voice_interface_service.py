"""Voice interface service for speech-to-text and text-to-speech."""

import logging
from typing import Optional, Dict, Any
from io import BytesIO

from src.services.voice_interface.speech_to_text_service import (
    SpeechToTextService,
    TranscriptionResult,
)
from src.services.voice_interface.text_to_speech_service import (
    TextToSpeechService,
    SynthesisResult,
)
from src.services.voice_interface.audio_processor import AudioProcessor
from src.shared.aws_clients.transcribe_client import TranscribeClient
from src.shared.aws_clients.polly_client import PollyClient
from src.shared.aws_clients.s3_client import S3Client
from src.shared.utils.errors import VoiceProcessingError
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)


class VoiceInterfaceService:
    """
    Voice interface service for handling speech-to-text and text-to-speech.

    This service provides:
    - Real-time speech transcription
    - Support for Indian languages with 90%+ accuracy
    - Audio quality enhancement and noise reduction
    - Audio response generation in multiple languages
    - Support for bilingual voices (Aditi, Kajal)
    - Voice preference management
    """

    def __init__(
        self,
        speech_to_text_service: Optional[SpeechToTextService] = None,
        text_to_speech_service: Optional[TextToSpeechService] = None,
        audio_processor: Optional[AudioProcessor] = None,
        transcribe_client: Optional[TranscribeClient] = None,
        polly_client: Optional[PollyClient] = None,
        s3_client: Optional[S3Client] = None,
    ):
        """
        Initialize voice interface service.

        Args:
            speech_to_text_service: Speech-to-text service
            text_to_speech_service: Text-to-speech service
            audio_processor: Audio processor for quality enhancement
            transcribe_client: Amazon Transcribe client
            polly_client: Amazon Polly client
            s3_client: S3 client
        """
        self.speech_to_text = speech_to_text_service or SpeechToTextService(
            transcribe_client=transcribe_client,
            s3_client=s3_client,
        )
        self.text_to_speech = text_to_speech_service or TextToSpeechService(
            polly_client=polly_client,
            s3_client=s3_client,
        )
        self.audio_processor = audio_processor or AudioProcessor()
        logger.info("Initialized VoiceInterfaceService with TTS support")

    def process_voice_input(
        self,
        audio_data: bytes,
        language_code: str = "en-US",
        audio_format: str = "mp3",
        enable_noise_reduction: bool = True,
        enable_quality_enhancement: bool = True,
    ) -> TranscriptionResult:
        """
        Process voice input with audio enhancement and transcription.

        This method:
        1. Enhances audio quality if enabled
        2. Reduces noise if enabled
        3. Transcribes speech to text
        4. Returns transcription with confidence scores

        Args:
            audio_data: Raw audio data
            language_code: Language code (e.g., 'en-US', 'hi-IN')
            audio_format: Audio format (mp3, wav, etc.)
            enable_noise_reduction: Enable noise reduction
            enable_quality_enhancement: Enable audio quality enhancement

        Returns:
            TranscriptionResult with transcribed text and metadata

        Raises:
            VoiceProcessingError: If processing fails
        """
        try:
            logger.info(
                f"Processing voice input in {language_code} "
                f"(noise_reduction={enable_noise_reduction}, "
                f"quality_enhancement={enable_quality_enhancement})"
            )

            # Step 1: Enhance audio quality if enabled
            processed_audio = audio_data
            enhancement_metadata = {}

            if enable_quality_enhancement or enable_noise_reduction:
                processed_audio, enhancement_metadata = self.audio_processor.enhance_audio(
                    audio_data=audio_data,
                    audio_format=audio_format,
                    enable_noise_reduction=enable_noise_reduction,
                    enable_quality_enhancement=enable_quality_enhancement,
                )

            # Step 2: Transcribe audio
            result = self.speech_to_text.transcribe_audio(
                audio_data=processed_audio,
                language_code=language_code,
                audio_format=audio_format,
                enable_noise_reduction=enable_noise_reduction,
                enable_quality_enhancement=enable_quality_enhancement,
            )

            # Add enhancement metadata to result
            result.metadata.update(enhancement_metadata)

            logger.info(
                f"Successfully processed voice input: {len(result.text)} chars, "
                f"confidence: {result.confidence:.2f}"
            )

            return result

        except VoiceProcessingError:
            raise
        except Exception as e:
            logger.error(f"Failed to process voice input: {e}")
            raise VoiceProcessingError(
                f"Failed to process voice input: {str(e)}",
                operation="process_voice_input",
                details={"language": language_code, "format": audio_format},
            )

    def transcribe_audio_stream(
        self,
        audio_stream: BytesIO,
        language_code: str = "en-US",
        audio_format: str = "mp3",
        enable_enhancements: bool = True,
    ) -> TranscriptionResult:
        """
        Transcribe audio from a stream with enhancements.

        Args:
            audio_stream: Audio stream
            language_code: Language code
            audio_format: Audio format
            enable_enhancements: Enable audio enhancements

        Returns:
            TranscriptionResult

        Raises:
            VoiceProcessingError: If transcription fails
        """
        try:
            audio_data = audio_stream.read()
            return self.process_voice_input(
                audio_data=audio_data,
                language_code=language_code,
                audio_format=audio_format,
                enable_noise_reduction=enable_enhancements,
                enable_quality_enhancement=enable_enhancements,
            )
        except Exception as e:
            logger.error(f"Failed to transcribe audio stream: {e}")
            raise VoiceProcessingError(
                f"Failed to transcribe audio stream: {str(e)}",
                operation="transcribe_stream",
            )

    def detect_language(
        self,
        audio_data: bytes,
        audio_format: str = "mp3",
    ) -> str:
        """
        Detect language from audio.

        Args:
            audio_data: Audio data
            audio_format: Audio format

        Returns:
            Detected language code

        Raises:
            VoiceProcessingError: If detection fails
        """
        try:
            return self.speech_to_text.detect_language(
                audio_data=audio_data,
                audio_format=audio_format,
            )
        except Exception as e:
            logger.error(f"Failed to detect language: {e}")
            raise VoiceProcessingError(
                f"Failed to detect language: {str(e)}",
                operation="detect_language",
            )

    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get supported languages for voice processing.

        Returns:
            Dictionary mapping language codes to full language codes
        """
        return self.speech_to_text.get_supported_languages()

    def is_indian_language(self, language_code: str) -> bool:
        """
        Check if language is an Indian language.

        Args:
            language_code: Language code

        Returns:
            True if Indian language
        """
        return self.speech_to_text.is_indian_language(language_code)

    def validate_audio_quality(
        self,
        audio_data: bytes,
        audio_format: str = "mp3",
    ) -> Dict[str, Any]:
        """
        Validate audio quality and provide recommendations.

        Args:
            audio_data: Audio data
            audio_format: Audio format

        Returns:
            Quality assessment with recommendations
        """
        try:
            return self.audio_processor.assess_audio_quality(
                audio_data=audio_data,
                audio_format=audio_format,
            )
        except Exception as e:
            logger.error(f"Failed to validate audio quality: {e}")
            return {
                "quality": "unknown",
                "recommendations": ["Unable to assess audio quality"],
                "error": str(e),
            }

    # Text-to-Speech Methods

    def generate_audio_response(
        self,
        text: str,
        language_code: str = "en-US",
        voice_id: Optional[str] = None,
        audio_format: str = "mp3",
    ) -> SynthesisResult:
        """
        Generate audio response from text.

        This method converts text to speech using Amazon Polly with support
        for multiple languages and bilingual voices.

        Args:
            text: Text to convert to speech
            language_code: Language code (e.g., 'en-US', 'hi-IN')
            voice_id: Specific voice ID (optional, auto-selected if not provided)
            audio_format: Output audio format (mp3, ogg_vorbis, pcm)

        Returns:
            SynthesisResult with audio data and metadata

        Raises:
            VoiceProcessingError: If synthesis fails
        """
        try:
            logger.info(
                f"Generating audio response: language={language_code}, "
                f"voice={voice_id}, text_length={len(text)}"
            )

            result = self.text_to_speech.synthesize_speech(
                text=text,
                language_code=language_code,
                voice_id=voice_id,
                audio_format=audio_format,
            )

            logger.info(
                f"Successfully generated audio response: "
                f"{len(result.audio_data)} bytes"
            )

            return result

        except VoiceProcessingError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate audio response: {e}")
            raise VoiceProcessingError(
                f"Failed to generate audio response: {str(e)}",
                operation="generate_audio_response",
                details={"language": language_code, "voice": voice_id},
            )

    def generate_audio_with_preferences(
        self,
        text: str,
        user_preferences: Dict[str, Any],
        audio_format: str = "mp3",
    ) -> SynthesisResult:
        """
        Generate audio response using user preferences.

        This method respects user's language and voice preferences for
        personalized audio responses.

        Args:
            text: Text to convert to speech
            user_preferences: User preferences including language and voice_id
            audio_format: Output audio format

        Returns:
            SynthesisResult with audio data and metadata

        Raises:
            VoiceProcessingError: If synthesis fails
        """
        try:
            logger.info("Generating audio with user preferences")

            result = self.text_to_speech.synthesize_with_preferences(
                text=text,
                user_preferences=user_preferences,
                audio_format=audio_format,
            )

            logger.info(
                f"Successfully generated audio with preferences: "
                f"voice={result.voice_id}, language={result.language_code}"
            )

            return result

        except VoiceProcessingError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate audio with preferences: {e}")
            raise VoiceProcessingError(
                f"Failed to generate audio with preferences: {str(e)}",
                operation="generate_audio_with_preferences",
            )

    def process_voice_round_trip(
        self,
        audio_input: bytes,
        input_language: str = "en-US",
        output_language: Optional[str] = None,
        voice_id: Optional[str] = None,
        audio_format: str = "mp3",
    ) -> Dict[str, Any]:
        """
        Process complete voice round-trip: speech-to-text and text-to-speech.

        This method:
        1. Transcribes input audio to text
        2. Processes the text (can be extended for translation, etc.)
        3. Generates audio response in the desired language

        Args:
            audio_input: Input audio data
            input_language: Input audio language code
            output_language: Output audio language code (defaults to input language)
            voice_id: Specific voice ID for output (optional)
            audio_format: Audio format

        Returns:
            Dictionary with transcription and synthesis results

        Raises:
            VoiceProcessingError: If processing fails
        """
        try:
            logger.info(
                f"Processing voice round-trip: "
                f"input_lang={input_language}, output_lang={output_language}"
            )

            # Step 1: Transcribe input audio
            transcription = self.process_voice_input(
                audio_data=audio_input,
                language_code=input_language,
                audio_format=audio_format,
            )

            # Step 2: Determine output language
            if output_language is None:
                output_language = input_language

            # Step 3: Generate audio response
            synthesis = self.generate_audio_response(
                text=transcription.text,
                language_code=output_language,
                voice_id=voice_id,
                audio_format=audio_format,
            )

            result = {
                "transcription": {
                    "text": transcription.text,
                    "confidence": transcription.confidence,
                    "language": transcription.language,
                },
                "synthesis": {
                    "audio_data": synthesis.audio_data,
                    "voice_id": synthesis.voice_id,
                    "language_code": synthesis.language_code,
                    "audio_size": len(synthesis.audio_data),
                },
                "metadata": {
                    "input_language": input_language,
                    "output_language": output_language,
                    "is_bilingual": synthesis.metadata.get("is_bilingual", False),
                },
            }

            logger.info(
                f"Successfully completed voice round-trip: "
                f"transcribed {len(transcription.text)} chars, "
                f"generated {len(synthesis.audio_data)} bytes audio"
            )

            return result

        except VoiceProcessingError:
            raise
        except Exception as e:
            logger.error(f"Failed to process voice round-trip: {e}")
            raise VoiceProcessingError(
                f"Failed to process voice round-trip: {str(e)}",
                operation="process_voice_round_trip",
            )

    def get_available_voices(
        self,
        language_code: Optional[str] = None,
        include_bilingual: bool = True,
    ) -> list:
        """
        Get available voices for text-to-speech.

        Args:
            language_code: Language code to filter by (optional)
            include_bilingual: Include bilingual voices

        Returns:
            List of voice information dictionaries

        Raises:
            VoiceProcessingError: If retrieval fails
        """
        try:
            return self.text_to_speech.get_available_voices(
                language_code=language_code,
                include_bilingual=include_bilingual,
            )
        except Exception as e:
            logger.error(f"Failed to get available voices: {e}")
            raise VoiceProcessingError(
                f"Failed to get available voices: {str(e)}",
                operation="get_available_voices",
            )

    def get_indian_language_voices(self) -> Dict[str, list]:
        """
        Get voices for Indian languages.

        Returns:
            Dictionary mapping language codes to voice information

        Raises:
            VoiceProcessingError: If retrieval fails
        """
        try:
            return self.text_to_speech.get_indian_language_voices()
        except Exception as e:
            logger.error(f"Failed to get Indian language voices: {e}")
            raise VoiceProcessingError(
                f"Failed to get Indian language voices: {str(e)}",
                operation="get_indian_language_voices",
            )

    def get_bilingual_voices(self) -> Dict[str, list]:
        """
        Get bilingual voices and their supported languages.

        Returns:
            Dictionary mapping voice IDs to supported language codes
        """
        return self.text_to_speech.get_bilingual_voices()

    def validate_voice_preference(
        self,
        voice_id: str,
        language_code: str,
    ) -> bool:
        """
        Validate if a voice supports a language.

        Args:
            voice_id: Voice ID
            language_code: Language code

        Returns:
            True if voice supports the language
        """
        return self.text_to_speech.validate_voice_for_language(
            voice_id=voice_id,
            language_code=language_code,
        )
