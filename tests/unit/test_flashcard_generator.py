"""Unit tests for flashcard generation service."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import uuid

from src.services.quiz_generation.flashcard_generator import FlashcardGenerator
from src.shared.models.quiz import Flashcard, DifficultyLevel, SpacedRepetitionData
from src.shared.models.content import (
    ProcessedContent,
    Summary,
    SummaryType,
    Concept,
)
from src.shared.utils.errors import ContentProcessingError


@pytest.fixture
def mock_bedrock_client():
    """Create a mock Bedrock client."""
    client = Mock()
    return client


@pytest.fixture
def flashcard_generator(mock_bedrock_client):
    """Create a FlashcardGenerator instance with mock client."""
    return FlashcardGenerator(bedrock_client=mock_bedrock_client)


@pytest.fixture
def sample_processed_content():
    """Create sample processed content for testing."""
    summary = Summary(
        id=str(uuid.uuid4()),
        content_id="test-content-123",
        type=SummaryType.BRIEF,
        text="Machine learning is a subset of AI that enables computers to learn from data.",
        key_points=[
            "Machine learning is part of artificial intelligence",
            "Systems learn from data without explicit programming",
            "Algorithms improve through experience",
        ],
        hierarchical_structure=[],
        generated_at=datetime.utcnow(),
    )

    concepts = [
        Concept(
            name="Machine Learning",
            description="A method of data analysis that automates analytical model building",
            importance=0.9,
            related_concepts=["AI", "Deep Learning"],
        ),
        Concept(
            name="Artificial Intelligence",
            description="The simulation of human intelligence by machines",
            importance=0.8,
            related_concepts=["Machine Learning"],
        ),
    ]

    return ProcessedContent(
        id="test-content-123",
        original_content="Machine learning is a subset of artificial intelligence...",
        summary=summary,
        key_points=summary.key_points,
        concepts=concepts,
        language="en",
        processing_time=1.5,
        metadata={"word_count": 100},
    )


@pytest.fixture
def sample_bedrock_response():
    """Sample Bedrock response for flashcard generation."""
    return """
FLASHCARD 1
Question: What is machine learning?
Answer: Machine learning is a subset of artificial intelligence that focuses on developing algorithms and statistical models that enable computers to learn from and make predictions based on data.
Difficulty: easy
Tags: machine-learning, ai, basics

FLASHCARD 2
Question: How do machine learning systems improve their performance?
Answer: Machine learning systems improve their performance through experience by analyzing data patterns and adjusting their algorithms accordingly, without being explicitly programmed for each specific task.
Difficulty: medium
Tags: machine-learning, learning-process, algorithms

FLASHCARD 3
Question: What is the key difference between traditional programming and machine learning?
Answer: In traditional programming, explicit instructions are provided to solve problems, while machine learning systems learn patterns from data and improve their performance over time without explicit programming for each scenario.
Difficulty: medium
Tags: machine-learning, programming, comparison

FLASHCARD 4
Question: What role does data play in machine learning?
Answer: Data is fundamental to machine learning as it provides the examples and patterns that algorithms use to learn, make predictions, and improve their accuracy over time.
Difficulty: easy
Tags: machine-learning, data, fundamentals

FLASHCARD 5
Question: Why is machine learning considered a subset of artificial intelligence?
Answer: Machine learning is considered a subset of AI because it represents one approach to achieving artificial intelligence by enabling systems to learn and adapt from experience, rather than following pre-programmed rules.
Difficulty: medium
Tags: machine-learning, ai, relationship

FLASHCARD 6
Question: What are statistical models in the context of machine learning?
Answer: Statistical models in machine learning are mathematical representations that capture patterns and relationships in data, allowing systems to make predictions and decisions based on probability and statistical inference.
Difficulty: hard
Tags: machine-learning, statistics, models

FLASHCARD 7
Question: How does machine learning enable computers to make predictions?
Answer: Machine learning enables predictions by training algorithms on historical data to identify patterns and relationships, which can then be applied to new, unseen data to forecast outcomes or classify information.
Difficulty: medium
Tags: machine-learning, predictions, algorithms

FLASHCARD 8
Question: What is meant by 'learning from data' in machine learning?
Answer: Learning from data means that machine learning algorithms analyze examples, identify patterns, extract features, and adjust their internal parameters to improve accuracy in performing specific tasks.
Difficulty: easy
Tags: machine-learning, data, learning

FLASHCARD 9
Question: What types of problems can machine learning solve?
Answer: Machine learning can solve various problems including classification, regression, clustering, pattern recognition, natural language processing, computer vision, and recommendation systems.
Difficulty: hard
Tags: machine-learning, applications, problem-solving

FLASHCARD 10
Question: What is the relationship between algorithms and machine learning?
Answer: Algorithms are the core of machine learning, providing the mathematical and computational procedures that process data, identify patterns, and make decisions or predictions based on learned information.
Difficulty: medium
Tags: machine-learning, algorithms, fundamentals
"""


class TestFlashcardGenerator:
    """Test suite for FlashcardGenerator."""

    def test_initialization(self, mock_bedrock_client):
        """Test FlashcardGenerator initialization."""
        generator = FlashcardGenerator(bedrock_client=mock_bedrock_client)
        assert generator.bedrock_client == mock_bedrock_client
        assert generator.MIN_FLASHCARDS == 10
        assert generator.MAX_TOKENS == 3000

    def test_generate_flashcards_success(
        self,
        flashcard_generator,
        mock_bedrock_client,
        sample_processed_content,
        sample_bedrock_response,
    ):
        """Test successful flashcard generation."""
        # Mock Bedrock response
        mock_bedrock_client.invoke_claude.return_value = sample_bedrock_response

        # Generate flashcards
        flashcards = flashcard_generator.generate_flashcards(
            content=sample_processed_content,
            count=10,
        )

        # Verify results
        assert len(flashcards) == 10
        assert all(isinstance(f, Flashcard) for f in flashcards)
        assert all(f.content_id == sample_processed_content.id for f in flashcards)
        assert all(f.question for f in flashcards)
        assert all(f.answer for f in flashcards)
        assert all(isinstance(f.difficulty, DifficultyLevel) for f in flashcards)
        assert all(f.tags for f in flashcards)
        assert all(isinstance(f.repetition_data, SpacedRepetitionData) for f in flashcards)

        # Verify Bedrock was called
        mock_bedrock_client.invoke_claude.assert_called_once()

    def test_generate_flashcards_minimum_count(
        self,
        flashcard_generator,
        mock_bedrock_client,
        sample_processed_content,
        sample_bedrock_response,
    ):
        """Test that at least MIN_FLASHCARDS are generated."""
        mock_bedrock_client.invoke_claude.return_value = sample_bedrock_response

        # Request fewer than minimum
        flashcards = flashcard_generator.generate_flashcards(
            content=sample_processed_content,
            count=5,
        )

        # Should still generate at least MIN_FLASHCARDS
        assert len(flashcards) >= flashcard_generator.MIN_FLASHCARDS

    def test_generate_flashcards_default_count(
        self,
        flashcard_generator,
        mock_bedrock_client,
        sample_processed_content,
        sample_bedrock_response,
    ):
        """Test flashcard generation with default count."""
        mock_bedrock_client.invoke_claude.return_value = sample_bedrock_response

        # Generate with default count
        flashcards = flashcard_generator.generate_flashcards(
            content=sample_processed_content,
        )

        # Should generate at least MIN_FLASHCARDS
        assert len(flashcards) >= flashcard_generator.MIN_FLASHCARDS

    def test_generate_flashcards_empty_content(self, flashcard_generator):
        """Test flashcard generation with empty content."""
        empty_content = ProcessedContent(
            id="empty-123",
            original_content="",
            summary=Summary(
                id=str(uuid.uuid4()),
                content_id="empty-123",
                type=SummaryType.BRIEF,
                text="",
                key_points=[],
                hierarchical_structure=[],
                generated_at=datetime.utcnow(),
            ),
            key_points=[],
            concepts=[],
            language="en",
            processing_time=0.0,
            metadata={},
        )

        with pytest.raises(ContentProcessingError) as exc_info:
            flashcard_generator.generate_flashcards(content=empty_content)

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_generate_flashcards_difficulty_distribution(
        self,
        flashcard_generator,
        mock_bedrock_client,
        sample_processed_content,
        sample_bedrock_response,
    ):
        """Test that flashcards have varied difficulty levels."""
        mock_bedrock_client.invoke_claude.return_value = sample_bedrock_response

        flashcards = flashcard_generator.generate_flashcards(
            content=sample_processed_content,
            count=10,
        )

        # Check that we have multiple difficulty levels
        difficulties = {f.difficulty for f in flashcards}
        assert len(difficulties) > 1, "Should have varied difficulty levels"

        # Count each difficulty level
        easy_count = sum(1 for f in flashcards if f.difficulty == DifficultyLevel.EASY)
        medium_count = sum(1 for f in flashcards if f.difficulty == DifficultyLevel.MEDIUM)
        hard_count = sum(1 for f in flashcards if f.difficulty == DifficultyLevel.HARD)

        assert easy_count > 0 or medium_count > 0 or hard_count > 0

    def test_generate_flashcards_with_tags(
        self,
        flashcard_generator,
        mock_bedrock_client,
        sample_processed_content,
        sample_bedrock_response,
    ):
        """Test that flashcards have relevant tags."""
        mock_bedrock_client.invoke_claude.return_value = sample_bedrock_response

        flashcards = flashcard_generator.generate_flashcards(
            content=sample_processed_content,
            count=10,
        )

        # Verify all flashcards have tags
        assert all(f.tags for f in flashcards)
        assert all(len(f.tags) <= 3 for f in flashcards)
        assert all(isinstance(tag, str) for f in flashcards for tag in f.tags)

    def test_parse_flashcards(self, flashcard_generator, sample_bedrock_response):
        """Test parsing flashcards from LLM response."""
        flashcard_data = flashcard_generator._parse_flashcards(sample_bedrock_response)

        assert len(flashcard_data) == 10
        assert all("question" in f for f in flashcard_data)
        assert all("answer" in f for f in flashcard_data)
        assert all("difficulty" in f for f in flashcard_data)
        assert all("tags" in f for f in flashcard_data)

    def test_parse_difficulty(self, flashcard_generator):
        """Test difficulty parsing."""
        assert flashcard_generator._parse_difficulty("easy") == DifficultyLevel.EASY
        assert flashcard_generator._parse_difficulty("medium") == DifficultyLevel.MEDIUM
        assert flashcard_generator._parse_difficulty("hard") == DifficultyLevel.HARD
        assert flashcard_generator._parse_difficulty("EASY") == DifficultyLevel.EASY
        assert flashcard_generator._parse_difficulty("invalid") == DifficultyLevel.MEDIUM

    def test_determine_difficulty_from_importance(self, flashcard_generator):
        """Test difficulty determination from importance score."""
        assert (
            flashcard_generator._determine_difficulty_from_importance(0.9)
            == DifficultyLevel.HARD
        )
        assert (
            flashcard_generator._determine_difficulty_from_importance(0.6)
            == DifficultyLevel.MEDIUM
        )
        assert (
            flashcard_generator._determine_difficulty_from_importance(0.3)
            == DifficultyLevel.EASY
        )

    def test_generate_simple_flashcards(
        self,
        flashcard_generator,
        sample_processed_content,
    ):
        """Test simple flashcard generation fallback."""
        flashcards = flashcard_generator._generate_simple_flashcards(
            content=sample_processed_content,
            count=5,
        )

        assert len(flashcards) <= 5
        assert all("question" in f for f in flashcards)
        assert all("answer" in f for f in flashcards)
        assert all("difficulty" in f for f in flashcards)
        assert all("tags" in f for f in flashcards)

    def test_generate_flashcards_from_text(
        self,
        flashcard_generator,
        mock_bedrock_client,
        sample_bedrock_response,
    ):
        """Test generating flashcards directly from text."""
        mock_bedrock_client.invoke_claude.return_value = sample_bedrock_response

        text = "Machine learning is a subset of artificial intelligence."
        flashcards = flashcard_generator.generate_flashcards_from_text(
            text=text,
            content_id="test-123",
            language="en",
            count=10,
        )

        assert len(flashcards) >= 10
        assert all(isinstance(f, Flashcard) for f in flashcards)
        assert all(f.content_id == "test-123" for f in flashcards)

    def test_generate_flashcards_bedrock_error(
        self,
        flashcard_generator,
        mock_bedrock_client,
        sample_processed_content,
    ):
        """Test handling of Bedrock errors."""
        mock_bedrock_client.invoke_claude.side_effect = Exception("Bedrock error")

        with pytest.raises(ContentProcessingError) as exc_info:
            flashcard_generator.generate_flashcards(content=sample_processed_content)

        assert "failed to generate flashcards" in str(exc_info.value).lower()

    def test_flashcard_spaced_repetition_initialization(
        self,
        flashcard_generator,
        mock_bedrock_client,
        sample_processed_content,
        sample_bedrock_response,
    ):
        """Test that flashcards have initialized spaced repetition data."""
        mock_bedrock_client.invoke_claude.return_value = sample_bedrock_response

        flashcards = flashcard_generator.generate_flashcards(
            content=sample_processed_content,
            count=10,
        )

        for flashcard in flashcards:
            assert flashcard.repetition_data is not None
            assert flashcard.repetition_data.ease_factor == 2.5
            assert flashcard.repetition_data.interval == 1
            assert flashcard.repetition_data.repetitions == 0
            assert flashcard.repetition_data.last_reviewed is None
            assert flashcard.repetition_data.next_review is None

    def test_flashcard_unique_ids(
        self,
        flashcard_generator,
        mock_bedrock_client,
        sample_processed_content,
        sample_bedrock_response,
    ):
        """Test that each flashcard has a unique ID."""
        mock_bedrock_client.invoke_claude.return_value = sample_bedrock_response

        flashcards = flashcard_generator.generate_flashcards(
            content=sample_processed_content,
            count=10,
        )

        ids = [f.id for f in flashcards]
        assert len(ids) == len(set(ids)), "All flashcard IDs should be unique"

    def test_flashcard_timestamps(
        self,
        flashcard_generator,
        mock_bedrock_client,
        sample_processed_content,
        sample_bedrock_response,
    ):
        """Test that flashcards have creation timestamps."""
        mock_bedrock_client.invoke_claude.return_value = sample_bedrock_response

        before_generation = datetime.utcnow()
        flashcards = flashcard_generator.generate_flashcards(
            content=sample_processed_content,
            count=10,
        )
        after_generation = datetime.utcnow()

        for flashcard in flashcards:
            assert flashcard.created_at is not None
            assert before_generation <= flashcard.created_at <= after_generation

    def test_generate_flashcards_with_long_content(
        self,
        flashcard_generator,
        mock_bedrock_client,
        sample_bedrock_response,
    ):
        """Test flashcard generation with very long content."""
        # Create content with very long text
        long_text = "Machine learning " * 1000  # Very long text
        
        summary = Summary(
            id=str(uuid.uuid4()),
            content_id="long-content-123",
            type=SummaryType.DETAILED,
            text=long_text,
            key_points=["Point 1", "Point 2"],
            hierarchical_structure=[],
            generated_at=datetime.utcnow(),
        )

        long_content = ProcessedContent(
            id="long-content-123",
            original_content=long_text,
            summary=summary,
            key_points=["Point 1", "Point 2"],
            concepts=[],
            language="en",
            processing_time=2.0,
            metadata={"word_count": 2000},
        )

        mock_bedrock_client.invoke_claude.return_value = sample_bedrock_response

        flashcards = flashcard_generator.generate_flashcards(
            content=long_content,
            count=10,
        )

        # Should handle long content and still generate flashcards
        assert len(flashcards) >= 10

    def test_generate_flashcards_insufficient_response(
        self,
        flashcard_generator,
        mock_bedrock_client,
        sample_processed_content,
    ):
        """Test handling when Bedrock returns insufficient flashcards."""
        # Mock response with only 3 flashcards
        insufficient_response = """
FLASHCARD 1
Question: What is ML?
Answer: Machine learning
Difficulty: easy
Tags: ml, basics

FLASHCARD 2
Question: What is AI?
Answer: Artificial intelligence
Difficulty: easy
Tags: ai, basics

FLASHCARD 3
Question: How do they relate?
Answer: ML is part of AI
Difficulty: medium
Tags: ml, ai, relationship
"""
        mock_bedrock_client.invoke_claude.return_value = insufficient_response

        flashcards = flashcard_generator.generate_flashcards(
            content=sample_processed_content,
            count=10,
        )

        # Should still generate at least MIN_FLASHCARDS using fallback
        assert len(flashcards) >= flashcard_generator.MIN_FLASHCARDS
