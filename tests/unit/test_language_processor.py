"""Unit tests for language processor service."""

import pytest
from unittest.mock import Mock
from src.services.multilingual.language_processor import LanguageProcessor
from src.shared.utils.errors import LanguageProcessingError


class TestLanguageProcessor:
    """Test suite for LanguageProcessor."""

    @pytest.fixture
    def mock_comprehend_client(self):
        """Create a mock Comprehend client."""
        return Mock()

    @pytest.fixture
    def mock_translate_client(self):
        """Create a mock Translate client."""
        return Mock()

    @pytest.fixture
    def language_processor(self, mock_comprehend_client, mock_translate_client):
        """Create a LanguageProcessor instance with mocked clients."""
        return LanguageProcessor(
            comprehend_client=mock_comprehend_client,
            translate_client=mock_translate_client,
        )

    def test_process_content_english(
        self, language_processor, mock_comprehend_client
    ):
        """Test processing English content."""
        # Arrange
        text = "Machine learning is a subset of artificial intelligence."
        mock_comprehend_client.extract_key_phrases.return_value = [
            "Machine learning",
            "artificial intelligence",
        ]
        mock_comprehend_client.detect_entities.return_value = [
            {"Text": "Machine learning", "Type": "TITLE", "Score": 0.95}
        ]
        mock_comprehend_client.extract_technical_terms.return_value = [
            "Machine learning",
            "artificial intelligence",
        ]

        # Act
        result = language_processor.process_content(text, "en")

        # Assert
        assert result["processed_text"] == text
        assert result["language_code"] == "en"
        assert len(result["key_phrases"]) == 2
        assert len(result["entities"]) == 1
        assert len(result["technical_terms"]) == 2

    def test_process_content_hindi(
        self, language_processor, mock_comprehend_client
    ):
        """Test processing Hindi content."""
        # Arrange
        text = "मशीन लर्निंग कृत्रिम बुद्धिमत्ता का एक उपसमुच्चय है"
        mock_comprehend_client.extract_key_phrases.return_value = ["मशीन लर्निंग"]
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        result = language_processor.process_content(text, "hi")

        # Assert
        assert result["processed_text"] == text
        assert result["language_code"] == "hi"
        assert len(result["key_phrases"]) == 1

    def test_process_content_empty_text(self, language_processor):
        """Test processing empty text."""
        with pytest.raises(LanguageProcessingError, match="Text cannot be empty"):
            language_processor.process_content("", "en")

    def test_process_content_without_technical_terms(
        self, language_processor, mock_comprehend_client
    ):
        """Test processing without technical term preservation."""
        # Arrange
        text = "This is a simple test."
        mock_comprehend_client.extract_key_phrases.return_value = ["simple test"]
        mock_comprehend_client.detect_entities.return_value = []

        # Act
        result = language_processor.process_content(
            text, "en", preserve_technical_terms=False
        )

        # Assert
        assert result["technical_terms"] == []
        mock_comprehend_client.extract_technical_terms.assert_not_called()

    def test_process_content_comprehend_error(
        self, language_processor, mock_comprehend_client
    ):
        """Test handling Comprehend errors gracefully."""
        # Arrange
        text = "Test text"
        mock_comprehend_client.extract_key_phrases.side_effect = Exception(
            "Service error"
        )
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        result = language_processor.process_content(text, "en")

        # Assert - should continue despite error
        assert result["processed_text"] == text
        assert result["key_phrases"] == []

    def test_translate_content_english_to_hindi(
        self, language_processor, mock_comprehend_client, mock_translate_client
    ):
        """Test translating from English to Hindi."""
        # Arrange
        text = "Machine learning is powerful"
        mock_comprehend_client.extract_technical_terms.return_value = [
            "Machine learning"
        ]
        mock_translate_client.translate_with_terminology.return_value = (
            "Machine learning शक्तिशाली है"
        )

        # Act
        result = language_processor.translate_content(text, "en", "hi")

        # Assert
        assert result["translated_text"] == "Machine learning शक्तिशाली है"
        assert result["source_language"] == "en"
        assert result["target_language"] == "hi"
        assert "Machine learning" in result["technical_terms_preserved"]

    def test_translate_content_same_language(self, language_processor):
        """Test translation when source and target are the same."""
        # Arrange
        text = "Test text"

        # Act
        result = language_processor.translate_content(text, "en", "en")

        # Assert
        assert result["translated_text"] == text
        assert result["source_language"] == "en"
        assert result["target_language"] == "en"
        assert result["technical_terms_preserved"] == []

    def test_translate_content_without_technical_terms(
        self, language_processor, mock_comprehend_client, mock_translate_client
    ):
        """Test translation without technical term preservation."""
        # Arrange
        text = "Simple text"
        mock_translate_client.translate_text.return_value = "सरल पाठ"

        # Act
        result = language_processor.translate_content(
            text, "en", "hi", preserve_technical_terms=False
        )

        # Assert
        assert result["translated_text"] == "सरल पाठ"
        assert result["technical_terms_preserved"] == []
        mock_translate_client.translate_text.assert_called_once()

    def test_translate_content_empty_text(self, language_processor):
        """Test translating empty text."""
        with pytest.raises(LanguageProcessingError, match="Text cannot be empty"):
            language_processor.translate_content("", "en", "hi")

    def test_process_multilingual_content_no_translation(
        self, language_processor, mock_comprehend_client
    ):
        """Test processing multilingual content without translation."""
        # Arrange
        text = "English text"
        mock_comprehend_client.extract_key_phrases.return_value = ["English text"]
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        result = language_processor.process_multilingual_content(
            text, "en", target_language="en"
        )

        # Assert
        assert result["original_text"] == text
        assert result["processed_text"] == text
        assert result["original_language"] == "en"
        assert result["processing_language"] == "en"
        assert result["was_translated"] is False

    def test_process_multilingual_content_with_translation(
        self, language_processor, mock_comprehend_client, mock_translate_client
    ):
        """Test processing multilingual content with translation."""
        # Arrange
        text = "हिंदी पाठ"
        mock_comprehend_client.extract_key_phrases.return_value = ["पाठ"]
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []
        mock_translate_client.translate_text.return_value = "Hindi text"

        # Act
        result = language_processor.process_multilingual_content(
            text, "hi", target_language="en"
        )

        # Assert
        assert result["original_text"] == text
        assert result["processed_text"] == "Hindi text"
        assert result["original_language"] == "hi"
        assert result["processing_language"] == "en"
        assert result["was_translated"] is True

    def test_extract_context_for_translation(
        self, language_processor, mock_comprehend_client
    ):
        """Test extracting context for translation."""
        # Arrange
        text = "This is a positive message about AI"
        mock_comprehend_client.analyze_sentiment.return_value = {
            "Sentiment": "POSITIVE",
            "Scores": {"Positive": 0.95},
        }
        mock_comprehend_client.detect_entities.return_value = [
            {"Text": "AI", "Type": "TITLE"}
        ]
        mock_comprehend_client.extract_key_phrases.return_value = [
            "positive message",
            "AI",
        ]

        # Act
        result = language_processor.extract_context_for_translation(text, "en")

        # Assert
        assert result["language_code"] == "en"
        assert result["sentiment"]["Sentiment"] == "POSITIVE"
        assert len(result["entities"]) == 1
        assert len(result["key_phrases"]) == 2

    def test_extract_context_with_errors(
        self, language_processor, mock_comprehend_client
    ):
        """Test context extraction with partial failures."""
        # Arrange
        text = "Test text"
        mock_comprehend_client.analyze_sentiment.side_effect = Exception("Error")
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_key_phrases.return_value = []

        # Act
        result = language_processor.extract_context_for_translation(text, "en")

        # Assert - should continue despite errors
        assert result["language_code"] == "en"
        assert result["sentiment"] is None
        assert result["entities"] == []

    def test_batch_process_content(
        self, language_processor, mock_comprehend_client
    ):
        """Test batch processing of multiple texts."""
        # Arrange
        texts = ["Text one", "Text two", "Text three"]
        mock_comprehend_client.extract_key_phrases.return_value = ["key phrase"]
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        results = language_processor.batch_process_content(texts, "en")

        # Assert
        assert len(results) == 3
        for result in results:
            assert result["language_code"] == "en"
            assert "processed_text" in result

    def test_batch_process_content_with_error(
        self, language_processor, mock_comprehend_client
    ):
        """Test batch processing with graceful error handling."""
        # Arrange
        texts = ["Text one", "Text two"]
        
        # First call succeeds, second fails but is handled gracefully
        mock_comprehend_client.extract_key_phrases.side_effect = [
            ["key phrase"],
            Exception("Error"),  # This will be caught and logged as warning
        ]
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        results = language_processor.batch_process_content(texts, "en")

        # Assert
        assert len(results) == 2
        # First result should be successful
        assert results[0]["processed_text"] == "Text one"
        assert results[0]["key_phrases"] == ["key phrase"]
        # Second result should have empty key_phrases due to error, but still process
        assert results[1]["processed_text"] == "Text two"
        assert results[1]["key_phrases"] == []  # Error was handled gracefully
