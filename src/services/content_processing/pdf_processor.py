"""PDF content processing service with text extraction."""

import logging
import time
import re
from io import BytesIO
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

from .text_processor import TextProcessor
from ...shared.models.content import (
    ProcessedContent,
    SummaryType,
)
from ...shared.utils.errors import (
    ContentProcessingError,
    ProcessingTimeoutError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Service for processing PDF content with text extraction."""

    # Processing time limits (in seconds)
    PDF_PROCESSING_TIMEOUT = 30

    # Technical term patterns (common patterns for technical terms)
    TECHNICAL_TERM_PATTERNS = [
        r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b',  # CamelCase
        r'\b[A-Z]{2,}\b',  # ACRONYMS
        r'\b\w+\(\)',  # function()
        r'\b[a-z_]+\.[a-z_]+\b',  # module.function
        r'\b\d+\.\d+\.\d+\b',  # version numbers
        r'\b[A-Z][a-z]+\d+\b',  # Type1, Class2
    ]

    def __init__(self, text_processor: TextProcessor) -> None:
        """
        Initialize PDF processor.

        Args:
            text_processor: TextProcessor instance for text analysis
        """
        self.text_processor = text_processor
        logger.info("Initialized PDFProcessor")

    def process_pdf(
        self,
        pdf_file: BytesIO,
        language: str = "en",
        summary_type: Optional[SummaryType] = None,
        preserve_formatting: bool = True,
    ) -> ProcessedContent:
        """
        Process PDF content with text extraction and summarization.

        This method:
        1. Extracts text from PDF pages
        2. Preserves technical terms and formatting
        3. Generates structured summaries using TextProcessor
        4. Returns ProcessedContent within 30-second timeout

        Args:
            pdf_file: PDF file as BytesIO object
            language: Language code (default: "en")
            summary_type: Type of summary to generate (auto-detected if None)
            preserve_formatting: Whether to preserve formatting (default: True)

        Returns:
            ProcessedContent with summary, key points, and concepts

        Raises:
            ContentProcessingError: If processing fails
            ProcessingTimeoutError: If processing exceeds 30 seconds
            ValidationError: If PDF is invalid or empty
        """
        start_time = time.time()

        try:
            logger.info(f"Starting PDF processing, language: {language}")

            # Extract text from PDF
            extracted_text, metadata = self._extract_text_from_pdf(
                pdf_file=pdf_file,
                preserve_formatting=preserve_formatting,
            )

            # Check timeout after extraction
            elapsed_time = time.time() - start_time
            if elapsed_time > self.PDF_PROCESSING_TIMEOUT:
                raise ProcessingTimeoutError(
                    content_type="pdf",
                    time_limit=self.PDF_PROCESSING_TIMEOUT,
                    time_elapsed=int(elapsed_time),
                )

            # Validate extracted text
            if not extracted_text or not extracted_text.strip():
                raise ValidationError(
                    message="PDF contains no extractable text",
                    field="pdf_content",
                    details={"page_count": metadata.get("page_count", 0)},
                )

            # Identify and preserve technical terms
            technical_terms = self._identify_technical_terms(extracted_text)
            logger.info(f"Identified {len(technical_terms)} technical terms")

            # Process text using TextProcessor
            # Calculate remaining time for text processing
            remaining_time = self.PDF_PROCESSING_TIMEOUT - (time.time() - start_time)
            if remaining_time < 5:
                raise ProcessingTimeoutError(
                    content_type="pdf",
                    time_limit=self.PDF_PROCESSING_TIMEOUT,
                    time_elapsed=int(time.time() - start_time),
                )

            processed_content = self.text_processor.process_text(
                text=extracted_text,
                language=language,
                summary_type=summary_type,
            )

            # Add PDF-specific metadata
            processed_content.metadata.update({
                "source_type": "pdf",
                "page_count": metadata.get("page_count", 0),
                "technical_terms": technical_terms[:20],  # Limit to top 20
                "extraction_method": "pypdf",
            })

            # Calculate final processing time
            processing_time = time.time() - start_time
            processed_content.processing_time = processing_time

            logger.info(
                f"Successfully processed PDF in {processing_time:.2f}s "
                f"(pages: {metadata.get('page_count', 0)}, "
                f"words: {metadata.get('word_count', 0)})"
            )

            return processed_content

        except (ProcessingTimeoutError, ValidationError):
            raise
        except ContentProcessingError:
            raise
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Error processing PDF: {e}")
            raise ContentProcessingError(
                message=f"Failed to process PDF: {str(e)}",
                content_type="pdf",
                details={"elapsed_time": elapsed_time},
            )

    def _extract_text_from_pdf(
        self,
        pdf_file: BytesIO,
        preserve_formatting: bool = True,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from PDF file.

        Args:
            pdf_file: PDF file as BytesIO object
            preserve_formatting: Whether to preserve formatting

        Returns:
            Tuple of (extracted_text, metadata)

        Raises:
            ContentProcessingError: If extraction fails
            ValidationError: If PDF is invalid
        """
        try:
            # Reset file pointer to beginning
            pdf_file.seek(0)

            # Create PDF reader
            try:
                reader = PdfReader(pdf_file)
            except Exception as e:
                raise ValidationError(
                    message=f"Invalid PDF file: {str(e)}",
                    field="pdf_file",
                )

            # Get page count
            page_count = len(reader.pages)
            logger.info(f"PDF has {page_count} pages")

            if page_count == 0:
                raise ValidationError(
                    message="PDF has no pages",
                    field="pdf_file",
                )

            # Extract text from all pages
            extracted_pages = []
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        if preserve_formatting:
                            # Preserve paragraph breaks and formatting
                            page_text = self._preserve_formatting(page_text)
                        extracted_pages.append(page_text)
                        logger.debug(f"Extracted text from page {page_num + 1}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue

            # Combine all pages
            if preserve_formatting:
                # Add page breaks between pages
                extracted_text = "\n\n--- Page Break ---\n\n".join(extracted_pages)
            else:
                extracted_text = "\n\n".join(extracted_pages)

            # Count words
            word_count = len(extracted_text.split())

            # Prepare metadata
            metadata = {
                "page_count": page_count,
                "pages_extracted": len(extracted_pages),
                "word_count": word_count,
            }

            # Try to extract PDF metadata
            try:
                if reader.metadata:
                    pdf_metadata = {}
                    if reader.metadata.title:
                        pdf_metadata["title"] = reader.metadata.title
                    if reader.metadata.author:
                        pdf_metadata["author"] = reader.metadata.author
                    if reader.metadata.subject:
                        pdf_metadata["subject"] = reader.metadata.subject
                    if pdf_metadata:
                        metadata["pdf_metadata"] = pdf_metadata
            except Exception as e:
                logger.debug(f"Could not extract PDF metadata: {e}")

            logger.info(
                f"Extracted {word_count} words from {len(extracted_pages)}/{page_count} pages"
            )

            return extracted_text, metadata

        except (ValidationError, ContentProcessingError):
            raise
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise ContentProcessingError(
                message=f"Failed to extract text from PDF: {str(e)}",
                content_type="pdf",
            )

    def _preserve_formatting(self, text: str) -> str:
        """
        Preserve formatting in extracted text.

        This method:
        - Preserves paragraph breaks
        - Maintains bullet points and numbered lists
        - Keeps indentation for code blocks
        - Preserves line breaks in structured content

        Args:
            text: Raw extracted text

        Returns:
            Formatted text
        """
        # Remove excessive whitespace while preserving structure
        lines = text.split('\n')
        formatted_lines = []

        for line in lines:
            # Preserve lines with content
            stripped = line.strip()
            if stripped:
                # Check if line is a bullet point or numbered list
                if re.match(r'^[\s]*[-•*]\s+', line) or re.match(r'^[\s]*\d+\.\s+', line):
                    formatted_lines.append(line.rstrip())
                # Check if line appears to be code (has significant indentation)
                elif len(line) - len(line.lstrip()) >= 4:
                    formatted_lines.append(line.rstrip())
                else:
                    formatted_lines.append(stripped)
            else:
                # Preserve paragraph breaks (empty lines)
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')

        # Join lines back together
        formatted_text = '\n'.join(formatted_lines)

        # Remove excessive consecutive empty lines (max 2)
        formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)

        return formatted_text

    def _identify_technical_terms(self, text: str) -> List[str]:
        """
        Identify technical terms in text.

        Technical terms include:
        - CamelCase identifiers
        - ACRONYMS
        - Function names (with parentheses)
        - Module/package names (with dots)
        - Version numbers
        - Type names with numbers

        Args:
            text: Text to analyze

        Returns:
            List of unique technical terms
        """
        technical_terms = set()

        # Apply each pattern
        for pattern in self.TECHNICAL_TERM_PATTERNS:
            matches = re.findall(pattern, text)
            technical_terms.update(matches)

        # Filter out common words and very short terms
        filtered_terms = []
        common_words = {
            'The', 'This', 'That', 'These', 'Those', 'What', 'When', 'Where',
            'Which', 'Who', 'Why', 'How', 'All', 'Each', 'Every', 'Some',
            'Many', 'Few', 'More', 'Most', 'Other', 'Such', 'Only', 'Own',
            'Same', 'So', 'Than', 'Too', 'Very', 'Can', 'Will', 'Just',
        }

        for term in technical_terms:
            # Skip common words
            if term in common_words:
                continue
            # Skip very short terms (less than 2 characters)
            if len(term) < 2:
                continue
            # Skip terms that are all numbers
            if term.isdigit():
                continue

            filtered_terms.append(term)

        # Sort by frequency (most common first)
        term_counts = {}
        for term in filtered_terms:
            term_counts[term] = text.count(term)

        sorted_terms = sorted(term_counts.keys(), key=lambda t: term_counts[t], reverse=True)

        logger.debug(f"Identified {len(sorted_terms)} technical terms")
        return sorted_terms

    def extract_text_only(
        self,
        pdf_file: BytesIO,
        preserve_formatting: bool = True,
    ) -> str:
        """
        Extract text from PDF without processing.

        Useful for quick text extraction without summarization.

        Args:
            pdf_file: PDF file as BytesIO object
            preserve_formatting: Whether to preserve formatting

        Returns:
            Extracted text

        Raises:
            ContentProcessingError: If extraction fails
        """
        try:
            extracted_text, _ = self._extract_text_from_pdf(
                pdf_file=pdf_file,
                preserve_formatting=preserve_formatting,
            )
            return extracted_text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise ContentProcessingError(
                message=f"Failed to extract text from PDF: {str(e)}",
                content_type="pdf",
            )

    def get_pdf_metadata(self, pdf_file: BytesIO) -> Dict[str, Any]:
        """
        Extract metadata from PDF without processing content.

        Args:
            pdf_file: PDF file as BytesIO object

        Returns:
            Dictionary with PDF metadata

        Raises:
            ContentProcessingError: If metadata extraction fails
        """
        try:
            # Reset file pointer
            pdf_file.seek(0)

            # Create PDF reader
            reader = PdfReader(pdf_file)

            metadata = {
                "page_count": len(reader.pages),
            }

            # Extract PDF metadata if available
            if reader.metadata:
                if reader.metadata.title:
                    metadata["title"] = reader.metadata.title
                if reader.metadata.author:
                    metadata["author"] = reader.metadata.author
                if reader.metadata.subject:
                    metadata["subject"] = reader.metadata.subject
                if reader.metadata.creator:
                    metadata["creator"] = reader.metadata.creator
                if reader.metadata.producer:
                    metadata["producer"] = reader.metadata.producer

            return metadata

        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {e}")
            raise ContentProcessingError(
                message=f"Failed to extract PDF metadata: {str(e)}",
                content_type="pdf",
            )
