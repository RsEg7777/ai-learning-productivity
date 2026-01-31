"""Language detection service using Amazon Comprehend."""

import logging
from typing import Dict, Any, List, Optional
from src.shared.aws_clients.comprehend_client import ComprehendClient
from src.shared.utils.errors import LanguageDetectionError

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Service for detecting languages in text content."""

    # Supported Indian languages as per requirements
    INDIAN_LANGUAGES = {
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati",
        "kn": "Kannada",
        "ml": "Malayalam",
        "pa": "Punjabi",
        "or": "Odia",
    }

    # All supported languages (Indian + English)
    SUPPORTED_LANGUAGES = {
        "en": "English",
        **INDIAN_LANGUAGES,
    }

    def __init__(self, comprehend_client: Optional[ComprehendClient] = None):
        """
        Initialize language detector.

        Args:
            comprehend_client: Optional ComprehendClient instance
        """
        self.comprehend_client = comprehend_client or ComprehendClient()
        logger.info("Initialized LanguageDetector")

    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the dominant language in text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with:
                - language_code: ISO 639-1 language code
                - language_name: Human-readable language name
                - confidence: Confidence score (0-1)
                - is_supported: Whether language is supported
                - is_indian_language: Whether it's an Indian language

        Raises:
            LanguageDetectionError: If detection fails
        """
        if not text or not text.strip():
            raise LanguageDetectionError("Text cannot be empty")

        try:
            # Use Comprehend to detect language
            result = self.comprehend_client.detect_dominant_language(text)
            language_code = result.get("LanguageCode", "en")
            confidence = result.get("Score", 0.0)

            # Check if language is supported
            is_supported = language_code in self.SUPPORTED_LANGUAGES
            is_indian_language = language_code in self.INDIAN_LANGUAGES

            # Get language name
            language_name = self.SUPPORTED_LANGUAGES.get(
                language_code, f"Unknown ({language_code})"
            )

            detection_result = {
                "language_code": language_code,
                "language_name": language_name,
                "confidence": confidence,
                "is_supported": is_supported,
                "is_indian_language": is_indian_language,
            }

            logger.info(
                f"Detected language: {language_name} ({language_code}) "
                f"with confidence {confidence:.2f}"
            )

            return detection_result

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            raise LanguageDetectionError(f"Failed to detect language: {str(e)}")

    def detect_languages_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Detect languages for multiple texts.

        Args:
            texts: List of texts to analyze

        Returns:
            List of detection results for each text

        Raises:
            LanguageDetectionError: If detection fails
        """
        results = []
        for i, text in enumerate(texts):
            try:
                result = self.detect_language(text)
                results.append(result)
            except LanguageDetectionError as e:
                logger.warning(f"Failed to detect language for text {i}: {e}")
                # Return default English result on error
                results.append({
                    "language_code": "en",
                    "language_name": "English",
                    "confidence": 0.0,
                    "is_supported": True,
                    "is_indian_language": False,
                    "error": str(e),
                })

        return results

    def is_supported_language(self, language_code: str) -> bool:
        """
        Check if a language code is supported.

        Args:
            language_code: ISO 639-1 language code

        Returns:
            True if language is supported
        """
        return language_code in self.SUPPORTED_LANGUAGES

    def is_indian_language(self, language_code: str) -> bool:
        """
        Check if a language code is an Indian language.

        Args:
            language_code: ISO 639-1 language code

        Returns:
            True if language is an Indian language
        """
        return language_code in self.INDIAN_LANGUAGES

    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get all supported languages.

        Returns:
            Dictionary mapping language codes to names
        """
        return self.SUPPORTED_LANGUAGES.copy()

    def get_indian_languages(self) -> Dict[str, str]:
        """
        Get all supported Indian languages.

        Returns:
            Dictionary mapping language codes to names
        """
        return self.INDIAN_LANGUAGES.copy()

    def validate_language_code(self, language_code: str) -> None:
        """
        Validate that a language code is supported.

        Args:
            language_code: ISO 639-1 language code

        Raises:
            LanguageDetectionError: If language is not supported
        """
        if not self.is_supported_language(language_code):
            supported = ", ".join(self.SUPPORTED_LANGUAGES.keys())
            raise LanguageDetectionError(
                f"Language '{language_code}' is not supported. "
                f"Supported languages: {supported}"
            )
