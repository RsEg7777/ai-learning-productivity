"""Main multilingual support service coordinating language detection and processing."""

import logging
from typing import Dict, Any, List, Optional
from src.services.multilingual.language_detector import LanguageDetector
from src.services.multilingual.language_processor import LanguageProcessor
from src.shared.aws_clients.comprehend_client import ComprehendClient
from src.shared.aws_clients.translate_client import TranslateClient
from src.shared.utils.errors import LanguageDetectionError, LanguageProcessingError

logger = logging.getLogger(__name__)


class MultilingualService:
    """
    Main service for multilingual support.
    
    Coordinates language detection and processing for the AI Learning Assistant.
    Supports English and Indian languages (Hindi, Tamil, Telugu, Bengali, Marathi,
    Gujarati, Kannada, Malayalam, Punjabi, Odia).
    """

    def __init__(
        self,
        comprehend_client: Optional[ComprehendClient] = None,
        translate_client: Optional[TranslateClient] = None,
    ):
        """
        Initialize multilingual service.

        Args:
            comprehend_client: Optional ComprehendClient instance
            translate_client: Optional TranslateClient instance
        """
        self.comprehend_client = comprehend_client or ComprehendClient()
        self.translate_client = translate_client or TranslateClient()
        
        self.language_detector = LanguageDetector(self.comprehend_client)
        self.language_processor = LanguageProcessor(
            self.comprehend_client, self.translate_client
        )
        
        logger.info("Initialized MultilingualService")

    def detect_and_process(
        self,
        text: str,
        target_language: Optional[str] = None,
        preserve_technical_terms: bool = True,
    ) -> Dict[str, Any]:
        """
        Detect language and process content accordingly.

        Args:
            text: Text to process
            target_language: Optional target language for translation
            preserve_technical_terms: Whether to preserve technical terms

        Returns:
            Dictionary with:
                - detection: Language detection results
                - processing: Content processing results
                - translation: Translation results (if applicable)

        Raises:
            LanguageDetectionError: If language detection fails
            LanguageProcessingError: If content processing fails
        """
        if not text or not text.strip():
            raise LanguageProcessingError("Text cannot be empty")

        try:
            # Detect language
            detection = self.language_detector.detect_language(text)
            detected_language = detection["language_code"]

            logger.info(
                f"Processing content in {detection['language_name']} "
                f"({detected_language})"
            )

            # Process content in detected language
            processing = self.language_processor.process_content(
                text, detected_language, preserve_technical_terms
            )

            result = {
                "detection": detection,
                "processing": processing,
                "translation": None,
            }

            # Translate if target language is specified and different
            if target_language and target_language != detected_language:
                translation = self.language_processor.translate_content(
                    text,
                    detected_language,
                    target_language,
                    preserve_technical_terms,
                )
                result["translation"] = translation

            return result

        except (LanguageDetectionError, LanguageProcessingError) as e:
            logger.error(f"Failed to detect and process content: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in detect_and_process: {e}")
            raise LanguageProcessingError(f"Failed to process content: {str(e)}")

    def process_in_same_language(
        self, text: str, language_code: str
    ) -> Dict[str, Any]:
        """
        Process content in the same language (no translation).

        Args:
            text: Text to process
            language_code: Language code

        Returns:
            Processing results

        Raises:
            LanguageProcessingError: If processing fails
        """
        # Validate language is supported
        self.language_detector.validate_language_code(language_code)

        # Process content
        return self.language_processor.process_content(text, language_code)

    def translate_between_languages(
        self,
        text: str,
        source_language: str,
        target_language: str,
        preserve_technical_terms: bool = True,
    ) -> Dict[str, Any]:
        """
        Translate content between two languages.

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            preserve_technical_terms: Whether to preserve technical terms

        Returns:
            Translation results

        Raises:
            LanguageProcessingError: If translation fails
        """
        # Validate both languages are supported
        self.language_detector.validate_language_code(source_language)
        self.language_detector.validate_language_code(target_language)

        # Translate content
        return self.language_processor.translate_content(
            text, source_language, target_language, preserve_technical_terms
        )

    def handle_user_input(
        self, text: str, user_preferred_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle user input with automatic language detection and processing.

        This method implements the requirement: "WHEN a user inputs content in any
        Indian_Languages, THE System SHALL process and respond in the same language"

        Args:
            text: User input text
            user_preferred_language: User's preferred language (optional)

        Returns:
            Dictionary with:
                - detected_language: Detected language information
                - response_language: Language to use for response
                - processed_content: Processed content
                - should_translate: Whether translation is needed

        Raises:
            LanguageDetectionError: If language detection fails
            LanguageProcessingError: If content processing fails
        """
        try:
            # Detect input language
            detection = self.language_detector.detect_language(text)
            detected_language = detection["language_code"]

            # Determine response language
            # If input is in Indian language, respond in same language
            # Otherwise, use user's preferred language or detected language
            if detection["is_indian_language"]:
                response_language = detected_language
            elif user_preferred_language:
                response_language = user_preferred_language
            else:
                response_language = detected_language

            # Process content
            processing = self.language_processor.process_content(
                text, detected_language
            )

            result = {
                "detected_language": detection,
                "response_language": response_language,
                "processed_content": processing,
                "should_translate": detected_language != response_language,
            }

            logger.info(
                f"Handled user input: detected={detected_language}, "
                f"response={response_language}"
            )

            return result

        except (LanguageDetectionError, LanguageProcessingError) as e:
            logger.error(f"Failed to handle user input: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in handle_user_input: {e}")
            raise LanguageProcessingError(f"Failed to handle user input: {str(e)}")

    def maintain_language_context(
        self,
        current_text: str,
        previous_language: str,
        user_preferred_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Maintain language context across conversation turns.

        This implements the requirement: "WHEN a user switches languages during a
        session, THE System SHALL maintain context and continue the conversation
        seamlessly"

        Args:
            current_text: Current user input
            previous_language: Language from previous interaction
            user_preferred_language: User's preferred language

        Returns:
            Dictionary with language context information

        Raises:
            LanguageDetectionError: If language detection fails
        """
        try:
            # Detect current language
            detection = self.language_detector.detect_language(current_text)
            current_language = detection["language_code"]

            # Check if language switched
            language_switched = current_language != previous_language

            result = {
                "current_language": detection,
                "previous_language": previous_language,
                "language_switched": language_switched,
                "response_language": current_language,
                "context_maintained": True,
            }

            if language_switched:
                logger.info(
                    f"Language switch detected: {previous_language} -> "
                    f"{current_language}"
                )
                result["switch_message"] = (
                    f"Language switched from {previous_language} to {current_language}"
                )

            return result

        except LanguageDetectionError as e:
            logger.error(f"Failed to maintain language context: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in maintain_language_context: {e}")
            raise LanguageDetectionError(
                f"Failed to maintain language context: {str(e)}"
            )

    def get_supported_languages(self) -> Dict[str, Any]:
        """
        Get information about supported languages.

        Returns:
            Dictionary with supported language information
        """
        return {
            "all_languages": self.language_detector.get_supported_languages(),
            "indian_languages": self.language_detector.get_indian_languages(),
            "total_count": len(self.language_detector.get_supported_languages()),
            "indian_count": len(self.language_detector.get_indian_languages()),
        }

    def validate_language_support(self, language_code: str) -> Dict[str, Any]:
        """
        Validate and get information about a language.

        Args:
            language_code: Language code to validate

        Returns:
            Dictionary with language validation information
        """
        is_supported = self.language_detector.is_supported_language(language_code)
        is_indian = self.language_detector.is_indian_language(language_code)

        supported_languages = self.language_detector.get_supported_languages()
        language_name = supported_languages.get(language_code, "Unknown")

        return {
            "language_code": language_code,
            "language_name": language_name,
            "is_supported": is_supported,
            "is_indian_language": is_indian,
        }
