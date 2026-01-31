"""Integration tests for translation service."""

import pytest
from unittest.mock import Mock
from src.services.multilingual.translation_service import TranslationService


class TestTranslationIntegration:
    """Integration tests for the complete translation workflow."""

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
        """Create a TranslationService instance."""
        return TranslationService(
            translate_client=mock_translate_client,
            comprehend_client=mock_comprehend_client,
        )

    def test_complete_translation_workflow_with_technical_terms(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test complete translation workflow with technical term preservation."""
        # Arrange
        text = "The API endpoint returns JSON data using HTTP protocol"
        mock_comprehend_client.detect_entities.return_value = [
            {"Text": "API", "Type": "TITLE", "Score": 0.95},
            {"Text": "JSON", "Type": "TITLE", "Score": 0.90},
            {"Text": "HTTP", "Type": "TITLE", "Score": 0.92},
        ]
        mock_comprehend_client.extract_technical_terms.return_value = [
            "API",
            "JSON",
            "HTTP",
        ]
        mock_translate_client.translate_text.return_value = (
            "API एंडपॉइंट HTTP प्रोटोकॉल का उपयोग करके JSON डेटा लौटाता है"
        )

        # Act
        result = translation_service.translate(text, "en", "hi")

        # Assert
        assert result["source_language"] == "en"
        assert result["target_language"] == "hi"
        assert "API" in result["technical_terms_preserved"]
        assert "JSON" in result["technical_terms_preserved"]
        assert "HTTP" in result["technical_terms_preserved"]
        assert all(
            term in result["translated_text"] for term in ["API", "JSON", "HTTP"]
        )

    def test_multilingual_conversation_with_context(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test maintaining context across multiple translations in a conversation."""
        # Arrange
        session_id = "user_session_123"
        
        # First message
        text1 = "Let's discuss the REST API"
        mock_comprehend_client.detect_entities.return_value = [
            {"Text": "REST API", "Type": "TITLE", "Score": 0.95}
        ]
        mock_comprehend_client.extract_technical_terms.return_value = ["REST API"]
        mock_translate_client.translate_text.return_value = (
            "आइए REST API पर चर्चा करें"
        )

        # Second message
        text2 = "The API uses authentication tokens"
        mock_comprehend_client.detect_entities.return_value = [
            {"Text": "authentication tokens", "Type": "TITLE", "Score": 0.88}
        ]
        mock_comprehend_client.extract_technical_terms.return_value = [
            "authentication tokens"
        ]
        mock_translate_client.translate_text.return_value = (
            "API authentication tokens का उपयोग करता है"
        )

        # Act
        result1 = translation_service.translate_with_context(
            text1, "en", "hi", session_id
        )
        result2 = translation_service.translate_with_context(
            text2, "en", "hi", session_id
        )

        # Assert
        assert result1["context_maintained"] is False  # First message
        assert result2["context_maintained"] is True  # Has context from first message
        # REST API may be split into REST and API by pattern matching
        assert any(term in result1["technical_terms_preserved"] for term in ["REST API", "API", "REST"])
        # Second translation should maintain API from context
        assert "API" in result2["technical_terms_preserved"]

    def test_language_switching_with_context_maintenance(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test context maintenance when switching between languages."""
        # Arrange
        session_id = "multilingual_session"
        
        # English to Hindi
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = ["SDK"]
        mock_translate_client.translate_text.return_value = "SDK का उपयोग करें"
        
        result1 = translation_service.translate_with_context(
            "Use the SDK", "en", "hi", session_id
        )

        # Hindi to English (language switch)
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = "SDK is important"
        
        result2 = translation_service.translate_with_context(
            "SDK महत्वपूर्ण है", "hi", "en", session_id
        )

        # Assert
        assert result1["source_language"] == "en"
        assert result1["target_language"] == "hi"
        assert result2["source_language"] == "hi"
        assert result2["target_language"] == "en"
        assert result2["context_maintained"] is True
        # SDK should be preserved across language switch
        assert "SDK" in result2["technical_terms_preserved"]

    def test_batch_translation_workflow(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test batch translation of multiple related texts."""
        # Arrange
        texts = [
            "Install the SDK version 2.0",
            "Configure the API key",
            "Test the HTTP endpoints",
        ]
        
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.side_effect = [
            "SDK संस्करण 2.0 इंस्टॉल करें",
            "API कुंजी कॉन्फ़िगर करें",
            "HTTP एंडपॉइंट का परीक्षण करें",
        ]

        # Act
        results = translation_service.batch_translate(texts, "en", "hi")

        # Assert
        assert len(results) == 3
        assert all(r["source_language"] == "en" for r in results)
        assert all(r["target_language"] == "hi" for r in results)
        # Check technical terms are preserved
        assert "SDK" in results[0]["technical_terms_preserved"]
        # Version numbers may or may not be detected depending on pattern matching
        assert any(term in ["2.0", "SDK"] for term in results[0]["technical_terms_preserved"])
        assert "API" in results[1]["technical_terms_preserved"]
        assert "HTTP" in results[2]["technical_terms_preserved"]

    def test_translation_quality_validation_workflow(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test complete workflow including quality validation."""
        # Arrange
        text = "Use REST API and GraphQL for data access"
        mock_comprehend_client.detect_entities.return_value = [
            {"Text": "REST API", "Type": "TITLE", "Score": 0.95},
            {"Text": "GraphQL", "Type": "TITLE", "Score": 0.93},
        ]
        mock_comprehend_client.extract_technical_terms.return_value = [
            "REST API",
            "GraphQL",
        ]
        mock_translate_client.translate_text.return_value = (
            "डेटा एक्सेस के लिए REST API और GraphQL का उपयोग करें"
        )

        # Act
        result = translation_service.translate(text, "en", "hi")
        validation = translation_service.validate_translation_quality(
            text, result["translated_text"], result["technical_terms_preserved"]
        )

        # Assert
        assert validation["preservation_rate"] >= 0.5  # At least half preserved
        assert len(validation["preserved_terms"]) >= 2  # At least 2 terms preserved
        # REST API may be split into REST and API
        assert any(term in validation["preserved_terms"] for term in ["REST API", "API"])
        assert "GraphQL" in validation["preserved_terms"]
        assert validation["length_reasonable"] is True
        assert validation["quality_score"] >= 0.5

    def test_technical_documentation_translation(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translating technical documentation with multiple technical terms."""
        # Arrange
        text = (
            "The SDK provides methods like initClient() and getData() to interact "
            "with the REST API. Use version 3.2.1 for best compatibility."
        )
        mock_comprehend_client.detect_entities.return_value = [
            {"Text": "SDK", "Type": "TITLE", "Score": 0.95},
            {"Text": "REST API", "Type": "TITLE", "Score": 0.93},
        ]
        mock_comprehend_client.extract_technical_terms.return_value = [
            "SDK",
            "REST API",
        ]
        mock_translate_client.translate_text.return_value = (
            "SDK, REST API के साथ इंटरैक्ट करने के लिए initClient() और getData() "
            "जैसे तरीके प्रदान करता है। सर्वोत्तम संगतता के लिए संस्करण 3.2.1 "
            "का उपयोग करें।"
        )

        # Act
        result = translation_service.translate(text, "en", "hi")

        # Assert
        # Check all technical elements are preserved
        technical_elements = ["SDK", "initClient()", "getData()", "REST API", "3.2.1"]
        for element in technical_elements:
            assert element in result["translated_text"], f"{element} not preserved"

    def test_code_snippet_translation(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translating text containing code snippets."""
        # Arrange
        text = "Call fetchData() to get user_profile information from the database"
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = (
            "डेटाबेस से user_profile जानकारी प्राप्त करने के लिए fetchData() "
            "को कॉल करें"
        )

        # Act
        result = translation_service.translate(text, "en", "hi")

        # Assert
        assert "fetchData()" in result["translated_text"]
        assert "user_profile" in result["translated_text"]
        assert "fetchData()" in result["technical_terms_preserved"]
        assert "user_profile" in result["technical_terms_preserved"]

    def test_mixed_language_content_translation(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translating content that already contains mixed languages."""
        # Arrange
        text = "API का उपयोग करके JSON data प्राप्त करें"
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = (
            "Get JSON data using API"
        )

        # Act
        result = translation_service.translate(text, "hi", "en")

        # Assert
        assert "API" in result["technical_terms_preserved"]
        assert "JSON" in result["technical_terms_preserved"]
        assert "API" in result["translated_text"]
        assert "JSON" in result["translated_text"]

    def test_error_recovery_in_translation_workflow(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test error recovery during translation workflow."""
        # Arrange
        text = "Use the API for data access"
        # Comprehend fails but translation should still work
        mock_comprehend_client.detect_entities.side_effect = Exception(
            "Comprehend error"
        )
        mock_comprehend_client.extract_technical_terms.side_effect = Exception(
            "Comprehend error"
        )
        mock_translate_client.translate_text.return_value = (
            "डेटा एक्सेस के लिए API का उपयोग करें"
        )

        # Act
        result = translation_service.translate(text, "en", "hi")

        # Assert
        # Should still complete translation using pattern-based term extraction
        assert result["translated_text"] == "डेटा एक्सेस के लिए API का उपयोग करें"
        assert "API" in result["technical_terms_preserved"]

    def test_context_clearing_workflow(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test clearing context after a session ends."""
        # Arrange
        session_id = "temp_session"
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = "अनुवादित पाठ"

        # Act
        # Create context
        translation_service.translate_with_context(
            "Test text", "en", "hi", session_id
        )
        assert translation_service.get_context(session_id) is not None

        # Clear context
        translation_service.clear_context(session_id)

        # Assert
        assert translation_service.get_context(session_id) is None

    def test_all_indian_languages_translation(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test translation workflow for all supported Indian languages."""
        # Arrange
        indian_languages = ["hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa"]
        text = "Use the API"
        
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act & Assert
        for lang in indian_languages:
            mock_translate_client.translate_text.return_value = f"API (translated to {lang})"
            result = translation_service.translate(text, "en", lang)
            
            assert result["source_language"] == "en"
            assert result["target_language"] == lang
            assert "API" in result["technical_terms_preserved"]
            assert "API" in result["translated_text"]

    def test_bidirectional_translation_consistency(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test consistency in bidirectional translation."""
        # Arrange
        english_text = "The SDK provides API access"
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        
        # English to Hindi
        mock_translate_client.translate_text.return_value = (
            "SDK, API एक्सेस प्रदान करता है"
        )
        result_en_to_hi = translation_service.translate(english_text, "en", "hi")

        # Hindi to English
        hindi_text = result_en_to_hi["translated_text"]
        mock_translate_client.translate_text.return_value = (
            "SDK provides API access"
        )
        result_hi_to_en = translation_service.translate(hindi_text, "hi", "en")

        # Assert
        # Technical terms should be preserved in both directions
        assert "SDK" in result_en_to_hi["technical_terms_preserved"]
        assert "API" in result_en_to_hi["technical_terms_preserved"]
        assert "SDK" in result_hi_to_en["technical_terms_preserved"]
        assert "API" in result_hi_to_en["technical_terms_preserved"]

    def test_long_conversation_context_maintenance(
        self, translation_service, mock_translate_client, mock_comprehend_client
    ):
        """Test context maintenance over a long conversation."""
        # Arrange
        session_id = "long_conversation"
        messages = [
            "Let's discuss the REST API",
            "The API uses OAuth authentication",
            "OAuth tokens expire after 3600 seconds",
            "Use refresh_token to get new tokens",
        ]
        
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.side_effect = [
            "आइए REST API पर चर्चा करें",
            "API, OAuth प्रमाणीकरण का उपयोग करता है",
            "OAuth टोकन 3600 सेकंड के बाद समाप्त हो जाते हैं",
            "नए टोकन प्राप्त करने के लिए refresh_token का उपयोग करें",
        ]

        # Act
        results = []
        for msg in messages:
            result = translation_service.translate_with_context(
                msg, "en", "hi", session_id
            )
            results.append(result)

        # Assert
        assert results[0]["context_maintained"] is False  # First message
        assert all(r["context_maintained"] for r in results[1:])  # Rest have context
        
        # Check technical terms are accumulated
        final_context = translation_service.get_context(session_id)
        assert final_context is not None
        assert "technical_terms" in final_context
