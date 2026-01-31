"""Input validation utilities."""

import logging
from typing import List, Optional, Tuple, Dict, Any
from ..models.content import ContentType
from .errors import ValidationError, UnsupportedFormatError

logger = logging.getLogger(__name__)


# Supported content types and their extensions
SUPPORTED_FORMATS = {
    ContentType.TEXT: [".txt", ".md", ".markdown"],
    ContentType.PDF: [".pdf"],
    ContentType.VIDEO: [".mp4", ".avi", ".mov", ".mkv", ".webm"],
    ContentType.AUDIO: [".mp3", ".wav", ".m4a", ".flac", ".ogg"],
    ContentType.CODE: [
        ".py",
        ".js",
        ".ts",
        ".java",
        ".cpp",
        ".c",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".rb",
    ],
}

# Supported language codes
SUPPORTED_LANGUAGES = {
    # English
    "en",
    "en-US",
    "en-GB",
    # Indian languages
    "hi",
    "hi-IN",  # Hindi
    "ta",
    "ta-IN",  # Tamil
    "te",
    "te-IN",  # Telugu
    "bn",
    "bn-IN",  # Bengali
    "mr",
    "mr-IN",  # Marathi
    "gu",
    "gu-IN",  # Gujarati
    "kn",
    "kn-IN",  # Kannada
    "ml",
    "ml-IN",  # Malayalam
    "pa",
    "pa-IN",  # Punjabi
    "or",
    "or-IN",  # Odia
    # Other common languages
    "es",
    "fr",
    "de",
    "zh",
    "ja",
    "ko",
}

# File size limits (in bytes)
MAX_FILE_SIZES = {
    ContentType.TEXT: 10 * 1024 * 1024,  # 10 MB
    ContentType.PDF: 50 * 1024 * 1024,  # 50 MB
    ContentType.VIDEO: 500 * 1024 * 1024,  # 500 MB
    ContentType.AUDIO: 100 * 1024 * 1024,  # 100 MB
    ContentType.CODE: 1 * 1024 * 1024,  # 1 MB
}


def validate_content_type(file_extension: str) -> ContentType:
    """
    Validate and determine content type from file extension.

    Args:
        file_extension: File extension (e.g., '.pdf', '.mp4')

    Returns:
        ContentType enum value

    Raises:
        UnsupportedFormatError: If format is not supported
    """
    file_extension = file_extension.lower()

    for content_type, extensions in SUPPORTED_FORMATS.items():
        if file_extension in extensions:
            return content_type

    # Collect all supported extensions for error message
    all_extensions = []
    for extensions in SUPPORTED_FORMATS.values():
        all_extensions.extend(extensions)

    # Generate format suggestions based on similarity
    suggestions = _suggest_similar_formats(file_extension, all_extensions)

    raise UnsupportedFormatError(
        format_provided=file_extension,
        supported_formats=all_extensions,
        suggestions=suggestions,
    )


def _suggest_similar_formats(provided_format: str, supported_formats: List[str]) -> List[str]:
    """
    Suggest similar formats based on the provided format.

    Uses simple heuristics to find potentially similar formats:
    - Same starting letter
    - Similar length
    - Common file type patterns

    Args:
        provided_format: The format that was provided
        supported_formats: List of supported formats

    Returns:
        List of suggested formats (up to 3)
    """
    suggestions = []
    provided_lower = provided_format.lower().lstrip('.')
    
    # Common format mappings
    format_mappings = {
        'mpeg': ['.mp4', '.mp3'],
        'mpg': ['.mp4', '.mp3'],
        'mpeg4': ['.mp4'],
        'mp4v': ['.mp4'],
        'h264': ['.mp4'],
        'aac': ['.m4a', '.mp3'],
        'wave': ['.wav'],
        'jpeg': ['.jpg'],
        'jpg': ['.jpg'],
        'png': ['.png'],
        'gif': ['.gif'],
        'doc': ['.txt', '.pdf'],
        'docx': ['.txt', '.pdf'],
        'odt': ['.txt', '.pdf'],
        'rtf': ['.txt'],
        'tex': ['.txt'],
        'mpeg-4': ['.mp4'],
        'quicktime': ['.mov'],
        'qt': ['.mov'],
        'x-msvideo': ['.avi'],
        'x-matroska': ['.mkv'],
        'webm': ['.webm'],
        'ogg': ['.ogg'],
        'flac': ['.flac'],
        'python': ['.py'],
        'javascript': ['.js'],
        'typescript': ['.ts'],
        'java': ['.java'],
        'c++': ['.cpp'],
        'csharp': ['.cs'],
        'golang': ['.go'],
        'rust': ['.rs'],
    }
    
    # Check if there's a direct mapping
    if provided_lower in format_mappings:
        for fmt in format_mappings[provided_lower]:
            if fmt in supported_formats and fmt not in suggestions:
                suggestions.append(fmt)
    
    # If no direct mapping, try similarity matching
    if not suggestions:
        # Check for formats starting with the same letter
        first_char = provided_lower[0] if provided_lower else ''
        for fmt in supported_formats:
            fmt_clean = fmt.lstrip('.')
            if fmt_clean.startswith(first_char) and fmt not in suggestions:
                suggestions.append(fmt)
                if len(suggestions) >= 3:
                    break
    
    # If still no suggestions, provide most common formats
    if not suggestions:
        common_formats = ['.pdf', '.txt', '.mp4', '.mp3']
        for fmt in common_formats:
            if fmt in supported_formats and fmt not in suggestions:
                suggestions.append(fmt)
                if len(suggestions) >= 3:
                    break
    
    return suggestions[:3]  # Return up to 3 suggestions


def validate_language_code(language_code: str) -> str:
    """
    Validate language code.

    Args:
        language_code: Language code to validate

    Returns:
        Validated language code

    Raises:
        ValidationError: If language code is not supported
    """
    if language_code not in SUPPORTED_LANGUAGES:
        raise ValidationError(
            message=f"Unsupported language code: {language_code}",
            field="language_code",
            details={
                "supported_languages": list(SUPPORTED_LANGUAGES),
            },
        )

    return language_code


def validate_file_size(file_size: int, content_type: ContentType) -> None:
    """
    Validate file size against limits.

    Args:
        file_size: File size in bytes
        content_type: Content type

    Raises:
        ValidationError: If file size exceeds limit
    """
    max_size = MAX_FILE_SIZES.get(content_type)

    if max_size and file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        actual_size_mb = file_size / (1024 * 1024)

        raise ValidationError(
            message=f"File size ({actual_size_mb:.2f} MB) exceeds limit ({max_size_mb:.2f} MB)",
            field="file_size",
            details={
                "file_size": file_size,
                "max_size": max_size,
                "content_type": content_type.value,
            },
        )


def validate_email(email: str) -> str:
    """
    Validate email address format.

    Args:
        email: Email address

    Returns:
        Validated email address

    Raises:
        ValidationError: If email format is invalid
    """
    import re

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        raise ValidationError(
            message=f"Invalid email format: {email}",
            field="email",
        )

    return email.lower()


def validate_password(password: str) -> None:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Raises:
        ValidationError: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise ValidationError(
            message="Password must be at least 8 characters long",
            field="password",
        )

    # Check for at least one uppercase, one lowercase, and one digit
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)

    if not (has_upper and has_lower and has_digit):
        raise ValidationError(
            message="Password must contain at least one uppercase letter, one lowercase letter, and one digit",
            field="password",
        )


def validate_text_length(
    text: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    field_name: str = "text",
) -> None:
    """
    Validate text length.

    Args:
        text: Text to validate
        min_length: Minimum length (optional)
        max_length: Maximum length (optional)
        field_name: Field name for error messages

    Raises:
        ValidationError: If text length is invalid
    """
    text_length = len(text)

    if min_length and text_length < min_length:
        raise ValidationError(
            message=f"{field_name} must be at least {min_length} characters",
            field=field_name,
            details={"length": text_length, "min_length": min_length},
        )

    if max_length and text_length > max_length:
        raise ValidationError(
            message=f"{field_name} must not exceed {max_length} characters",
            field=field_name,
            details={"length": text_length, "max_length": max_length},
        )


def get_supported_formats_by_type(content_type: ContentType) -> List[str]:
    """
    Get list of supported file extensions for a content type.

    Args:
        content_type: Content type

    Returns:
        List of supported extensions
    """
    return SUPPORTED_FORMATS.get(content_type, [])


def validate_file_format_comprehensive(
    filename: str,
    file_size: Optional[int] = None,
    mime_type: Optional[str] = None,
) -> Tuple[ContentType, Dict[str, Any]]:
    """
    Perform comprehensive file format validation.

    This function validates:
    1. File extension is present and supported
    2. File size is within limits (if provided)
    3. MIME type matches extension (if provided)

    Args:
        filename: Filename with extension
        file_size: File size in bytes (optional)
        mime_type: MIME type (optional)

    Returns:
        Tuple of (ContentType, validation_info dict)

    Raises:
        ValidationError: If filename is invalid
        UnsupportedFormatError: If format is not supported
    """
    # Extract extension
    if "." not in filename:
        raise ValidationError(
            message="Filename must have an extension",
            field="filename",
            details={
                "filename": filename,
                "suggestion": "Please provide a filename with a valid extension (e.g., document.pdf, video.mp4)",
            },
        )
    
    extension = "." + filename.rsplit(".", 1)[1].lower()
    
    # Validate content type
    content_type = validate_content_type(extension)
    
    validation_info = {
        "extension": extension,
        "content_type": content_type.value,
        "filename": filename,
    }
    
    # Validate file size if provided
    if file_size is not None:
        try:
            validate_file_size(file_size, content_type)
            validation_info["file_size_valid"] = True
            validation_info["file_size"] = file_size
        except ValidationError as e:
            validation_info["file_size_valid"] = False
            validation_info["file_size_error"] = str(e)
            raise
    
    # Validate MIME type if provided
    if mime_type:
        expected_mime_types = _get_expected_mime_types(content_type, extension)
        mime_type_valid = any(
            mime_type.startswith(expected) for expected in expected_mime_types
        )
        validation_info["mime_type"] = mime_type
        validation_info["mime_type_valid"] = mime_type_valid
        validation_info["expected_mime_types"] = expected_mime_types
        
        if not mime_type_valid:
            logger.warning(
                f"MIME type mismatch: got {mime_type}, expected one of {expected_mime_types}"
            )
    
    return content_type, validation_info


def _get_expected_mime_types(content_type: ContentType, extension: str) -> List[str]:
    """
    Get expected MIME types for a content type and extension.

    Args:
        content_type: Content type
        extension: File extension

    Returns:
        List of expected MIME type prefixes
    """
    mime_type_map = {
        ContentType.TEXT: ["text/"],
        ContentType.PDF: ["application/pdf"],
        ContentType.VIDEO: ["video/"],
        ContentType.AUDIO: ["audio/"],
        ContentType.CODE: ["text/", "application/"],
    }
    
    return mime_type_map.get(content_type, [])
