"""Language-specific processing pipelines."""

import logging
from typing import Dict, Any, List, Optional
from src.shared.aws_clients.comprehend_client import ComprehendClient
from src.shared.aws_clients.translate_client import TranslateClient
from src.shared.utils.errors import LanguageProcessingError

logger = logging.getLogger(__name__)


class LanguageProcessor:
    """Service for language-specific content processing."""

    def __init__(
        self,
        comprehend_client: Optional[ComprehendClient] = None,
        translate_client: Optional[TranslateClient] = None,
    ):
        """
        Initialize language processor.

        Args:
            comprehend_client: Optional ComprehendClient instance
            translate_client: Optional TranslateClient instance
        """
        self.comprehend_client = comprehend_client or ComprehendClient()
        self.translate_client = translate_client or TranslateClient()
        logger.info("Initialized LanguageProcessor")

    def process_content(
        self, text: str, language_code: str, preserve_technical_terms: bool = True
    ) -> Dict[str, Any]:
        """
        Process content in a specific language.

        Args:
            text: Text to process
            language_code: ISO 639-1 language code
            preserve_technical_terms: Whether to preserve technical terms

        Returns:
            Dictionary with:
                - processed_text: Processed text
                - language_code: Language code
                - key_phrases: Extracted key phrases
                - entities: Detected entities
                - technical_terms: Extracted technical terms (if requested)

        Raises:
            LanguageProcessingError: If processing fails
        """
        if not text or not text.strip():
            raise LanguageProcessingError("Text cannot be empty")

        try:
            result = {
                "processed_text": text,
                "language_code": language_code,
                "key_phrases": [],
                "entities": [],
                "technical_terms": [],
            }

            # Extract key phrases
            try:
                key_phrases = self.comprehend_client.extract_key_phrases(
                    text, language_code
                )
                result["key_phrases"] = key_phrases
                logger.info(f"Extracted {len(key_phrases)} key phrases")
            except Exception as e:
                logger.warning(f"Failed to extract key phrases: {e}")

            # Detect entities
            try:
                entities = self.comprehend_client.detect_entities(text, language_code)
                result["entities"] = entities
                logger.info(f"Detected {len(entities)} entities")
            except Exception as e:
                logger.warning(f"Failed to detect entities: {e}")

            # Extract technical terms if requested
            if preserve_technical_terms:
                try:
                    technical_terms = self.comprehend_client.extract_technical_terms(
                        text, language_code
                    )
                    result["technical_terms"] = technical_terms
                    logger.info(f"Extracted {len(technical_terms)} technical terms")
                except Exception as e:
                    logger.warning(f"Failed to extract technical terms: {e}")

            return result

        except Exception as e:
            logger.error(f"Content processing failed: {e}")
            raise LanguageProcessingError(f"Failed to process content: {str(e)}")

    def translate_content(
        self,
        text: str,
        source_language: str,
        target_language: str,
        preserve_technical_terms: bool = True,
    ) -> Dict[str, Any]:
        """
        Translate content between languages.

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            preserve_technical_terms: Whether to preserve technical terms

        Returns:
            Dictionary with:
                - translated_text: Translated text
                - source_language: Source language code
                - target_language: Target language code
                - technical_terms_preserved: List of preserved technical terms

        Raises:
            LanguageProcessingError: If translation fails
        """
        if not text or not text.strip():
            raise LanguageProcessingError("Text cannot be empty")

        if source_language == target_language:
            return {
                "translated_text": text,
                "source_language": source_language,
                "target_language": target_language,
                "technical_terms_preserved": [],
            }

        try:
            technical_terms = []

            # Extract technical terms if preservation is requested
            if preserve_technical_terms:
                try:
                    technical_terms = self.comprehend_client.extract_technical_terms(
                        text, source_language
                    )
                    logger.info(f"Identified {len(technical_terms)} technical terms to preserve")
                except Exception as e:
                    logger.warning(f"Failed to extract technical terms: {e}")

            # Translate with technical term preservation
            if technical_terms:
                translated_text = self.translate_client.translate_with_terminology(
                    text, source_language, target_language, technical_terms
                )
            else:
                translated_text = self.translate_client.translate_text(
                    text, source_language, target_language
                )

            result = {
                "translated_text": translated_text,
                "source_language": source_language,
                "target_language": target_language,
                "technical_terms_preserved": technical_terms,
            }

            logger.info(
                f"Successfully translated from {source_language} to {target_language}"
            )
            return result

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise LanguageProcessingError(f"Failed to translate content: {str(e)}")

    def process_multilingual_content(
        self, text: str, detected_language: str, target_language: str = "en"
    ) -> Dict[str, Any]:
        """
        Process content that may need translation.

        Args:
            text: Text to process
            detected_language: Detected language code
            target_language: Target language for processing (default: English)

        Returns:
            Dictionary with:
                - original_text: Original text
                - processed_text: Processed/translated text
                - original_language: Original language code
                - processing_language: Language used for processing
                - was_translated: Whether translation occurred
                - analysis: Content analysis results

        Raises:
            LanguageProcessingError: If processing fails
        """
        try:
            result = {
                "original_text": text,
                "processed_text": text,
                "original_language": detected_language,
                "processing_language": detected_language,
                "was_translated": False,
                "analysis": {},
            }

            # Process in original language
            analysis = self.process_content(text, detected_language)
            result["analysis"] = analysis

            # Translate if needed and target language is different
            if detected_language != target_language:
                translation = self.translate_content(
                    text, detected_language, target_language
                )
                result["processed_text"] = translation["translated_text"]
                result["processing_language"] = target_language
                result["was_translated"] = True
                result["technical_terms_preserved"] = translation[
                    "technical_terms_preserved"
                ]

            logger.info(
                f"Processed multilingual content: {detected_language} -> "
                f"{result['processing_language']}"
            )
            return result

        except Exception as e:
            logger.error(f"Multilingual content processing failed: {e}")
            raise LanguageProcessingError(
                f"Failed to process multilingual content: {str(e)}"
            )

    def extract_context_for_translation(
        self, text: str, language_code: str
    ) -> Dict[str, Any]:
        """
        Extract context information to improve translation quality.

        Args:
            text: Text to analyze
            language_code: Language code

        Returns:
            Dictionary with context information including sentiment, entities, etc.

        Raises:
            LanguageProcessingError: If extraction fails
        """
        try:
            context = {
                "language_code": language_code,
                "sentiment": None,
                "entities": [],
                "key_phrases": [],
            }

            # Analyze sentiment
            try:
                sentiment = self.comprehend_client.analyze_sentiment(text, language_code)
                context["sentiment"] = sentiment
            except Exception as e:
                logger.warning(f"Failed to analyze sentiment: {e}")

            # Extract entities
            try:
                entities = self.comprehend_client.detect_entities(text, language_code)
                context["entities"] = entities
            except Exception as e:
                logger.warning(f"Failed to detect entities: {e}")

            # Extract key phrases
            try:
                key_phrases = self.comprehend_client.extract_key_phrases(
                    text, language_code
                )
                context["key_phrases"] = key_phrases
            except Exception as e:
                logger.warning(f"Failed to extract key phrases: {e}")

            return context

        except Exception as e:
            logger.error(f"Context extraction failed: {e}")
            raise LanguageProcessingError(f"Failed to extract context: {str(e)}")

    def batch_process_content(
        self, texts: List[str], language_code: str
    ) -> List[Dict[str, Any]]:
        """
        Process multiple texts in the same language.

        Args:
            texts: List of texts to process
            language_code: Language code

        Returns:
            List of processing results

        Raises:
            LanguageProcessingError: If processing fails
        """
        results = []
        for i, text in enumerate(texts):
            try:
                result = self.process_content(text, language_code)
                results.append(result)
            except LanguageProcessingError as e:
                logger.warning(f"Failed to process text {i}: {e}")
                results.append({
                    "processed_text": text,
                    "language_code": language_code,
                    "key_phrases": [],
                    "entities": [],
                    "technical_terms": [],
                    "error": str(e),
                })

        return results
