"""Unit tests for multilingual service."""

import pytest
from unittest.mock import Mock, patch
from src.services.multilingual.multilingual_service import MultilingualService
from src.shared.utils.errors import LanguageDetectionError, LanguageProcessingError


class TestMultilingualService:
    """Test suite for MultilingualService."""

    @pytest.fixture
    def mock_comprehend_client(self):
        """Create a mock Comprehend client."""
        return Mock()

    @pytest.fixture
    def mock_translate_client(self):
        """Create a mock Translate client."""
        return Mock()

    @pytest.fixture
    def multilingual_service(self, mock_comprehend_client, mock_translate_client):
        """Create a MultilingualService instance with mocked clients."""
        return MultilingualService(
            comprehend_client=mock_comprehend_client,
            translate_client=mock_translate_client,
        )

    def test_detect_and_process_english(
        self, multilingual_service, mock_comprehend_client
    ):
        """Test detecting and processing English content."""
        # Arrange
        text = "This is English text"
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "en",
            "Score": 0.99,
        }
        mock_comprehend_client.extract_key_phrases.return_value = ["English text"]
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        result = multilingual_service.detect_and_process(text)

        # Assert
        assert result["detection"]["language_code"] == "en"
        assert result["processing"]["language_code"] == "en"
        assert result["translation"] is None

    def test_detect_and_process_with_translation(
        self, multilingual_service, mock_comprehend_client, mock_translate_client
    ):
        """Test detecting and processing with translation."""
        # Arrange
        text = "हिंदी पाठ"
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "hi",
            "Score": 0.95,
        }
        mock_comprehend_client.extract_key_phrases.return_value = []
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = "Hindi text"

        # Act
        result = multilingual_service.detect_and_process(text, target_language="en")

        # Assert
        assert result["detection"]["language_code"] == "hi"
        assert result["processing"]["language_code"] == "hi"
        assert result["translation"] is not None
        assert result["translation"]["translated_text"] == "Hindi text"

    def test_detect_and_process_empty_text(self, multilingual_service):
        """Test with empty text."""
        with pytest.raises(LanguageProcessingError, match="Text cannot be empty"):
            multilingual_service.detect_and_process("")

    def test_process_in_same_language(
        self, multilingual_service, mock_comprehend_client
    ):
        """Test processing content in the same language."""
        # Arrange
        text = "Test text"
        mock_comprehend_client.extract_key_phrases.return_value = ["Test text"]
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        result = multilingual_service.process_in_same_language(text, "en")

        # Assert
        assert result["language_code"] == "en"
        assert result["processed_text"] == text

    def test_process_in_same_language_unsupported(self, multilingual_service):
        """Test processing with unsupported language."""
        with pytest.raises(LanguageDetectionError, match="not supported"):
            multilingual_service.process_in_same_language("Test", "fr")

    def test_translate_between_languages(
        self, multilingual_service, mock_comprehend_client, mock_translate_client
    ):
        """Test translating between two languages."""
        # Arrange
        text = "English text"
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = "हिंदी पाठ"

        # Act
        result = multilingual_service.translate_between_languages(text, "en", "hi")

        # Assert
        assert result["translated_text"] == "हिंदी पाठ"
        assert result["source_language"] == "en"
        assert result["target_language"] == "hi"

    def test_translate_between_languages_unsupported_source(
        self, multilingual_service
    ):
        """Test translation with unsupported source language."""
        with pytest.raises(LanguageDetectionError, match="not supported"):
            multilingual_service.translate_between_languages("Test", "fr", "en")

    def test_translate_between_languages_unsupported_target(
        self, multilingual_service
    ):
        """Test translation with unsupported target language."""
        with pytest.raises(LanguageDetectionError, match="not supported"):
            multilingual_service.translate_between_languages("Test", "en", "fr")

    def test_handle_user_input_english(
        self, multilingual_service, mock_comprehend_client
    ):
        """Test handling English user input."""
        # Arrange
        text = "English input"
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "en",
            "Score": 0.99,
        }
        mock_comprehend_client.extract_key_phrases.return_value = []
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        result = multilingual_service.handle_user_input(text)

        # Assert
        assert result["detected_language"]["language_code"] == "en"
        assert result["response_language"] == "en"
        assert result["should_translate"] is False

    def test_handle_user_input_indian_language(
        self, multilingual_service, mock_comprehend_client
    ):
        """Test handling Indian language input - should respond in same language."""
        # Arrange
        text = "हिंदी इनपुट"
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "hi",
            "Score": 0.95,
        }
        mock_comprehend_client.extract_key_phrases.return_value = []
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        result = multilingual_service.handle_user_input(text)

        # Assert
        assert result["detected_language"]["language_code"] == "hi"
        assert result["response_language"] == "hi"
        assert result["detected_language"]["is_indian_language"] is True

    def test_handle_user_input_with_preferred_language(
        self, multilingual_service, mock_comprehend_client
    ):
        """Test handling input with user's preferred language."""
        # Arrange
        text = "English input"
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "en",
            "Score": 0.99,
        }
        mock_comprehend_client.extract_key_phrases.return_value = []
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        result = multilingual_service.handle_user_input(
            text, user_preferred_language="hi"
        )

        # Assert
        assert result["detected_language"]["language_code"] == "en"
        assert result["response_language"] == "hi"
        assert result["should_translate"] is True

    def test_maintain_language_context_no_switch(
        self, multilingual_service, mock_comprehend_client
    ):
        """Test maintaining context when language doesn't change."""
        # Arrange
        text = "English text"
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "en",
            "Score": 0.99,
        }

        # Act
        result = multilingual_service.maintain_language_context(text, "en")

        # Assert
        assert result["current_language"]["language_code"] == "en"
        assert result["previous_language"] == "en"
        assert result["language_switched"] is False
        assert result["context_maintained"] is True

    def test_maintain_language_context_with_switch(
        self, multilingual_service, mock_comprehend_client
    ):
        """Test maintaining context when language switches."""
        # Arrange
        text = "हिंदी पाठ"
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "hi",
            "Score": 0.95,
        }

        # Act
        result = multilingual_service.maintain_language_context(text, "en")

        # Assert
        assert result["current_language"]["language_code"] == "hi"
        assert result["previous_language"] == "en"
        assert result["language_switched"] is True
        assert "switch_message" in result

    def test_get_supported_languages(self, multilingual_service):
        """Test getting supported languages information."""
        # Act
        result = multilingual_service.get_supported_languages()

        # Assert
        assert "all_languages" in result
        assert "indian_languages" in result
        assert result["total_count"] == 11  # English + 10 Indian languages
        assert result["indian_count"] == 10
        assert "en" in result["all_languages"]
        assert "hi" in result["indian_languages"]

    def test_validate_language_support_supported(self, multilingual_service):
        """Test validating a supported language."""
        # Act
        result = multilingual_service.validate_language_support("hi")

        # Assert
        assert result["language_code"] == "hi"
        assert result["language_name"] == "Hindi"
        assert result["is_supported"] is True
        assert result["is_indian_language"] is True

    def test_validate_language_support_unsupported(self, multilingual_service):
        """Test validating an unsupported language."""
        # Act
        result = multilingual_service.validate_language_support("fr")

        # Assert
        assert result["language_code"] == "fr"
        assert result["language_name"] == "Unknown"
        assert result["is_supported"] is False
        assert result["is_indian_language"] is False

    def test_all_indian_languages_in_service(self, multilingual_service):
        """Test that all required Indian languages are available."""
        # Arrange
        required_languages = {
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

        # Act
        supported = multilingual_service.get_supported_languages()

        # Assert
        for code, name in required_languages.items():
            assert code in supported["indian_languages"]
            assert supported["indian_languages"][code] == name
