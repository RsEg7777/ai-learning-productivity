"""Unit tests for PDF processor."""

import pytest
from io import BytesIO
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.services.content_processing import PDFProcessor, TextProcessor
from src.shared.models.content import ProcessedContent, Summary, SummaryType, Concept
from src.shared.utils.errors import (
    ContentProcessingError,
    ProcessingTimeoutError,
    ValidationError,
)


class TestPDFProcessor:
    """Test suite for PDFProcessor."""

    @pytest.fixture
    def mock_text_processor(self):
        """Create mock TextProcessor."""
        mock_processor = Mock(spec=TextProcessor)
        
        # Mock process_text to return a ProcessedContent
        mock_summary = Summary(
            id="summary123",
            content_id="content123",
            type=SummaryType.BRIEF,
            text="This is a test summary of the PDF content.",
            key_points=["Point 1", "Point 2", "Point 3"],
            hierarchical_structure=[],
            generated_at=datetime.utcnow(),
        )
        
        mock_processed = ProcessedContent(
            id="processed123",
            original_content="Sample text content",
            summary=mock_summary,
            key_points=["Point 1", "Point 2", "Point 3"],
            concepts=[
                Concept(name="TestConcept", description="A test concept", importance=0.8, related_concepts=[])
            ],
            language="en",
            processing_time=1.5,
            metadata={"word_count": 100},
        )
        
        mock_processor.process_text.return_value = mock_processed
        return mock_processor

    @pytest.fixture
    def pdf_processor(self, mock_text_processor):
        """Create PDFProcessor instance."""
        return PDFProcessor(text_processor=mock_text_processor)

    @pytest.fixture
    def sample_pdf(self):
        """Create a sample PDF file."""
        # Create a simple PDF with text
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Add some text content
        c.drawString(100, 750, "Sample PDF Document")
        c.drawString(100, 730, "This is a test PDF with technical terms.")
        c.drawString(100, 710, "It contains CamelCase, ACRONYMS, and function() calls.")
        c.drawString(100, 690, "Version 1.2.3 of the API documentation.")
        c.drawString(100, 670, "")
        c.drawString(100, 650, "Technical Terms:")
        c.drawString(100, 630, "- HTTPRequest")
        c.drawString(100, 610, "- JSONParser")
        c.drawString(100, 590, "- DatabaseConnection")
        
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return buffer

    @pytest.fixture
    def empty_pdf(self):
        """Create an empty PDF file."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return buffer

    @pytest.fixture
    def multi_page_pdf(self):
        """Create a multi-page PDF file."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Page 1
        c.drawString(100, 750, "Page 1: Introduction")
        c.drawString(100, 730, "This is the first page of the document.")
        c.showPage()
        
        # Page 2
        c.drawString(100, 750, "Page 2: Technical Details")
        c.drawString(100, 730, "This page contains technical information.")
        c.drawString(100, 710, "Including API endpoints and data structures.")
        c.showPage()
        
        # Page 3
        c.drawString(100, 750, "Page 3: Conclusion")
        c.drawString(100, 730, "Summary of the document.")
        c.showPage()
        
        c.save()
        buffer.seek(0)
        return buffer

    def test_process_pdf_success(self, pdf_processor, sample_pdf, mock_text_processor):
        """Test successful PDF processing."""
        # Act
        result = pdf_processor.process_pdf(
            pdf_file=sample_pdf,
            language="en",
        )

        # Assert
        assert isinstance(result, ProcessedContent)
        assert result.language == "en"
        assert result.processing_time > 0
        assert "source_type" in result.metadata
        assert result.metadata["source_type"] == "pdf"
        assert "page_count" in result.metadata
        assert "technical_terms" in result.metadata
        
        # Verify text processor was called
        mock_text_processor.process_text.assert_called_once()

    def test_process_pdf_with_summary_type(self, pdf_processor, sample_pdf, mock_text_processor):
        """Test PDF processing with specific summary type."""
        # Act
        result = pdf_processor.process_pdf(
            pdf_file=sample_pdf,
            language="en",
            summary_type=SummaryType.DETAILED,
        )

        # Assert
        assert isinstance(result, ProcessedContent)
        
        # Verify text processor was called with correct summary type
        call_args = mock_text_processor.process_text.call_args
        assert call_args[1]["summary_type"] == SummaryType.DETAILED

    def test_process_pdf_multi_page(self, pdf_processor, multi_page_pdf, mock_text_processor):
        """Test processing multi-page PDF."""
        # Act
        result = pdf_processor.process_pdf(
            pdf_file=multi_page_pdf,
            language="en",
        )

        # Assert
        assert isinstance(result, ProcessedContent)
        assert result.metadata["page_count"] == 3

    def test_process_pdf_empty_content(self, pdf_processor, empty_pdf):
        """Test processing PDF with no extractable text."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            pdf_processor.process_pdf(
                pdf_file=empty_pdf,
                language="en",
            )

        assert "no extractable text" in str(exc_info.value).lower()

    def test_process_pdf_invalid_file(self, pdf_processor):
        """Test processing invalid PDF file."""
        # Arrange
        invalid_pdf = BytesIO(b"This is not a PDF file")

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            pdf_processor.process_pdf(
                pdf_file=invalid_pdf,
                language="en",
            )

        assert "invalid pdf" in str(exc_info.value).lower()

    def test_process_pdf_preserve_formatting(self, pdf_processor, sample_pdf, mock_text_processor):
        """Test PDF processing with formatting preservation."""
        # Act
        result = pdf_processor.process_pdf(
            pdf_file=sample_pdf,
            language="en",
            preserve_formatting=True,
        )

        # Assert
        assert isinstance(result, ProcessedContent)
        
        # Verify text processor was called
        call_args = mock_text_processor.process_text.call_args
        extracted_text = call_args[1]["text"]
        
        # Check that formatting markers are present
        assert isinstance(extracted_text, str)
        assert len(extracted_text) > 0

    def test_process_pdf_no_formatting(self, pdf_processor, sample_pdf, mock_text_processor):
        """Test PDF processing without formatting preservation."""
        # Act
        result = pdf_processor.process_pdf(
            pdf_file=sample_pdf,
            language="en",
            preserve_formatting=False,
        )

        # Assert
        assert isinstance(result, ProcessedContent)
        mock_text_processor.process_text.assert_called_once()

    def test_extract_text_only(self, pdf_processor, sample_pdf):
        """Test extracting text without processing."""
        # Act
        text = pdf_processor.extract_text_only(pdf_file=sample_pdf)

        # Assert
        assert isinstance(text, str)
        assert len(text) > 0
        assert "Sample PDF Document" in text or "test PDF" in text.lower()

    def test_extract_text_only_multi_page(self, pdf_processor, multi_page_pdf):
        """Test extracting text from multi-page PDF."""
        # Act
        text = pdf_processor.extract_text_only(pdf_file=multi_page_pdf)

        # Assert
        assert isinstance(text, str)
        assert len(text) > 0
        # Should contain content from multiple pages
        assert "Page 1" in text or "Introduction" in text
        assert "Page 2" in text or "Technical Details" in text
        assert "Page 3" in text or "Conclusion" in text

    def test_extract_text_only_invalid_pdf(self, pdf_processor):
        """Test extracting text from invalid PDF."""
        # Arrange
        invalid_pdf = BytesIO(b"Not a PDF")

        # Act & Assert
        with pytest.raises(ContentProcessingError):
            pdf_processor.extract_text_only(pdf_file=invalid_pdf)

    def test_get_pdf_metadata(self, pdf_processor, sample_pdf):
        """Test extracting PDF metadata."""
        # Act
        metadata = pdf_processor.get_pdf_metadata(pdf_file=sample_pdf)

        # Assert
        assert isinstance(metadata, dict)
        assert "page_count" in metadata
        assert metadata["page_count"] > 0

    def test_get_pdf_metadata_multi_page(self, pdf_processor, multi_page_pdf):
        """Test extracting metadata from multi-page PDF."""
        # Act
        metadata = pdf_processor.get_pdf_metadata(pdf_file=multi_page_pdf)

        # Assert
        assert metadata["page_count"] == 3

    def test_get_pdf_metadata_invalid_pdf(self, pdf_processor):
        """Test extracting metadata from invalid PDF."""
        # Arrange
        invalid_pdf = BytesIO(b"Not a PDF")

        # Act & Assert
        with pytest.raises(ContentProcessingError):
            pdf_processor.get_pdf_metadata(pdf_file=invalid_pdf)

    def test_identify_technical_terms(self, pdf_processor):
        """Test technical term identification."""
        # Arrange
        text = """
        This document describes the HTTPRequest class and JSONParser module.
        The API version 1.2.3 uses CamelCase naming conventions.
        Functions like getData() and processRequest() are available.
        The DatabaseConnection handles SQL queries.
        Common acronyms include HTTP, JSON, API, and SQL.
        """

        # Act
        terms = pdf_processor._identify_technical_terms(text)

        # Assert
        assert isinstance(terms, list)
        assert len(terms) > 0
        
        # Check for expected technical terms
        terms_str = " ".join(terms)
        assert any(term in terms_str for term in ["HTTPRequest", "JSONParser", "CamelCase", "DatabaseConnection"])

    def test_identify_technical_terms_filters_common_words(self, pdf_processor):
        """Test that common words are filtered out."""
        # Arrange
        text = "The API uses This and That for processing. HTTP and JSON are supported."

        # Act
        terms = pdf_processor._identify_technical_terms(text)

        # Assert
        # Should not include common words like "The", "This", "That"
        assert "The" not in terms
        assert "This" not in terms
        assert "That" not in terms
        
        # Should include technical terms
        assert any(term in ["API", "HTTP", "JSON"] for term in terms)

    def test_preserve_formatting_bullet_points(self, pdf_processor):
        """Test formatting preservation for bullet points."""
        # Arrange
        text = """
        Introduction
        
        - First point
        - Second point
        - Third point
        
        Conclusion
        """

        # Act
        formatted = pdf_processor._preserve_formatting(text)

        # Assert
        assert "- First point" in formatted
        assert "- Second point" in formatted
        assert "- Third point" in formatted

    def test_preserve_formatting_numbered_lists(self, pdf_processor):
        """Test formatting preservation for numbered lists."""
        # Arrange
        text = """
        Steps:
        
        1. First step
        2. Second step
        3. Third step
        """

        # Act
        formatted = pdf_processor._preserve_formatting(text)

        # Assert
        assert "1. First step" in formatted
        assert "2. Second step" in formatted
        assert "3. Third step" in formatted

    def test_preserve_formatting_removes_excessive_whitespace(self, pdf_processor):
        """Test that excessive whitespace is removed."""
        # Arrange
        text = """
        
        
        
        Paragraph 1
        
        
        
        Paragraph 2
        
        
        
        """

        # Act
        formatted = pdf_processor._preserve_formatting(text)

        # Assert
        # Should not have more than 2 consecutive newlines
        assert "\n\n\n" not in formatted
        assert "Paragraph 1" in formatted
        assert "Paragraph 2" in formatted

    def test_process_pdf_timeout(self, pdf_processor, sample_pdf, mock_text_processor):
        """Test PDF processing timeout."""
        # Arrange
        # Make text processor take too long by simulating timeout in extraction
        # We'll patch the time.time to simulate timeout
        with patch('src.services.content_processing.pdf_processor.time.time') as mock_time:
            # First call (start_time), second call (after extraction check), third call (timeout check)
            mock_time.side_effect = [0, 35, 35]  # Simulate 35 seconds elapsed

            # Act & Assert
            with pytest.raises(ProcessingTimeoutError) as exc_info:
                pdf_processor.process_pdf(
                    pdf_file=sample_pdf,
                    language="en",
                )

            assert exc_info.value.error_code == "PROCESSING_TIMEOUT"
            assert exc_info.value.details["content_type"] == "pdf"
            assert exc_info.value.details["time_limit"] == 30

    def test_process_pdf_different_languages(self, pdf_processor, sample_pdf, mock_text_processor):
        """Test PDF processing with different languages."""
        languages = ["en", "hi", "es", "fr"]

        for lang in languages:
            # Reset mock and update return value to match language
            mock_text_processor.process_text.reset_mock()
            
            # Create a new mock result with the correct language
            mock_summary = Summary(
                id="summary123",
                content_id="content123",
                type=SummaryType.BRIEF,
                text="This is a test summary of the PDF content.",
                key_points=["Point 1", "Point 2", "Point 3"],
                hierarchical_structure=[],
                generated_at=datetime.utcnow(),
            )
            
            mock_processed = ProcessedContent(
                id="processed123",
                original_content="Sample text content",
                summary=mock_summary,
                key_points=["Point 1", "Point 2", "Point 3"],
                concepts=[
                    Concept(name="TestConcept", description="A test concept", importance=0.8, related_concepts=[])
                ],
                language=lang,  # Use the correct language
                processing_time=1.5,
                metadata={"word_count": 100},
            )
            
            mock_text_processor.process_text.return_value = mock_processed

            # Act
            result = pdf_processor.process_pdf(
                pdf_file=sample_pdf,
                language=lang,
            )

            # Assert
            assert result.language == lang
            
            # Verify text processor was called with correct language
            call_args = mock_text_processor.process_text.call_args
            assert call_args[1]["language"] == lang

    def test_extract_text_from_pdf_metadata(self, pdf_processor, sample_pdf):
        """Test that PDF metadata is extracted."""
        # Act
        text, metadata = pdf_processor._extract_text_from_pdf(
            pdf_file=sample_pdf,
            preserve_formatting=True,
        )

        # Assert
        assert isinstance(metadata, dict)
        assert "page_count" in metadata
        assert "pages_extracted" in metadata
        assert "word_count" in metadata
        assert metadata["page_count"] > 0
        assert metadata["word_count"] > 0

    def test_technical_terms_in_processed_content(self, pdf_processor, sample_pdf, mock_text_processor):
        """Test that technical terms are included in processed content metadata."""
        # Act
        result = pdf_processor.process_pdf(
            pdf_file=sample_pdf,
            language="en",
        )

        # Assert
        assert "technical_terms" in result.metadata
        assert isinstance(result.metadata["technical_terms"], list)

    def test_process_pdf_with_code_blocks(self, pdf_processor, mock_text_processor):
        """Test PDF processing with code blocks."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create PDF with code-like content
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        c.drawString(100, 750, "Code Example:")
        c.drawString(120, 730, "    def function():")
        c.drawString(120, 710, "        return True")
        
        c.showPage()
        c.save()
        buffer.seek(0)

        # Act
        result = pdf_processor.process_pdf(
            pdf_file=buffer,
            language="en",
        )

        # Assert
        assert isinstance(result, ProcessedContent)
        mock_text_processor.process_text.assert_called_once()

    def test_process_pdf_large_document(self, pdf_processor, mock_text_processor):
        """Test processing large PDF document."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a larger PDF
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Add multiple pages with content
        for page_num in range(10):
            c.drawString(100, 750, f"Page {page_num + 1}")
            for line_num in range(20):
                c.drawString(100, 730 - (line_num * 20), f"Line {line_num + 1} of page {page_num + 1}")
            c.showPage()
        
        c.save()
        buffer.seek(0)

        # Act
        result = pdf_processor.process_pdf(
            pdf_file=buffer,
            language="en",
        )

        # Assert
        assert isinstance(result, ProcessedContent)
        assert result.metadata["page_count"] == 10

    def test_extract_text_handles_extraction_errors(self, pdf_processor, mock_text_processor):
        """Test that extraction handles errors gracefully."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a valid PDF
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 750, "Page 1")
        c.showPage()
        c.drawString(100, 750, "Page 2")
        c.showPage()
        c.save()
        buffer.seek(0)

        # Act - should handle any page extraction errors
        text, metadata = pdf_processor._extract_text_from_pdf(
            pdf_file=buffer,
            preserve_formatting=True,
        )

        # Assert
        assert isinstance(text, str)
        assert len(text) > 0
        assert metadata["page_count"] == 2
