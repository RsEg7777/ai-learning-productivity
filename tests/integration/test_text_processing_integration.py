"""Integration tests for text processing workflow."""

import pytest
from unittest.mock import Mock, patch
from io import BytesIO

from src.services.content_processing.text_processor import TextProcessor
from src.services.content_processing.content_upload_service import ContentUploadService
from src.shared.aws_clients.bedrock_client import BedrockClient
from src.shared.aws_clients.s3_client import S3Client
from src.shared.models.content import ContentType, SummaryType


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    client = Mock(spec=S3Client)
    client.upload_file = Mock(return_value="s3://test-bucket/uploads/user123/2024/01/content123.txt")
    client.file_exists = Mock(return_value=True)
    return client


@pytest.fixture
def mock_bedrock_client():
    """Create a mock Bedrock client."""
    client = Mock(spec=BedrockClient)
    client.generate_summary = Mock(return_value="This is a comprehensive summary of the content.")
    client.invoke_claude = Mock(return_value="""1. First key point
2. Second key point
3. Third key point

Concept: Machine Learning
Description: AI subset for learning from data
Importance: 0.9""")
    return client


@pytest.fixture
def upload_service(mock_s3_client):
    """Create ContentUploadService instance."""
    return ContentUploadService(s3_client=mock_s3_client)


@pytest.fixture
def text_processor(mock_bedrock_client):
    """Create TextProcessor instance."""
    return TextProcessor(bedrock_client=mock_bedrock_client)


class TestTextProcessingIntegration:
    """Integration tests for complete text processing workflow."""

    def test_upload_and_process_text_content(
        self,
        upload_service,
        text_processor,
        mock_s3_client,
        mock_bedrock_client,
    ):
        """Test complete workflow: upload text file and process it."""
        # Step 1: Upload text content
        text_content = "This is a test document about machine learning. " * 50
        file_obj = BytesIO(text_content.encode('utf-8'))
        
        content = upload_service.upload_content(
            user_id="user123",
            file_obj=file_obj,
            filename="test_document.txt",
            title="Test Document",
            language="en",
        )
        
        # Verify upload
        assert content.id is not None
        assert content.user_id == "user123"
        assert content.type == ContentType.TEXT
        assert content.s3_location is not None
        mock_s3_client.upload_file.assert_called_once()
        
        # Step 2: Process the text content
        processed = text_processor.process_text(
            text=text_content,
            language="en",
        )
        
        # Verify processing
        assert processed.id is not None
        assert processed.original_content == text_content
        assert processed.summary is not None
        assert processed.summary.text == "This is a comprehensive summary of the content."
        assert len(processed.key_points) > 0
        assert len(processed.concepts) > 0
        assert processed.processing_time < 30  # Within timeout
        
        # Verify Bedrock was called
        assert mock_bedrock_client.generate_summary.called
        assert mock_bedrock_client.invoke_claude.called

    def test_upload_and_process_large_text(
        self,
        upload_service,
        text_processor,
        mock_s3_client,
        mock_bedrock_client,
    ):
        """Test workflow with large text requiring hierarchical summary."""
        # Create large text (>10,000 words)
        text_content = "This is a test sentence about artificial intelligence. " * 2500
        file_obj = BytesIO(text_content.encode('utf-8'))
        
        # Mock multiple summary calls for chunks
        mock_bedrock_client.generate_summary.side_effect = [
            "Summary of chunk 1",
            "Summary of chunk 2",
            "Overall hierarchical summary",
        ]
        
        # Step 1: Upload
        content = upload_service.upload_content(
            user_id="user456",
            file_obj=file_obj,
            filename="large_document.txt",
            title="Large Document",
            language="en",
        )
        
        assert content.id is not None
        
        # Step 2: Process with hierarchical summary
        processed = text_processor.process_text(
            text=text_content,
            language="en",
        )
        
        # Verify hierarchical processing
        assert processed.summary.type == SummaryType.HIERARCHICAL
        assert len(processed.summary.hierarchical_structure) > 0
        assert processed.processing_time < 30

    def test_process_text_with_different_summary_types(
        self,
        text_processor,
        mock_bedrock_client,
    ):
        """Test processing same text with different summary types."""
        text_content = "Machine learning is a subset of AI. " * 100
        
        # Test brief summary
        brief_result = text_processor.process_text(
            text=text_content,
            language="en",
            summary_type=SummaryType.BRIEF,
        )
        assert brief_result.summary.type == SummaryType.BRIEF
        
        # Test detailed summary
        detailed_result = text_processor.process_text(
            text=text_content,
            language="en",
            summary_type=SummaryType.DETAILED,
        )
        assert detailed_result.summary.type == SummaryType.DETAILED

    def test_multilingual_text_processing(
        self,
        upload_service,
        text_processor,
        mock_s3_client,
        mock_bedrock_client,
    ):
        """Test processing text in different languages."""
        # French text
        french_text = "Ceci est un document de test sur l'apprentissage automatique. " * 50
        file_obj = BytesIO(french_text.encode('utf-8'))
        
        # Upload
        content = upload_service.upload_content(
            user_id="user789",
            file_obj=file_obj,
            filename="document_fr.txt",
            title="Document Français",
            language="fr",
        )
        
        assert content.language == "fr"
        
        # Process
        processed = text_processor.process_text(
            text=french_text,
            language="fr",
        )
        
        assert processed.language == "fr"
        assert processed.summary is not None

    def test_end_to_end_with_concept_extraction(
        self,
        text_processor,
        mock_bedrock_client,
    ):
        """Test end-to-end processing with focus on concept extraction."""
        text_content = """
        Machine learning is a subset of artificial intelligence that enables 
        systems to learn and improve from experience without being explicitly 
        programmed. Deep learning is a subset of machine learning that uses 
        neural networks with multiple layers. Natural language processing is 
        another important area of AI that deals with text and speech.
        """
        
        # Mock concept extraction response
        mock_bedrock_client.invoke_claude.return_value = """Concept: Machine Learning
Description: AI subset that enables learning from experience
Importance: 0.95

Concept: Deep Learning
Description: ML subset using multi-layer neural networks
Importance: 0.90

Concept: Natural Language Processing
Description: AI area dealing with text and speech
Importance: 0.85"""
        
        processed = text_processor.process_text(text=text_content, language="en")
        
        # Verify concepts were extracted
        assert len(processed.concepts) >= 3
        concept_names = [c.name for c in processed.concepts]
        assert "Machine Learning" in concept_names
        assert "Deep Learning" in concept_names
        assert "Natural Language Processing" in concept_names
        
        # Verify importance scores
        for concept in processed.concepts:
            assert 0.0 <= concept.importance <= 1.0

    def test_processing_performance_within_timeout(
        self,
        text_processor,
        mock_bedrock_client,
    ):
        """Test that processing completes within 30-second timeout."""
        # Medium-sized text
        text_content = "This is a test sentence. " * 500
        
        processed = text_processor.process_text(text=text_content, language="en")
        
        # Verify processing time is within limit
        assert processed.processing_time < 30
        assert processed.processing_time >= 0  # Allow 0 for mocked tests

    def test_key_points_extraction_quality(
        self,
        text_processor,
        mock_bedrock_client,
    ):
        """Test that key points are properly extracted."""
        text_content = """
        The main findings of this study are:
        1. Machine learning improves accuracy
        2. Deep learning requires more data
        3. Transfer learning reduces training time
        4. Ensemble methods increase robustness
        5. Regularization prevents overfitting
        """
        
        mock_bedrock_client.invoke_claude.return_value = """1. Machine learning improves accuracy
2. Deep learning requires more data
3. Transfer learning reduces training time
4. Ensemble methods increase robustness
5. Regularization prevents overfitting"""
        
        processed = text_processor.process_text(text=text_content, language="en")
        
        # Verify key points
        assert len(processed.key_points) >= 3
        assert any("accuracy" in kp.lower() for kp in processed.key_points)

    def test_metadata_tracking(
        self,
        text_processor,
        mock_bedrock_client,
    ):
        """Test that metadata is properly tracked."""
        text_content = "Short test content."
        
        processed = text_processor.process_text(text=text_content, language="en")
        
        # Verify metadata
        assert "word_count" in processed.metadata
        assert "summary_type" in processed.metadata
        assert processed.metadata["word_count"] == 3
        assert processed.metadata["summary_type"] in ["brief", "detailed", "hierarchical"]
