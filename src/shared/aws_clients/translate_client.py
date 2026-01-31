"""Amazon Translate client for multilingual support."""

import logging
from typing import Optional, List
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class TranslateClient:
    """Client for Amazon Translate operations."""

    def __init__(self, region: Optional[str] = None) -> None:
        """
        Initialize Translate client.

        Args:
            region: AWS region (optional)
        """
        self.region = region or "us-east-1"
        self.client = boto3.client("translate", region_name=self.region)
        logger.info(f"Initialized TranslateClient in region: {self.region}")

    def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
        terminology_names: Optional[List[str]] = None,
    ) -> str:
        """
        Translate text from source to target language.

        Args:
            text: Text to translate
            source_language: Source language code (e.g., 'en', 'hi')
            target_language: Target language code
            terminology_names: Custom terminology names (optional)

        Returns:
            Translated text

        Raises:
            ClientError: If translation fails
        """
        try:
            params = {
                "Text": text,
                "SourceLanguageCode": source_language,
                "TargetLanguageCode": target_language,
            }

            if terminology_names:
                params["TerminologyNames"] = terminology_names

            response = self.client.translate_text(**params)
            translated_text = response["TranslatedText"]

            logger.info(f"Successfully translated text from {source_language} to {target_language}")
            return translated_text

        except ClientError as e:
            logger.error(f"Failed to translate text: {e}")
            raise

    def translate_with_terminology(
        self,
        text: str,
        source_language: str,
        target_language: str,
        technical_terms: List[str],
    ) -> str:
        """
        Translate text while preserving technical terms.

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            technical_terms: List of technical terms to preserve

        Returns:
            Translated text with preserved technical terms
        """
        # For now, we'll use a simple approach of marking technical terms
        # In production, you would create custom terminology in Amazon Translate
        marked_text = text
        term_markers = {}

        # Mark technical terms with placeholders
        for i, term in enumerate(technical_terms):
            placeholder = f"__TECH_TERM_{i}__"
            term_markers[placeholder] = term
            marked_text = marked_text.replace(term, placeholder)

        # Translate the marked text
        translated = self.translate_text(marked_text, source_language, target_language)

        # Restore technical terms
        for placeholder, term in term_markers.items():
            translated = translated.replace(placeholder, term)

        return translated

    def detect_language(self, text: str) -> dict:
        """
        Detect the dominant language of text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with language code and confidence score

        Raises:
            ClientError: If detection fails
        """
        # Note: Amazon Translate doesn't have a direct language detection API
        # We'll use Amazon Comprehend for this (see comprehend_client.py)
        # This is a placeholder that would integrate with Comprehend
        logger.warning("Language detection should use ComprehendClient")
        return {"LanguageCode": "en", "Score": 0.0}

    def batch_translate(
        self,
        texts: List[str],
        source_language: str,
        target_language: str,
    ) -> List[str]:
        """
        Translate multiple texts.

        Args:
            texts: List of texts to translate
            source_language: Source language code
            target_language: Target language code

        Returns:
            List of translated texts

        Raises:
            ClientError: If translation fails
        """
        translated_texts = []

        for text in texts:
            try:
                translated = self.translate_text(text, source_language, target_language)
                translated_texts.append(translated)
            except ClientError as e:
                logger.error(f"Failed to translate text in batch: {e}")
                translated_texts.append(text)  # Return original on error

        return translated_texts

    def get_supported_languages(self) -> dict:
        """
        Get supported language pairs.

        Returns:
            Dictionary of supported languages
        """
        # Common Indian languages supported by Amazon Translate
        indian_languages = {
            "hi": "Hindi",
            "ta": "Tamil",
            "te": "Telugu",
            "bn": "Bengali",
            "mr": "Marathi",
            "gu": "Gujarati",
            "kn": "Kannada",
            "ml": "Malayalam",
            "pa": "Punjabi",
        }

        other_languages = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
        }

        return {**indian_languages, **other_languages}
