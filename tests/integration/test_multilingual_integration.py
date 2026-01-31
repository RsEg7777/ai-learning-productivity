"""Integration tests for multilingual support system."""

import pytest
from unittest.mock import Mock, patch
from src.services.multilingual.multilingual_service import MultilingualService


class TestMultilingualIntegration:
    """Integration tests for the complete multilingual workflow."""

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
        """Create a MultilingualService instance."""
        return MultilingualService(
            comprehend_client=mock_comprehend_client,
            translate_client=mock_translate_client,
        )

    def test_complete_workflow_english_content(
        self, multilingual_service, mock_comprehend_client
    ):
        """Test complete workflow with English content."""
        # Arrange
        text = "Machine learning is a powerful technology for data analysis."
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "en",
            "Score": 0.99,
        }
        mock_comprehend_client.extract_key_phrases.return_value = [
            "Machine learning",
            "powerful technology",
            "data analysis",
        ]
        mock_comprehend_client.detect_entities.return_value = [
            {"Text": "Machine learning", "Type": "TITLE", "Score": 0.95}
        ]
        mock_comprehend_client.extract_technical_terms.return_value = [
            "Machine learning",
            "data analysis",
        ]

        # Act
        result = multilingual_service.detect_and_process(text)

        # Assert
        assert result["detection"]["language_code"] == "en"
        assert result["detection"]["is_supported"] is True
        assert result["processing"]["language_code"] == "en"
        assert len(result["processing"]["key_phrases"]) == 3
        assert len(result["processing"]["technical_terms"]) == 2
        assert result["translation"] is None

    def test_complete_workflow_hindi_to_english(
        self, multilingual_service, mock_comprehend_client, mock_translate_client
    ):
        """Test complete workflow with Hindi content translated to English."""
        # Arrange
        hindi_text = "मशीन लर्निंग डेटा विश्लेषण के लिए एक शक्तिशाली तकनीक है"
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "hi",
            "Score": 0.95,
        }
        mock_comprehend_client.extract_key_phrases.return_value = [
            "मशीन लर्निंग",
            "डेटा विश्लेषण",
        ]
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = [
            "मशीन लर्निंग"
        ]
        mock_translate_client.translate_with_terminology.return_value = (
            "Machine learning is a powerful technology for data analysis"
        )

        # Act
        result = multilingual_service.detect_and_process(
            hindi_text, target_language="en"
        )

        # Assert
        assert result["detection"]["language_code"] == "hi"
        assert result["detection"]["is_indian_language"] is True
        assert result["processing"]["language_code"] == "hi"
        assert result["translation"] is not None
        assert result["translation"]["source_language"] == "hi"
        assert result["translation"]["target_language"] == "en"
        assert "Machine learning" in result["translation"]["translated_text"]

    def test_user_input_handling_indian_language(
        self, multilingual_service, mock_comprehend_client
    ):
        """Test handling user input in Indian language - should respond in same language."""
        # Arrange
        tamil_text = "இயந்திர கற்றல் என்றால் என்ன?"
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "ta",
            "Score": 0.93,
        }
        mock_comprehend_client.extract_key_phrases.return_value = ["இயந்திர கற்றல்"]
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        result = multilingual_service.handle_user_input(tamil_text)

        # Assert
        assert result["detected_language"]["language_code"] == "ta"
        assert result["detected_language"]["is_indian_language"] is True
        assert result["response_language"] == "ta"  # Should respond in Tamil
        assert result["should_translate"] is False

    def test_language_context_switching(
        self, multilingual_service, mock_comprehend_client
    ):
        """Test maintaining context when user switches languages."""
        # Arrange - User switches from English to Hindi
        hindi_text = "अब हिंदी में बात करते हैं"
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "hi",
            "Score": 0.96,
        }

        # Act
        result = multilingual_service.maintain_language_context(
            hindi_text, previous_language="en"
        )

        # Assert
        assert result["current_language"]["language_code"] == "hi"
        assert result["previous_language"] == "en"
        assert result["language_switched"] is True
        assert result["context_maintained"] is True
        assert "switch_message" in result

    def test_multilingual_batch_processing(
        self, multilingual_service, mock_comprehend_client
    ):
        """Test processing multiple texts in different languages."""
        # Arrange
        texts = [
            "English text about AI",
            "हिंदी में पाठ",
            "தமிழ் உரை",
        ]
        
        mock_comprehend_client.detect_dominant_language.side_effect = [
            {"LanguageCode": "en", "Score": 0.99},
            {"LanguageCode": "hi", "Score": 0.95},
            {"LanguageCode": "ta", "Score": 0.93},
        ]
        mock_comprehend_client.extract_key_phrases.return_value = []
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        results = []
        for text in texts:
            result = multilingual_service.detect_and_process(text)
            results.append(result)

        # Assert
        assert len(results) == 3
        assert results[0]["detection"]["language_code"] == "en"
        assert results[1]["detection"]["language_code"] == "hi"
        assert results[2]["detection"]["language_code"] == "ta"
        assert results[1]["detection"]["is_indian_language"] is True
        assert results[2]["detection"]["is_indian_language"] is True

    def test_technical_term_preservation_across_translation(
        self, multilingual_service, mock_comprehend_client, mock_translate_client
    ):
        """Test that technical terms are preserved during translation."""
        # Arrange
        text = "API और SDK का उपयोग करके application बनाएं"
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "hi",
            "Score": 0.94,
        }
        mock_comprehend_client.extract_key_phrases.return_value = []
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = [
            "API",
            "SDK",
            "application",
        ]
        mock_translate_client.translate_with_terminology.return_value = (
            "Build application using API and SDK"
        )

        # Act
        result = multilingual_service.detect_and_process(text, target_language="en")

        # Assert
        assert result["translation"] is not None
        assert "API" in result["translation"]["technical_terms_preserved"]
        assert "SDK" in result["translation"]["technical_terms_preserved"]
        assert "application" in result["translation"]["technical_terms_preserved"]

    def test_all_indian_languages_workflow(
        self, multilingual_service, mock_comprehend_client
    ):
        """Test that all required Indian languages work in the workflow."""
        # Arrange
        indian_languages = ["hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa", "or"]
        
        mock_comprehend_client.extract_key_phrases.return_value = []
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act & Assert
        for lang_code in indian_languages:
            mock_comprehend_client.detect_dominant_language.return_value = {
                "LanguageCode": lang_code,
                "Score": 0.90,
            }
            
            result = multilingual_service.detect_and_process(f"Test text in {lang_code}")
            
            assert result["detection"]["language_code"] == lang_code
            assert result["detection"]["is_indian_language"] is True
            assert result["detection"]["is_supported"] is True

    def test_language_support_validation(self, multilingual_service):
        """Test language support validation."""
        # Act
        supported_info = multilingual_service.get_supported_languages()

        # Assert
        assert supported_info["total_count"] == 11  # English + 10 Indian languages
        assert supported_info["indian_count"] == 10
        assert "en" in supported_info["all_languages"]
        
        # Verify all required Indian languages
        required_indian = ["hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa", "or"]
        for lang in required_indian:
            assert lang in supported_info["indian_languages"]

    def test_error_handling_in_workflow(
        self, multilingual_service, mock_comprehend_client
    ):
        """Test error handling in the complete workflow."""
        # Arrange
        text = "Test text"
        mock_comprehend_client.detect_dominant_language.return_value = {
            "LanguageCode": "en",
            "Score": 0.99,
        }
        # Simulate partial failures
        mock_comprehend_client.extract_key_phrases.side_effect = Exception("Error")
        mock_comprehend_client.detect_entities.return_value = []
        mock_comprehend_client.extract_technical_terms.return_value = []

        # Act
        result = multilingual_service.detect_and_process(text)

        # Assert - should still complete despite errors
        assert result["detection"]["language_code"] == "en"
        assert result["processing"]["language_code"] == "en"
        assert result["processing"]["key_phrases"] == []  # Empty due to error
