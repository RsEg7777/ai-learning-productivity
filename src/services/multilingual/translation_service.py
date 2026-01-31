"""Translation service with Amazon Translate for multilingual support."""

import logging
import re
from typing import Dict, Any, List, Optional, Set
from src.shared.aws_clients.translate_client import TranslateClient
from src.shared.aws_clients.comprehend_client import ComprehendClient
from src.shared.utils.errors import LanguageProcessingError

logger = logging.getLogger(__name__)


class TranslationService:
    """
    Service for translating content between languages with technical term preservation.
    
    This service implements requirements:
    - 4.2: Maintain context across language switches
    - 4.3: Preserve technical terms during translation
    - 4.5: Maintain original meaning and technical accuracy
    """

    # Common technical term patterns
    TECHNICAL_PATTERNS = [
        r'\b[A-Z]{2,}\b',  # Acronyms (API, SDK, HTTP)
        r'\b\w+\(\)',  # Function calls
        r'\b[a-z]+_[a-z_]+\b',  # Snake case identifiers
        r'\b[a-z]+[A-Z]\w+\b',  # Camel case identifiers
        r'\b\d+\.\d+\.\d+\b',  # Version numbers
        r'<[^>]+>',  # HTML/XML tags
        r'\$\w+',  # Variables
    ]

    def __init__(
        self,
        translate_client: Optional[TranslateClient] = None,
        comprehend_client: Optional[ComprehendClient] = None,
    ):
        """
        Initialize translation service.

        Args:
            translate_client: Optional TranslateClient instance
            comprehend_client: Optional ComprehendClient instance
        """
        self.translate_client = translate_client or TranslateClient()
        self.comprehend_client = comprehend_client or ComprehendClient()
        self._context_cache: Dict[str, Any] = {}
        logger.info("Initialized TranslationService")

    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        preserve_technical_terms: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Translate text between languages with technical term preservation.

        Args:
            text: Text to translate
            source_language: Source language code (e.g., 'en', 'hi')
            target_language: Target language code
            preserve_technical_terms: Whether to preserve technical terms
            context: Optional context from previous translations

        Returns:
            Dictionary with:
                - translated_text: Translated text
                - source_language: Source language code
                - target_language: Target language code
                - technical_terms_preserved: List of preserved terms
                - context: Context information for future translations

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
                "context": context or {},
            }

        try:
            technical_terms = []
            
            # Extract technical terms if preservation is requested
            if preserve_technical_terms:
                technical_terms = self._extract_technical_terms(
                    text, source_language, context
                )
                logger.info(
                    f"Identified {len(technical_terms)} technical terms to preserve"
                )

            # Perform translation with term preservation
            if technical_terms:
                translated_text = self._translate_with_preservation(
                    text, source_language, target_language, technical_terms
                )
            else:
                translated_text = self.translate_client.translate_text(
                    text, source_language, target_language
                )

            # Build context for future translations
            translation_context = self._build_context(
                text, translated_text, source_language, target_language, technical_terms
            )

            result = {
                "translated_text": translated_text,
                "source_language": source_language,
                "target_language": target_language,
                "technical_terms_preserved": technical_terms,
                "context": translation_context,
            }

            logger.info(
                f"Successfully translated from {source_language} to {target_language}"
            )
            return result

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise LanguageProcessingError(f"Failed to translate content: {str(e)}")

    def translate_with_context(
        self,
        text: str,
        source_language: str,
        target_language: str,
        session_id: str,
        preserve_technical_terms: bool = True,
    ) -> Dict[str, Any]:
        """
        Translate text while maintaining context from previous translations.

        This implements requirement 4.2: "WHEN a user switches languages during a
        session, THE System SHALL maintain context and continue the conversation
        seamlessly"

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            session_id: Session identifier for context tracking
            preserve_technical_terms: Whether to preserve technical terms

        Returns:
            Translation result with maintained context

        Raises:
            LanguageProcessingError: If translation fails
        """
        # Retrieve context from previous translations in this session
        context = self._context_cache.get(session_id, {})
        
        # Perform translation with context
        result = self.translate(
            text, source_language, target_language, preserve_technical_terms, context
        )

        # Update context cache
        self._context_cache[session_id] = result["context"]
        
        # Add session information
        result["session_id"] = session_id
        result["context_maintained"] = bool(context)

        logger.info(f"Translated with context for session {session_id}")
        return result

    def batch_translate(
        self,
        texts: List[str],
        source_language: str,
        target_language: str,
        preserve_technical_terms: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Translate multiple texts in batch.

        Args:
            texts: List of texts to translate
            source_language: Source language code
            target_language: Target language code
            preserve_technical_terms: Whether to preserve technical terms

        Returns:
            List of translation results

        Raises:
            LanguageProcessingError: If translation fails
        """
        results = []
        
        for i, text in enumerate(texts):
            try:
                result = self.translate(
                    text, source_language, target_language, preserve_technical_terms
                )
                results.append(result)
            except LanguageProcessingError as e:
                logger.warning(f"Failed to translate text {i}: {e}")
                results.append({
                    "translated_text": text,
                    "source_language": source_language,
                    "target_language": target_language,
                    "technical_terms_preserved": [],
                    "context": {},
                    "error": str(e),
                })

        logger.info(f"Batch translated {len(texts)} texts")
        return results

    def clear_context(self, session_id: str) -> None:
        """
        Clear translation context for a session.

        Args:
            session_id: Session identifier
        """
        if session_id in self._context_cache:
            del self._context_cache[session_id]
            logger.info(f"Cleared context for session {session_id}")

    def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get translation context for a session.

        Args:
            session_id: Session identifier

        Returns:
            Context dictionary or None if not found
        """
        return self._context_cache.get(session_id)

    def _extract_technical_terms(
        self, text: str, language_code: str, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Extract technical terms from text.

        Args:
            text: Text to analyze
            language_code: Language code
            context: Optional context from previous translations

        Returns:
            List of technical terms
        """
        technical_terms: Set[str] = set()

        # Extract using pattern matching
        for pattern in self.TECHNICAL_PATTERNS:
            matches = re.findall(pattern, text)
            technical_terms.update(matches)

        # Extract using Comprehend (entities and key phrases)
        try:
            # Get entities that might be technical terms
            entities = self.comprehend_client.detect_entities(text, language_code)
            for entity in entities:
                entity_text = entity.get("Text", "")
                entity_type = entity.get("Type", "")
                
                # Consider TITLE, ORGANIZATION, and COMMERCIAL_ITEM as potential technical terms
                if entity_type in ["TITLE", "ORGANIZATION", "COMMERCIAL_ITEM"]:
                    technical_terms.add(entity_text)

            # Get technical terms from Comprehend
            comprehend_terms = self.comprehend_client.extract_technical_terms(
                text, language_code
            )
            technical_terms.update(comprehend_terms)

        except Exception as e:
            logger.warning(f"Failed to extract technical terms using Comprehend: {e}")

        # Add terms from context if available
        if context and "technical_terms" in context:
            technical_terms.update(context["technical_terms"])

        return sorted(list(technical_terms))

    def _translate_with_preservation(
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
            technical_terms: List of terms to preserve

        Returns:
            Translated text with preserved terms
        """
        # Create a mapping of terms to placeholders
        term_map = {}
        modified_text = text
        
        # Sort terms by length (longest first) to avoid partial replacements
        sorted_terms = sorted(technical_terms, key=len, reverse=True)
        
        for i, term in enumerate(sorted_terms):
            placeholder = f"__TECH_TERM_{i}__"
            term_map[placeholder] = term
            # Use word boundaries to avoid partial matches
            modified_text = re.sub(
                r'\b' + re.escape(term) + r'\b',
                placeholder,
                modified_text,
                flags=re.IGNORECASE
            )

        # Translate the modified text
        translated = self.translate_client.translate_text(
            modified_text, source_language, target_language
        )

        # Restore technical terms
        for placeholder, term in term_map.items():
            translated = translated.replace(placeholder, term)

        return translated

    def _build_context(
        self,
        original_text: str,
        translated_text: str,
        source_language: str,
        target_language: str,
        technical_terms: List[str],
    ) -> Dict[str, Any]:
        """
        Build context information for future translations.

        Args:
            original_text: Original text
            translated_text: Translated text
            source_language: Source language code
            target_language: Target language code
            technical_terms: Preserved technical terms

        Returns:
            Context dictionary
        """
        return {
            "last_source_language": source_language,
            "last_target_language": target_language,
            "technical_terms": technical_terms,
            "text_length": len(original_text),
            "translation_length": len(translated_text),
        }

    def validate_translation_quality(
        self, original_text: str, translated_text: str, technical_terms: List[str]
    ) -> Dict[str, Any]:
        """
        Validate translation quality and technical term preservation.

        Args:
            original_text: Original text
            translated_text: Translated text
            technical_terms: Expected technical terms

        Returns:
            Dictionary with validation results
        """
        # Check if technical terms are preserved
        preserved_terms = []
        missing_terms = []
        
        for term in technical_terms:
            if term in translated_text:
                preserved_terms.append(term)
            else:
                missing_terms.append(term)

        # Calculate preservation rate
        preservation_rate = (
            len(preserved_terms) / len(technical_terms)
            if technical_terms
            else 1.0
        )

        # Check length ratio (translations should be within reasonable bounds)
        length_ratio = len(translated_text) / len(original_text) if original_text else 0
        length_reasonable = 0.5 <= length_ratio <= 2.0

        return {
            "preserved_terms": preserved_terms,
            "missing_terms": missing_terms,
            "preservation_rate": preservation_rate,
            "length_ratio": length_ratio,
            "length_reasonable": length_reasonable,
            "quality_score": preservation_rate if length_reasonable else preservation_rate * 0.8,
        }
