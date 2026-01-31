"""Text-to-speech service using Amazon Polly."""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from io import BytesIO

from src.shared.aws_clients.polly_client import PollyClient
from src.shared.aws_clients.s3_client import S3Client
from src.shared.utils.errors import VoiceProcessingError
from src.shared.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SynthesisResult:
    """Result of text-to-speech synthesis."""
    audio_data: bytes
    voice_id: str
    language_code: str
    text_length: int
    audio_format: str
    engine: str
    metadata: Dict[str, Any]


class TextToSpeechService:
    """
    Text-to-speech service using Amazon Polly.
    
    This service provides:
    - Audio response generation in multiple languages
    - Support for bilingual voices (Aditi, Kajal) for Indian languages
    - Voice preference management
    - Automatic voice selection based on language
    """
    
    # Voice mappings for different languages
    VOICE_MAP = {
        # English voices
        "en-US": "Joanna",
        "en-GB": "Emma",
        "en-IN": "Aditi",  # Indian English (bilingual: English + Hindi)
        "en-AU": "Nicole",
        
        # Indian language voices
        "hi-IN": "Aditi",  # Hindi (bilingual: Hindi + English)
        "ta-IN": "Kajal",  # Tamil (bilingual: Tamil + English)
        
        # Other languages (can be extended)
        "es-ES": "Lucia",
        "fr-FR": "Celine",
        "de-DE": "Vicki",
        "it-IT": "Carla",
        "pt-BR": "Camila",
        "ja-JP": "Mizuki",
        "ko-KR": "Seoyeon",
        "zh-CN": "Zhiyu",
    }
    
    # Bilingual voices that support multiple languages
    BILINGUAL_VOICES = {
        "Aditi": ["en-IN", "hi-IN"],  # English (Indian) and Hindi
        "Kajal": ["en-IN", "ta-IN"],  # English (Indian) and Tamil
    }
    
    # Indian language codes
    INDIAN_LANGUAGES = [
        "hi-IN",  # Hindi
        "ta-IN",  # Tamil
        "te-IN",  # Telugu
        "bn-IN",  # Bengali
        "mr-IN",  # Marathi
        "gu-IN",  # Gujarati
        "kn-IN",  # Kannada
        "ml-IN",  # Malayalam
        "pa-IN",  # Punjabi
    ]
    
    def __init__(
        self,
        polly_client: Optional[PollyClient] = None,
        s3_client: Optional[S3Client] = None,
    ):
        """
        Initialize text-to-speech service.
        
        Args:
            polly_client: Amazon Polly client
            s3_client: S3 client for storing audio files
        """
        self.polly_client = polly_client or PollyClient()
        self.s3_client = s3_client
        logger.info("Initialized TextToSpeechService")
    
    def synthesize_speech(
        self,
        text: str,
        language_code: str = "en-US",
        voice_id: Optional[str] = None,
        audio_format: str = "mp3",
        engine: str = "neural",
    ) -> SynthesisResult:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to convert to speech
            language_code: Language code (e.g., 'en-US', 'hi-IN')
            voice_id: Specific voice ID (optional, auto-selected if not provided)
            audio_format: Output audio format (mp3, ogg_vorbis, pcm)
            engine: Speech engine (neural, standard)
        
        Returns:
            SynthesisResult with audio data and metadata
        
        Raises:
            VoiceProcessingError: If synthesis fails
        """
        try:
            # Select voice if not provided
            if not voice_id:
                voice_id = self._select_voice(language_code)
            
            logger.info(
                f"Synthesizing speech: language={language_code}, "
                f"voice={voice_id}, format={audio_format}, engine={engine}"
            )
            
            # Validate text length
            if not text or len(text.strip()) == 0:
                raise VoiceProcessingError(
                    "Text cannot be empty",
                    operation="synthesize_speech",
                )
            
            # Synthesize speech using Polly
            audio_data = self.polly_client.synthesize_speech(
                text=text,
                voice_id=voice_id,
                output_format=audio_format,
                language_code=language_code,
                engine=engine,
            )
            
            # Create result
            result = SynthesisResult(
                audio_data=audio_data,
                voice_id=voice_id,
                language_code=language_code,
                text_length=len(text),
                audio_format=audio_format,
                engine=engine,
                metadata={
                    "is_bilingual": voice_id in self.BILINGUAL_VOICES,
                    "is_indian_language": self._is_indian_language(language_code),
                    "audio_size_bytes": len(audio_data),
                },
            )
            
            logger.info(
                f"Successfully synthesized speech: {len(audio_data)} bytes, "
                f"voice={voice_id}"
            )
            
            return result
            
        except VoiceProcessingError:
            raise
        except Exception as e:
            logger.error(f"Failed to synthesize speech: {e}")
            raise VoiceProcessingError(
                f"Failed to synthesize speech: {str(e)}",
                operation="synthesize_speech",
                details={
                    "language": language_code,
                    "voice": voice_id,
                    "format": audio_format,
                },
            )
    
    def synthesize_with_preferences(
        self,
        text: str,
        user_preferences: Dict[str, Any],
        audio_format: str = "mp3",
    ) -> SynthesisResult:
        """
        Synthesize speech using user preferences.
        
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
            # Extract preferences
            language_code = user_preferences.get("language", "en")
            voice_id = user_preferences.get("voice_id")
            
            # Convert language code to full format if needed
            if "-" not in language_code:
                language_code = self._expand_language_code(language_code)
            
            logger.info(
                f"Synthesizing with user preferences: "
                f"language={language_code}, voice={voice_id}"
            )
            
            return self.synthesize_speech(
                text=text,
                language_code=language_code,
                voice_id=voice_id,
                audio_format=audio_format,
            )
            
        except Exception as e:
            logger.error(f"Failed to synthesize with preferences: {e}")
            raise VoiceProcessingError(
                f"Failed to synthesize with preferences: {str(e)}",
                operation="synthesize_with_preferences",
            )
    
    def synthesize_to_stream(
        self,
        text: str,
        language_code: str = "en-US",
        voice_id: Optional[str] = None,
        audio_format: str = "mp3",
    ) -> BytesIO:
        """
        Synthesize speech and return as stream.
        
        Args:
            text: Text to convert to speech
            language_code: Language code
            voice_id: Specific voice ID (optional)
            audio_format: Output audio format
        
        Returns:
            BytesIO stream containing audio data
        
        Raises:
            VoiceProcessingError: If synthesis fails
        """
        try:
            result = self.synthesize_speech(
                text=text,
                language_code=language_code,
                voice_id=voice_id,
                audio_format=audio_format,
            )
            
            stream = BytesIO(result.audio_data)
            stream.seek(0)
            return stream
            
        except Exception as e:
            logger.error(f"Failed to synthesize to stream: {e}")
            raise VoiceProcessingError(
                f"Failed to synthesize to stream: {str(e)}",
                operation="synthesize_to_stream",
            )
    
    def get_available_voices(
        self,
        language_code: Optional[str] = None,
        include_bilingual: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get available voices for a language.
        
        Args:
            language_code: Language code to filter by (optional)
            include_bilingual: Include bilingual voices
        
        Returns:
            List of voice information dictionaries
        
        Raises:
            VoiceProcessingError: If retrieval fails
        """
        try:
            voices = self.polly_client.get_available_voices(
                language_code=language_code
            )
            
            # Add bilingual information
            for voice in voices:
                voice_id = voice.get("Id")
                if voice_id in self.BILINGUAL_VOICES:
                    voice["IsBilingual"] = True
                    voice["SupportedLanguages"] = self.BILINGUAL_VOICES[voice_id]
                else:
                    voice["IsBilingual"] = False
            
            # Filter bilingual if requested
            if not include_bilingual:
                voices = [v for v in voices if not v.get("IsBilingual", False)]
            
            logger.info(f"Retrieved {len(voices)} available voices")
            return voices
            
        except Exception as e:
            logger.error(f"Failed to get available voices: {e}")
            raise VoiceProcessingError(
                f"Failed to get available voices: {str(e)}",
                operation="get_available_voices",
            )
    
    def get_indian_language_voices(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get voices for Indian languages.
        
        Returns:
            Dictionary mapping language codes to voice information
        
        Raises:
            VoiceProcessingError: If retrieval fails
        """
        try:
            indian_voices = {}
            
            for lang_code in self.INDIAN_LANGUAGES:
                try:
                    voices = self.get_available_voices(language_code=lang_code)
                    if voices:
                        indian_voices[lang_code] = voices
                except Exception as e:
                    logger.warning(
                        f"Could not retrieve voices for {lang_code}: {e}"
                    )
            
            logger.info(
                f"Retrieved Indian language voices for "
                f"{len(indian_voices)} languages"
            )
            return indian_voices
            
        except Exception as e:
            logger.error(f"Failed to get Indian language voices: {e}")
            raise VoiceProcessingError(
                f"Failed to get Indian language voices: {str(e)}",
                operation="get_indian_language_voices",
            )
    
    def get_bilingual_voices(self) -> Dict[str, List[str]]:
        """
        Get bilingual voices and their supported languages.
        
        Returns:
            Dictionary mapping voice IDs to supported language codes
        """
        return self.BILINGUAL_VOICES.copy()
    
    def _select_voice(self, language_code: str) -> str:
        """
        Select appropriate voice for language.
        
        Args:
            language_code: Language code
        
        Returns:
            Voice ID
        """
        # Check if we have a direct mapping
        if language_code in self.VOICE_MAP:
            return self.VOICE_MAP[language_code]
        
        # Try to match by language prefix (e.g., 'en' from 'en-US')
        lang_prefix = language_code.split("-")[0]
        for code, voice in self.VOICE_MAP.items():
            if code.startswith(lang_prefix):
                logger.info(
                    f"Using voice {voice} for {language_code} "
                    f"(matched via {code})"
                )
                return voice
        
        # Default to Joanna for English
        logger.warning(
            f"No voice mapping found for {language_code}, "
            f"defaulting to Joanna"
        )
        return "Joanna"
    
    def _is_indian_language(self, language_code: str) -> bool:
        """
        Check if language is an Indian language.
        
        Args:
            language_code: Language code
        
        Returns:
            True if Indian language
        """
        return language_code in self.INDIAN_LANGUAGES
    
    def _expand_language_code(self, short_code: str) -> str:
        """
        Expand short language code to full format.
        
        Args:
            short_code: Short language code (e.g., 'en', 'hi')
        
        Returns:
            Full language code (e.g., 'en-US', 'hi-IN')
        """
        # Map short codes to full codes
        expansion_map = {
            "en": "en-US",
            "hi": "hi-IN",
            "ta": "ta-IN",
            "te": "te-IN",
            "bn": "bn-IN",
            "mr": "mr-IN",
            "gu": "gu-IN",
            "kn": "kn-IN",
            "ml": "ml-IN",
            "pa": "pa-IN",
            "es": "es-ES",
            "fr": "fr-FR",
            "de": "de-DE",
            "it": "it-IT",
            "pt": "pt-BR",
            "ja": "ja-JP",
            "ko": "ko-KR",
            "zh": "zh-CN",
        }
        
        return expansion_map.get(short_code, f"{short_code}-US")
    
    def validate_voice_for_language(
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
        # Check bilingual voices
        if voice_id in self.BILINGUAL_VOICES:
            return language_code in self.BILINGUAL_VOICES[voice_id]
        
        # Check standard voice mappings
        expected_voice = self.VOICE_MAP.get(language_code)
        return voice_id == expected_voice
