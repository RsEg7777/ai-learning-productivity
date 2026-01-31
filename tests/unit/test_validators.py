"""Unit tests for validators."""

import pytest
from src.shared.utils.validators import (
    validate_content_type,
    validate_language_code,
    validate_file_size,
    validate_email,
    validate_password,
    validate_text_length,
)
from src.shared.utils.errors import ValidationError, UnsupportedFormatError
from src.shared.models.content import ContentType


class TestContentTypeValidation:
    """Test content type validation."""

    def test_valid_text_extension(self):
        """Test valid text file extension."""
        content_type = validate_content_type(".txt")
        assert content_type == ContentType.TEXT

    def test_valid_pdf_extension(self):
        """Test valid PDF file extension."""
        content_type = validate_content_type(".pdf")
        assert content_type == ContentType.PDF

    def test_valid_video_extension(self):
        """Test valid video file extension."""
        content_type = validate_content_type(".mp4")
        assert content_type == ContentType.VIDEO

    def test_unsupported_extension(self):
        """Test unsupported file extension."""
        with pytest.raises(UnsupportedFormatError) as exc_info:
            validate_content_type(".xyz")
        assert "Unsupported file format" in str(exc_info.value)


class TestLanguageCodeValidation:
    """Test language code validation."""

    def test_valid_english_code(self):
        """Test valid English language code."""
        lang = validate_language_code("en")
        assert lang == "en"

    def test_valid_hindi_code(self):
        """Test valid Hindi language code."""
        lang = validate_language_code("hi-IN")
        assert lang == "hi-IN"

    def test_invalid_language_code(self):
        """Test invalid language code."""
        with pytest.raises(ValidationError) as exc_info:
            validate_language_code("xyz")
        assert "Unsupported language code" in str(exc_info.value)


class TestFileSizeValidation:
    """Test file size validation."""

    def test_valid_text_file_size(self):
        """Test valid text file size."""
        # 5 MB - should pass
        validate_file_size(5 * 1024 * 1024, ContentType.TEXT)

    def test_oversized_text_file(self):
        """Test oversized text file."""
        # 15 MB - should fail (limit is 10 MB)
        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(15 * 1024 * 1024, ContentType.TEXT)
        assert "exceeds limit" in str(exc_info.value)


class TestEmailValidation:
    """Test email validation."""

    def test_valid_email(self):
        """Test valid email address."""
        email = validate_email("test@example.com")
        assert email == "test@example.com"

    def test_invalid_email_format(self):
        """Test invalid email format."""
        with pytest.raises(ValidationError):
            validate_email("invalid-email")

    def test_email_lowercase_conversion(self):
        """Test email is converted to lowercase."""
        email = validate_email("Test@Example.COM")
        assert email == "test@example.com"


class TestPasswordValidation:
    """Test password validation."""

    def test_valid_password(self):
        """Test valid password."""
        validate_password("Test1234")  # Should not raise

    def test_short_password(self):
        """Test password too short."""
        with pytest.raises(ValidationError) as exc_info:
            validate_password("Test12")
        assert "at least 8 characters" in str(exc_info.value)

    def test_password_missing_uppercase(self):
        """Test password missing uppercase letter."""
        with pytest.raises(ValidationError) as exc_info:
            validate_password("test1234")
        assert "uppercase letter" in str(exc_info.value)

    def test_password_missing_lowercase(self):
        """Test password missing lowercase letter."""
        with pytest.raises(ValidationError) as exc_info:
            validate_password("TEST1234")
        assert "lowercase letter" in str(exc_info.value)

    def test_password_missing_digit(self):
        """Test password missing digit."""
        with pytest.raises(ValidationError) as exc_info:
            validate_password("TestTest")
        assert "digit" in str(exc_info.value)


class TestTextLengthValidation:
    """Test text length validation."""

    def test_valid_text_length(self):
        """Test valid text length."""
        validate_text_length("Hello", min_length=3, max_length=10)

    def test_text_too_short(self):
        """Test text too short."""
        with pytest.raises(ValidationError) as exc_info:
            validate_text_length("Hi", min_length=5)
        assert "at least 5 characters" in str(exc_info.value)

    def test_text_too_long(self):
        """Test text too long."""
        with pytest.raises(ValidationError) as exc_info:
            validate_text_length("Hello World", max_length=5)
        assert "must not exceed 5 characters" in str(exc_info.value)
