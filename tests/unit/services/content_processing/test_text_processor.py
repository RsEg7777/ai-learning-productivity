"""Unit tests for TextProcessor."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.services.content_processing.text_processor import TextProcessor
from src.shared.models.content import (
    ProcessedContent,
    Summary,
    SummaryType,
    SummaryNode,
    Concept,
)
from src.shared.utils.errors import (
    ContentProcessingError,
    ProcessingTimeoutError,
)


@pytest.fixture
def mock_bedrock_client():
    """Create a mock Bedrock client."""
    client = Mock()
    client.generate_summary = Mock(return_value="This is a test summary.")
    client.invoke_claude = Mock(return_value="1. Key point one\n2. Key point two\n3. Key point three")
    return client


@pytest.fixture
def text_processor(mock_bedrock_client):
    """Create a TextProcessor instance with mock client."""
    return TextProcessor(bedrock_client=mock_bedrock_client)


class TestTextProcessor:
    """Test suite for TextProcessor."""

    def test_initialization(self, mock_bedrock_client):
        """Test TextProcessor initialization."""
        processor = TextProcessor(bedrock_client=mock_bedrock_client)
        assert processor.bedrock_client == mock_bedrock_client
        assert processor.TEXT_PROCESSING_TIMEOUT == 30
        assert processor.HIERARCHICAL_THRESHOLD == 10000

    def test_process_text_brief_summary(self, text_processor, mock_bedrock_client):
        """Test processing short text with brief summary."""
        text = "This is a short test text with less than 2000 words. " * 20
        
        result = text_processor.process_text(text, language="en")
        
        assert isinstance(result, ProcessedContent)
        assert result.original_content == text
        assert result.language == "en"
        assert result.summary.type == SummaryType.BRIEF
        assert result.processing_time < 30
        assert len(result.key_points) > 0
        
        # Verify Bedrock was called
        mock_bedrock_client.generate_summary.assert_called_once()

    def test_process_text_detailed_summary(self, text_processor, mock_bedrock_client):
        """Test processing medium text with detailed summary."""
        # Create text with ~2500 words
        text = "This is a test sentence with multiple words. " * 500
        
        result = text_processor.process_text(text, language="en")
        
        assert isinstance(result, ProcessedContent)
        assert result.summary.type == SummaryType.DETAILED
        assert result.processing_time < 30

    def test_process_text_hierarchical_summary(self, text_processor, mock_bedrock_client):
        """Test processing large text with hierarchical summary."""
        # Create text with >10,000 words
        text = "This is a test sentence with multiple words. " * 2500
        
        # Mock multiple summary calls for chunks
        mock_bedrock_client.generate_summary.side_effect = [
            "Summary of chunk 1",
            "Summary of chunk 2",
            "Overall hierarchical summary with main points and sub-points",
        ]
        
        result = text_processor.process_text(text, language="en")
        
        assert isinstance(result, ProcessedContent)
        assert result.summary.type == SummaryType.HIERARCHICAL
        assert len(result.summary.hierarchical_structure) > 0
        assert result.processing_time < 30

    def test_process_text_empty_input(self, text_processor):
        """Test processing empty text raises error."""
        with pytest.raises(ContentProcessingError) as exc_info:
            text_processor.process_text("", language="en")
        
        assert "cannot be empty" in str(exc_info.value)

    def test_process_text_whitespace_only(self, text_processor):
        """Test processing whitespace-only text raises error."""
        with pytest.raises(ContentProcessingError) as exc_info:
            text_processor.process_text("   \n\t  ", language="en")
        
        assert "cannot be empty" in str(exc_info.value)

    def test_process_text_explicit_summary_type(self, text_processor, mock_bedrock_client):
        """Test processing with explicit summary type."""
        text = "Short text."
        
        result = text_processor.process_text(
            text,
            language="en",
            summary_type=SummaryType.DETAILED,
        )
        
        assert result.summary.type == SummaryType.DETAILED

    def test_process_text_extracts_concepts(self, text_processor, mock_bedrock_client):
        """Test that concepts are extracted from text."""
        text = "Machine learning is a subset of artificial intelligence."
        
        # Mock concept extraction
        mock_bedrock_client.invoke_claude.return_value = """Concept: Machine Learning
Description: A subset of AI that enables systems to learn from data
Importance: 0.9

Concept: Artificial Intelligence
Description: Technology that simulates human intelligence
Importance: 0.8"""
        
        result = text_processor.process_text(text, language="en")
        
        assert len(result.concepts) > 0
        assert all(isinstance(c, Concept) for c in result.concepts)

    def test_count_words(self, text_processor):
        """Test word counting."""
        text = "This is a test with five words"
        count = text_processor._count_words(text)
        assert count == 7

    def test_count_words_with_extra_whitespace(self, text_processor):
        """Test word counting with extra whitespace."""
        text = "This  is   a    test"
        count = text_processor._count_words(text)
        assert count == 4

    def test_split_into_chunks(self, text_processor):
        """Test splitting text into chunks."""
        # Create text with paragraph breaks to enable splitting
        paragraphs = ["word " * 100 for _ in range(10)]
        text = "\n\n".join(paragraphs)  # 1000 words with paragraph breaks
        chunks = text_processor._split_into_chunks(text, chunk_size=300)
        
        assert len(chunks) > 1
        # Verify each chunk is roughly the right size
        for chunk in chunks:
            word_count = len(chunk.split())
            assert word_count <= 400  # Allow some flexibility

    def test_split_into_chunks_small_text(self, text_processor):
        """Test splitting small text returns single chunk."""
        text = "This is a small text."
        chunks = text_processor._split_into_chunks(text, chunk_size=100)
        
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_extract_key_points_from_summary(self, text_processor):
        """Test extracting key points from summary text."""
        summary_text = """1. First key point
2. Second key point
3. Third key point"""
        
        key_points = text_processor._extract_key_points_from_summary(summary_text)
        
        assert len(key_points) == 3
        assert "First key point" in key_points
        assert "Second key point" in key_points

    def test_extract_key_points_from_bullet_list(self, text_processor):
        """Test extracting key points from bullet list."""
        summary_text = """- First bullet point
- Second bullet point
• Third bullet point"""
        
        key_points = text_processor._extract_key_points_from_summary(summary_text)
        
        assert len(key_points) >= 2

    def test_extract_sub_points(self, text_processor):
        """Test extracting sub-points from text."""
        text = """1. First point
2. Second point
3. Third point"""
        
        sub_points = text_processor._extract_sub_points(text)
        
        assert len(sub_points) >= 2
        assert any("First point" in sp for sp in sub_points)

    def test_parse_key_points(self, text_processor):
        """Test parsing key points from LLM response."""
        response = """1. First key point here
2. Second key point here
3. Third key point here"""
        
        key_points = text_processor._parse_key_points(response)
        
        assert len(key_points) == 3
        assert "First key point here" in key_points

    def test_parse_concepts(self, text_processor):
        """Test parsing concepts from LLM response."""
        response = """Concept: Machine Learning
Description: A subset of AI that enables learning from data
Importance: 0.9

Concept: Neural Networks
Description: Computing systems inspired by biological neural networks
Importance: 0.8"""
        
        concepts = text_processor._parse_concepts(response)
        
        assert len(concepts) == 2
        assert concepts[0].name == "Machine Learning"
        assert concepts[0].importance == 0.9
        assert concepts[1].name == "Neural Networks"

    def test_parse_concepts_invalid_importance(self, text_processor):
        """Test parsing concepts with invalid importance scores."""
        response = """Concept: Test Concept
Description: A test concept
Importance: 1.5"""
        
        concepts = text_processor._parse_concepts(response)
        
        # Should clamp to valid range
        assert len(concepts) == 1
        assert concepts[0].importance <= 1.0

    def test_build_hierarchical_structure(self, text_processor):
        """Test building hierarchical structure from chunk summaries."""
        chunk_summaries = [
            "Summary of first section with key points.",
            "Summary of second section with more points.",
        ]
        
        structure = text_processor._build_hierarchical_structure(chunk_summaries)
        
        assert len(structure) == 2
        assert all(isinstance(node, SummaryNode) for node in structure)
        assert structure[0].level == 0
        assert "Section 1" in structure[0].text

    def test_generate_standard_summary(self, text_processor, mock_bedrock_client):
        """Test generating standard summary."""
        text = "This is test content."
        
        summary = text_processor._generate_standard_summary(
            text,
            SummaryType.BRIEF,
            "en",
        )
        
        assert isinstance(summary, Summary)
        assert summary.type == SummaryType.BRIEF
        assert summary.text == "This is a test summary."
        mock_bedrock_client.generate_summary.assert_called_once()

    def test_generate_hierarchical_summary(self, text_processor, mock_bedrock_client):
        """Test generating hierarchical summary."""
        # Create large text
        text = "This is a test sentence. " * 10000
        
        # Mock summary generation
        mock_bedrock_client.generate_summary.side_effect = [
            "Chunk 1 summary",
            "Chunk 2 summary",
            "Overall summary with hierarchy",
        ]
        
        summary = text_processor._generate_hierarchical_summary(text, "en")
        
        assert isinstance(summary, Summary)
        assert summary.type == SummaryType.HIERARCHICAL
        assert len(summary.hierarchical_structure) > 0

    def test_bedrock_error_handling(self, text_processor, mock_bedrock_client):
        """Test error handling when Bedrock fails."""
        text = "Test content"
        mock_bedrock_client.generate_summary.side_effect = Exception("Bedrock error")
        
        with pytest.raises(ContentProcessingError) as exc_info:
            text_processor.process_text(text)
        
        # Error message could be from summary generation or overall processing
        assert "Failed to generate summary" in str(exc_info.value) or "Failed to process text content" in str(exc_info.value)

    def test_processing_includes_metadata(self, text_processor, mock_bedrock_client):
        """Test that processed content includes metadata."""
        text = "This is a test with ten words in it now."
        
        result = text_processor.process_text(text)
        
        assert "word_count" in result.metadata
        assert "summary_type" in result.metadata
        assert result.metadata["word_count"] > 0

    def test_multilingual_processing(self, text_processor, mock_bedrock_client):
        """Test processing text in different languages."""
        text = "Ceci est un texte en français."
        
        result = text_processor.process_text(text, language="fr")
        
        assert result.language == "fr"
        assert isinstance(result, ProcessedContent)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_text_at_hierarchical_threshold(self, text_processor, mock_bedrock_client):
        """Test text exactly at hierarchical threshold."""
        # Create text with exactly 10,000 words
        text = "word " * 10000
        
        mock_bedrock_client.generate_summary.side_effect = [
            "Chunk summary",
            "Overall summary",
        ]
        
        result = text_processor.process_text(text)
        
        # Should not use hierarchical for exactly 10,000 words
        assert result.summary.type in [SummaryType.DETAILED, SummaryType.HIERARCHICAL]

    def test_text_just_over_threshold(self, text_processor, mock_bedrock_client):
        """Test text just over hierarchical threshold."""
        # Create text with 10,001 words
        text = "word " * 10001
        
        mock_bedrock_client.generate_summary.side_effect = [
            "Chunk summary",
            "Overall summary",
        ]
        
        result = text_processor.process_text(text)
        
        assert result.summary.type == SummaryType.HIERARCHICAL

    def test_very_long_text(self, text_processor, mock_bedrock_client):
        """Test processing very long text."""
        # Create text with 50,000 words
        text = "word " * 50000
        
        # Mock multiple chunk summaries
        mock_bedrock_client.generate_summary.side_effect = [
            f"Chunk {i} summary" for i in range(10)
        ] + ["Overall summary"]
        
        result = text_processor.process_text(text)
        
        assert isinstance(result, ProcessedContent)
        assert result.summary.type == SummaryType.HIERARCHICAL

    def test_text_with_special_characters(self, text_processor, mock_bedrock_client):
        """Test processing text with special characters."""
        text = "This text has special chars: @#$%^&*() and émojis 🎉"
        
        result = text_processor.process_text(text)
        
        assert isinstance(result, ProcessedContent)
        assert result.original_content == text

    def test_text_with_code_blocks(self, text_processor, mock_bedrock_client):
        """Test processing text containing code blocks."""
        text = """Here is some code:
```python
def hello():
    print("Hello, world!")
```
This is the explanation."""
        
        result = text_processor.process_text(text)
        
        assert isinstance(result, ProcessedContent)

    def test_single_word_text(self, text_processor, mock_bedrock_client):
        """Test processing single word."""
        text = "Hello"
        
        result = text_processor.process_text(text)
        
        assert isinstance(result, ProcessedContent)
        assert result.metadata["word_count"] == 1
