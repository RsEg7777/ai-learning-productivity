"""Unit tests for language detection service."""

import pytest
from unittest.mock import Mock, patch
from src.services.multilingual.language_detector import LanguageDetector
from src.shared.utils.errors import LanguageDetectionError


class TestLanguageDetector:
    """Test suite for LanguageDetector."""

    @pytest.fixture
    def mock_comprehend_client(self):
        """Create a mock Comprehend client."""
        return Mock()

    @pytest.fixture
    def language_detector(self, mock_comprehend_client):
        """Create a LanguageDetector instance with mocked client."""
        return LanguageDetector(comprehend_client=mock_comprehend_client)

    def test_detect_language_english(self, language_detector, mock_comprehend_client):
        """Test detecting English language."""
        # Arrange
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "en",
            "Score": 0.99,
        }
        text = "This is a test in English"

        # Act
        result = language_detector.detect_language(text)

        # Assert
        assert result["language_code"] == "en"
        assert result["language_name"] == "English"
        assert result["confidence"] == 0.99
        assert result["is_supported"] is True
        assert result["is_indian_language"] is False
        mock_comprehend_client.detect_dominant_language.assert_called_once_with(text)

    def test_detect_language_hindi(self, language_detector, mock_comprehend_client):
        """Test detecting Hindi language."""
        # Arrange
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "hi",
            "Score": 0.95,
        }
        text = "यह हिंदी में एक परीक्षण है"

        # Act
        result = language_detector.detect_language(text)

        # Assert
        assert result["language_code"] == "hi"
        assert result["language_name"] == "Hindi"
        assert result["confidence"] == 0.95
        assert result["is_supported"] is True
        assert result["is_indian_language"] is True

    def test_detect_language_tamil(self, language_detector, mock_comprehend_client):
        """Test detecting Tamil language."""
        # Arrange
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "ta",
            "Score": 0.92,
        }
        text = "இது தமிழில் ஒரு சோதனை"

        # Act
        result = language_detector.detect_language(text)

        # Assert
        assert result["language_code"] == "ta"
        assert result["language_name"] == "Tamil"
        assert result["is_indian_language"] is True

    def test_detect_language_empty_text(self, language_detector):
        """Test detecting language with empty text."""
        # Act & Assert
        with pytest.raises(LanguageDetectionError, match="Text cannot be empty"):
            language_detector.detect_language("")

    def test_detect_language_whitespace_only(self, language_detector):
        """Test detecting language with whitespace only."""
        # Act & Assert
        with pytest.raises(LanguageDetectionError, match="Text cannot be empty"):
            language_detector.detect_language("   \n\t  ")

    def test_detect_language_unsupported(self, language_detector, mock_comprehend_client):
        """Test detecting unsupported language."""
        # Arrange
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "fr",
            "Score": 0.88,
        }
        text = "Ceci est un test en français"

        # Act
        result = language_detector.detect_language(text)

        # Assert
        assert result["language_code"] == "fr"
        assert result["language_name"] == "Unknown (fr)"
        assert result["is_supported"] is False
        assert result["is_indian_language"] is False

    def test_detect_language_no_languages_returned(
        self, language_detector, mock_comprehend_client
    ):
        """Test when Comprehend returns no languages."""
        # Arrange
        mock_comprehend_client.detect_dominant_language.return_value = {
            "Languages": []
        }
        text = "Some text"

        # Act
        result = language_detector.detect_language(text)

        # Assert
        assert result["language_code"] == "en"
        assert result["confidence"] == 0.0

    def test_detect_language_client_error(self, language_detector, mock_comprehend_client):
        """Test handling of Comprehend client errors."""
        # Arrange
        from botocore.exceptions import ClientError

        mock_comprehend_client.detect_dominant_language.side_effect = ClientError(
            {"Error": {"Code": "ServiceError", "Message": "Service unavailable"}},
            "detect_dominant_language",
        )
        text = "Some text"

        # Act & Assert
        with pytest.raises(LanguageDetectionError):
            language_detector.detect_language(text)

    def test_detect_languages_batch(self, language_detector, mock_comprehend_client):
        """Test batch language detection."""
        # Arrange
        mock_comprehend_client.detect_dominant_language.side_effect = [
            {"LanguageCode": "en", "Score": 0.99},
            {"LanguageCode": "hi", "Score": 0.95},
            {"LanguageCode": "ta", "Score": 0.92},
        ]
        texts = [
            "English text",
            "हिंदी पाठ",
            "தமிழ் உரை",
        ]

        # Act
        results = language_detector.detect_languages_batch(texts)

        # Assert
        assert len(results) == 3
        assert results[0]["language_code"] == "en"
        assert results[1]["language_code"] == "hi"
        assert results[2]["language_code"] == "ta"

    def test_detect_languages_batch_with_error(
        self, language_detector, mock_comprehend_client
    ):
        """Test batch detection with one failing."""
        # Arrange
        mock_comprehend_client.detect_dominant_language.side_effect = [
            {"LanguageCode": "en", "Score": 0.99},
            LanguageDetectionError("Detection failed"),
            {"LanguageCode": "ta", "Score": 0.92},
        ]
        texts = ["English text", "Problem text", "தமிழ் உரை"]

        # Act
        results = language_detector.detect_languages_batch(texts)

        # Assert
        assert len(results) == 3
        assert results[0]["language_code"] == "en"
        assert results[1]["language_code"] == "en"  # Default fallback
        assert results[1]["confidence"] == 0.0
        assert "error" in results[1]
        assert results[2]["language_code"] == "ta"

    def test_is_supported_language(self, language_detector):
        """Test checking if language is supported."""
        assert language_detector.is_supported_language("en") is True
        assert language_detector.is_supported_language("hi") is True
        assert language_detector.is_supported_language("ta") is True
        assert language_detector.is_supported_language("fr") is False
        assert language_detector.is_supported_language("de") is False

    def test_is_indian_language(self, language_detector):
        """Test checking if language is Indian."""
        assert language_detector.is_indian_language("hi") is True
        assert language_detector.is_indian_language("ta") is True
        assert language_detector.is_indian_language("te") is True
        assert language_detector.is_indian_language("bn") is True
        assert language_detector.is_indian_language("en") is False
        assert language_detector.is_indian_language("fr") is False

    def test_get_supported_languages(self, language_detector):
        """Test getting all supported languages."""
        languages = language_detector.get_supported_languages()
        
        assert "en" in languages
        assert "hi" in languages
        assert "ta" in languages
        assert "te" in languages
        assert "bn" in languages
        assert "mr" in languages
        assert "gu" in languages
        assert "kn" in languages
        assert "ml" in languages
        assert "pa" in languages
        assert "or" in languages
        assert len(languages) == 11  # English + 10 Indian languages

    def test_get_indian_languages(self, language_detector):
        """Test getting Indian languages only."""
        languages = language_detector.get_indian_languages()
        
        assert "hi" in languages
        assert "ta" in languages
        assert "te" in languages
        assert "en" not in languages
        assert len(languages) == 10

    def test_validate_language_code_valid(self, language_detector):
        """Test validating a supported language code."""
        # Should not raise any exception
        language_detector.validate_language_code("en")
        language_detector.validate_language_code("hi")
        language_detector.validate_language_code("ta")

    def test_validate_language_code_invalid(self, language_detector):
        """Test validating an unsupported language code."""
        with pytest.raises(
            LanguageDetectionError, match="Language 'fr' is not supported"
        ):
            language_detector.validate_language_code("fr")

    def test_all_indian_languages_supported(self, language_detector):
        """Test that all required Indian languages are supported."""
        required_languages = ["hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa", "or"]
        
        for lang in required_languages:
            assert language_detector.is_supported_language(lang)
            assert language_detector.is_indian_language(lang)
