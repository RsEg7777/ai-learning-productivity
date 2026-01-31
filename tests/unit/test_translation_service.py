"""Unit tests for translation service."""

import pytest
from unittest.mock import Mock, patch
from src.services.multilingual.translation_service import TranslationService
from src.shared.utils.errors import LanguageProcessingError


class TestTranslationService:
    """Test suite for TranslationService."""

    @pytest.fixture
    def mock_translate_client(self):
        """Create a mock Translate client."""
        return Mock()

    @pytest.fixture
    def mock_comprehend_client(self):
        """Create a mock Comprehend client."""
        return Mock()

    @pytest.fixture
    def translation_service(self, mock_translate_client, mock_comprehend_client):
        """Create a TranslationService instance with mocked clients."""
        return TranslationService(
            translate_client=mock_translate_client,
            comprehend_client=mock_comprehend_client,
        )

    def test_translate_english_to_hindi(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translating from English to Hindi."""
        # Arrange
        text = "Machine learning is a powerful technology"
        mock_comprehend_client.detect_entities.return_value = [
            {"Text": "Machine learning", "Type": "TITLE", "Score": 0.95}
        ]
        mock_comprehend_client.extract_technical_terms.return_value = [
            "Machine learning"
        ]
        mock_translate_client.translate_text.return_value = (
            "Machine learning एक शक्तिशाली तकनीक है"
        )

        # Act
        result = translation_service.translate(text, "en", "hi")

        # Assert
        assert result["translated_text"] == "Machine learning एक शक्तिशाली तकनीक है"
        assert result["source_language"] == "en"
        assert result["target_language"] == "hi"
        assert "Machine learning" in result["technical_terms_preserved"]
        assert "context" in result

    def test_translate_same_language(self, translation_service):
        """Test translation when source and target are the same."""
        # Arrange
        text = "Test text"

        # Act
        result = translation_service.translate(text, "en", "en")

        # Assert
        assert result["translated_text"] == text
        assert result["source_language"] == "en"
        assert result["target_language"] == "en"
        assert result["technical_terms_preserved"] == []

    def test_translate_empty_text(self, translation_service):
        """Test translating empty text."""
        with pytest.raises(LanguageProcessingError, match="Text cannot be empty"):
            translation_service.translate("", "en", "hi")

    def test_translate_without_technical_term_preservation(
        self, translation_service, mock_translate_client
    ):
        """Test translation without technical term preservation."""
        # Arrange
        text = "Simple text"
        mock_translate_client.translate_text.return_value = "सरल पाठ"

        # Act
        result = translation_service.translate(
            text, "en", "hi", preserve_technical_terms=False
        )

        # Assert
        assert result["translated_text"] == "सरल पाठ"
        assert result["technical_terms_preserved"] == []
        mock_translate_client.translate_text.assert_called_once()

    def test_translate_with_acronyms(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translation preserves acronyms like API, SDK."""
        # Arrange
        text = "Use the API and SDK for development"
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = (
            "विकास के लिए API और SDK का उपयोग करें"
        )

        # Act
        result = translation_service.translate(text, "en", "hi")

        # Assert
        assert "API" in result["translated_text"]
        assert "SDK" in result["translated_text"]
        # Acronyms should be detected by pattern matching
        assert any(term in ["API", "SDK"] for term in result["technical_terms_preserved"])

    def test_translate_with_function_calls(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translation preserves function call syntax."""
        # Arrange
        text = "Call the getData() function to retrieve information"
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = (
            "जानकारी प्राप्त करने के लिए getData() फ़ंक्शन को कॉल करें"
        )

        # Act
        result = translation_service.translate(text, "en", "hi")

        # Assert
        assert "getData()" in result["translated_text"]

    def test_translate_with_version_numbers(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translation preserves version numbers."""
        # Arrange
        text = "Install version 2.5.1 of the library"
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = (
            "लाइब्रेरी का संस्करण 2.5.1 इंस्टॉल करें"
        )

        # Act
        result = translation_service.translate(text, "en", "hi")

        # Assert
        assert "2.5.1" in result["translated_text"]

    def test_translate_with_context(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translation with context from previous translations."""
        # Arrange
        text = "Use the same API endpoint"
        context = {
            "technical_terms": ["API"],
            "last_source_language": "en",
            "last_target_language": "hi",
        }
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = (
            "समान API एंडपॉइंट का उपयोग करें"
        )

        # Act
        result = translation_service.translate(text, "en", "hi", context=context)

        # Assert
        assert "API" in result["technical_terms_preserved"]
        assert result["context"]["technical_terms"] == ["API"]

    def test_translate_with_context_session(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translation with session-based context maintenance."""
        # Arrange
        text1 = "API is important"
        text2 = "Use the API correctly"
        session_id = "session123"
        
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.side_effect = [
            "API महत्वपूर्ण है",
            "API का सही उपयोग करें",
        ]

        # Act
        result1 = translation_service.translate_with_context(
            text1, "en", "hi", session_id
        )
        result2 = translation_service.translate_with_context(
            text2, "en", "hi", session_id
        )

        # Assert
        assert result1["session_id"] == session_id
        assert result1["context_maintained"] is False  # First translation
        assert result2["context_maintained"] is True  # Second translation has context
        assert "API" in result2["technical_terms_preserved"]

    def test_batch_translate(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test batch translation of multiple texts."""
        # Arrange
        texts = ["First text", "Second text", "Third text"]
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.side_effect = [
            "पहला पाठ",
            "दूसरा पाठ",
            "तीसरा पाठ",
        ]

        # Act
        results = translation_service.batch_translate(texts, "en", "hi")

        # Assert
        assert len(results) == 3
        assert results[0]["translated_text"] == "पहला पाठ"
        assert results[1]["translated_text"] == "दूसरा पाठ"
        assert results[2]["translated_text"] == "तीसरा पाठ"

    def test_batch_translate_with_error(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test batch translation with graceful error handling."""
        # Arrange
        texts = ["First text", "Second text"]
        mock_comprehend_client.detect_entities.side_effect = [
            [],
            Exception("Service error"),
        ]
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.side_effect = [
            "पहला पाठ",
            Exception("Translation error"),
        ]

        # Act
        results = translation_service.batch_translate(texts, "en", "hi")

        # Assert
        assert len(results) == 2
        assert results[0]["translated_text"] == "पहला पाठ"
        assert "error" in results[1]  # Second translation failed gracefully

    def test_clear_context(self, translation_service):
        """Test clearing translation context."""
        # Arrange
        session_id = "session123"
        translation_service._context_cache[session_id] = {"some": "context"}

        # Act
        translation_service.clear_context(session_id)

        # Assert
        assert session_id not in translation_service._context_cache

    def test_get_context(self, translation_service):
        """Test retrieving translation context."""
        # Arrange
        session_id = "session123"
        context = {"technical_terms": ["API"]}
        translation_service._context_cache[session_id] = context

        # Act
        retrieved_context = translation_service.get_context(session_id)

        # Assert
        assert retrieved_context == context

    def test_get_context_not_found(self, translation_service):
        """Test retrieving non-existent context."""
        # Act
        context = translation_service.get_context("nonexistent")

        # Assert
        assert context is None

    def test_extract_technical_terms_with_patterns(
        self, translation_service, mock_comprehend_client
    ):
        """Test technical term extraction using patterns."""
        # Arrange
        text = "Use API, SDK, and getData() with version 1.2.3"
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        terms = translation_service._extract_technical_terms(text, "en")

        # Assert
        assert "API" in terms
        assert "SDK" in terms
        assert "getData()" in terms
        assert "1.2.3" in terms

    def test_extract_technical_terms_with_entities(
        self, translation_service, mock_comprehend_client
    ):
        """Test technical term extraction using Comprehend entities."""
        # Arrange
        text = "Amazon Web Services provides cloud computing"
        mock_comprehend_client.detect_entities.return_value = [
            {"Text": "Amazon Web Services", "Type": "ORGANIZATION", "Score": 0.99},
            {"Text": "cloud computing", "Type": "TITLE", "Score": 0.85},
        ]
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        terms = translation_service._extract_technical_terms(text, "en")

        # Assert
        assert "Amazon Web Services" in terms
        assert "cloud computing" in terms

    def test_extract_technical_terms_with_comprehend_error(
        self, translation_service, mock_comprehend_client
    ):
        """Test technical term extraction when Comprehend fails."""
        # Arrange
        text = "Use API and SDK"
        mock_comprehend_client.detect_entities.side_effect = Exception("Service error")
        mock_comprehend_client.extract_technical_terms.side_effect = Exception(
            "Service error"
        )

        # Act
        terms = translation_service._extract_technical_terms(text, "en")

        # Assert - should still extract using patterns
        assert "API" in terms
        assert "SDK" in terms

    def test_translate_with_preservation_multiple_terms(
        self, translation_service, mock_translate_client
    ):
        """Test translation with multiple technical terms to preserve."""
        # Arrange
        text = "The API uses SDK for HTTP requests"
        technical_terms = ["API", "SDK", "HTTP"]
        mock_translate_client.translate_text.return_value = (
            "API, SDK का उपयोग HTTP अनुरोधों के लिए करता है"
        )

        # Act
        result = translation_service._translate_with_preservation(
            text, "en", "hi", technical_terms
        )

        # Assert
        assert "API" in result
        assert "SDK" in result
        assert "HTTP" in result

    def test_build_context(self, translation_service):
        """Test building context information."""
        # Arrange
        original = "Original text"
        translated = "अनुवादित पाठ"
        technical_terms = ["API", "SDK"]

        # Act
        context = translation_service._build_context(
            original, translated, "en", "hi", technical_terms
        )

        # Assert
        assert context["last_source_language"] == "en"
        assert context["last_target_language"] == "hi"
        assert context["technical_terms"] == ["API", "SDK"]
        assert context["text_length"] == len(original)
        assert context["translation_length"] == len(translated)

    def test_validate_translation_quality_all_preserved(self, translation_service):
        """Test translation quality validation with all terms preserved."""
        # Arrange
        original = "Use API and SDK"
        translated = "API और SDK का उपयोग करें"
        technical_terms = ["API", "SDK"]

        # Act
        validation = translation_service.validate_translation_quality(
            original, translated, technical_terms
        )

        # Assert
        assert validation["preservation_rate"] == 1.0
        assert len(validation["preserved_terms"]) == 2
        assert len(validation["missing_terms"]) == 0
        assert validation["length_reasonable"] is True
        assert validation["quality_score"] == 1.0

    def test_validate_translation_quality_missing_terms(self, translation_service):
        """Test translation quality validation with missing terms."""
        # Arrange
        original = "Use API and SDK"
        translated = "एपीआई और एसडीके का उपयोग करें"  # Terms translated, not preserved
        technical_terms = ["API", "SDK"]

        # Act
        validation = translation_service.validate_translation_quality(
            original, translated, technical_terms
        )

        # Assert
        assert validation["preservation_rate"] == 0.0
        assert len(validation["preserved_terms"]) == 0
        assert len(validation["missing_terms"]) == 2
        assert "API" in validation["missing_terms"]
        assert "SDK" in validation["missing_terms"]

    def test_validate_translation_quality_unreasonable_length(
        self, translation_service
    ):
        """Test translation quality validation with unreasonable length ratio."""
        # Arrange
        original = "Short"
        translated = "बहुत लंबा अनुवादित पाठ जो मूल से बहुत अधिक लंबा है"
        technical_terms = []

        # Act
        validation = translation_service.validate_translation_quality(
            original, translated, technical_terms
        )

        # Assert
        assert validation["length_reasonable"] is False
        assert validation["quality_score"] < 1.0

    def test_translate_hindi_to_english(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translating from Hindi to English."""
        # Arrange
        text = "API का उपयोग करके डेटा प्राप्त करें"
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = "Get data using API"

        # Act
        result = translation_service.translate(text, "hi", "en")

        # Assert
        assert result["translated_text"] == "Get data using API"
        assert result["source_language"] == "hi"
        assert result["target_language"] == "en"
        assert "API" in result["technical_terms_preserved"]

    def test_translate_with_snake_case_identifiers(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translation preserves snake_case identifiers."""
        # Arrange
        text = "Use the get_user_data function"
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = (
            "get_user_data फ़ंक्शन का उपयोग करें"
        )

        # Act
        result = translation_service.translate(text, "en", "hi")

        # Assert
        assert "get_user_data" in result["translated_text"]
        assert "get_user_data" in result["technical_terms_preserved"]

    def test_translate_with_camel_case_identifiers(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translation preserves camelCase identifiers."""
        # Arrange
        text = "Call getUserData to fetch information"
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = (
            "जानकारी प्राप्त करने के लिए getUserData को कॉल करें"
        )

        # Act
        result = translation_service.translate(text, "en", "hi")

        # Assert
        assert "getUserData" in result["translated_text"]
        assert "getUserData" in result["technical_terms_preserved"]

    def test_translate_with_html_tags(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translation preserves HTML tags."""
        # Arrange
        text = "Use <div> tags for layout"
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = (
            "लेआउट के लिए <div> टैग का उपयोग करें"
        )

        # Act
        result = translation_service.translate(text, "en", "hi")

        # Assert
        assert "<div>" in result["translated_text"]

    def test_translate_complex_technical_content(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translation of complex technical content with multiple term types."""
        # Arrange
        text = "Install SDK 2.5.1 and call initAPI() to start using the REST API"
        mock_comprehend_client.detect_entities.return_value = [
            {"Text": "REST API", "Type": "TITLE", "Score": 0.9}
        ]
        mock_comprehend_client.extract_technical_terms.return_value = ["REST API"]
        mock_translate_client.translate_text.return_value = (
            "SDK 2.5.1 इंस्टॉल करें और REST API का उपयोग शुरू करने के लिए "
            "initAPI() को कॉल करें"
        )

        # Act
        result = translation_service.translate(text, "en", "hi")

        # Assert
        assert "SDK" in result["technical_terms_preserved"]
        assert "2.5.1" in result["technical_terms_preserved"]
        assert "initAPI()" in result["technical_terms_preserved"]
        assert "REST API" in result["technical_terms_preserved"]
        assert all(
            term in result["translated_text"]
            for term in ["SDK", "2.5.1", "initAPI()", "REST API"]
        )
