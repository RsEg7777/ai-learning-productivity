"""Amazon Polly client for text-to-speech."""

import logging
from typing import Optional, BinaryIO
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class PollyClient:
    """Client for Amazon Polly operations."""

    def __init__(self, region: Optional[str] = None) -> None:
        """
        Initialize Polly client.

        Args:
            region: AWS region (optional)
        """
        self.region = region or "us-east-1"
        self.client = boto3.client("polly", region_name=self.region)
        logger.info(f"Initialized PollyClient in region: {self.region}")

    def synthesize_speech(
        self,
        text: str,
        voice_id: str = "Joanna",
        output_format: str = "mp3",
        language_code: Optional[str] = None,
        engine: str = "neural",
    ) -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            voice_id: Voice identifier (e.g., 'Joanna', 'Aditi', 'Kajal')
            output_format: Output format (mp3, ogg_vorbis, pcm)
            language_code: Language code (optional, auto-detected from voice)
            engine: Speech engine (neural, standard)

        Returns:
            Audio data as bytes

        Raises:
            ClientError: If synthesis fails
        """
        try:
            params = {
                "Text": text,
                "VoiceId": voice_id,
                "OutputFormat": output_format,
                "Engine": engine,
            }

            if language_code:
                params["LanguageCode"] = language_code

            response = self.client.synthesize_speech(**params)
            audio_stream = response["AudioStream"]
            audio_data = audio_stream.read()

            logger.info(f"Successfully synthesized speech using voice {voice_id}")
            return audio_data

        except ClientError as e:
            logger.error(f"Failed to synthesize speech: {e}")
            raise

    def synthesize_to_file(
        self,
        text: str,
        output_file: BinaryIO,
        voice_id: str = "Joanna",
        output_format: str = "mp3",
        language_code: Optional[str] = None,
    ) -> None:
        """
        Synthesize speech and write to file.

        Args:
            text: Text to synthesize
            output_file: File object to write audio to
            voice_id: Voice identifier
            output_format: Output format
            language_code: Language code (optional)

        Raises:
            ClientError: If synthesis fails
        """
        audio_data = self.synthesize_speech(
            text=text,
            voice_id=voice_id,
            output_format=output_format,
            language_code=language_code,
        )
        output_file.write(audio_data)
        logger.info("Successfully wrote synthesized speech to file")

    def get_available_voices(self, language_code: Optional[str] = None) -> list:
        """
        Get list of available voices.

        Args:
            language_code: Filter by language code (optional)

        Returns:
            List of voice information

        Raises:
            ClientError: If retrieval fails
        """
        try:
            params = {}
            if language_code:
                params["LanguageCode"] = language_code

            response = self.client.describe_voices(**params)
            voices = response.get("Voices", [])

            logger.info(f"Retrieved {len(voices)} available voices")
            return voices

        except ClientError as e:
            logger.error(f"Failed to get available voices: {e}")
            raise

    def get_indian_language_voices(self) -> dict:
        """
        Get voices for Indian languages.

        Returns:
            Dictionary mapping language codes to voice information
        """
        indian_language_codes = [
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

        indian_voices = {}
        for lang_code in indian_language_codes:
            try:
                voices = self.get_available_voices(language_code=lang_code)
                if voices:
                    indian_voices[lang_code] = voices
            except Exception as e:
                logger.warning(f"Could not retrieve voices for {lang_code}: {e}")

        return indian_voices

    def synthesize_multilingual(
        self,
        text: str,
        language_code: str,
        output_format: str = "mp3",
    ) -> bytes:
        """
        Synthesize speech with automatic voice selection based on language.

        Args:
            text: Text to synthesize
            language_code: Language code (e.g., 'hi-IN', 'en-US')
            output_format: Output format

        Returns:
            Audio data as bytes
        """
        # Map language codes to preferred voices
        voice_map = {
            "en-US": "Joanna",
            "en-GB": "Emma",
            "hi-IN": "Aditi",  # Hindi (bilingual)
            "ta-IN": "Kajal",  # Tamil (bilingual)
            # Add more mappings as needed
        }

        voice_id = voice_map.get(language_code, "Joanna")

        return self.synthesize_speech(
            text=text,
            voice_id=voice_id,
            output_format=output_format,
            language_code=language_code,
        )
