"""Unit tests for quiz generation service."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.services.quiz_generation.quiz_generator import QuizGenerator
from src.shared.models.quiz import Quiz, Question, QuestionType, DifficultyLevel
from src.shared.models.content import ProcessedContent, Summary, SummaryType, Concept
from src.shared.utils.errors import ContentProcessingError


@pytest.fixture
def mock_bedrock_client():
    """Create a mock Bedrock client."""
    client = Mock()
    return client


@pytest.fixture
def quiz_generator(mock_bedrock_client):
    """Create a QuizGenerator instance with mock client."""
    return QuizGenerator(bedrock_client=mock_bedrock_client)


@pytest.fixture
def sample_content():
    """Create sample processed content for testing."""
    summary = Summary(
        id="summary-1",
        content_id="content-1",
        type=SummaryType.BRIEF,
        text="Python is a high-level programming language. It emphasizes code readability. Python supports multiple programming paradigms.",
        key_points=["High-level language", "Code readability", "Multiple paradigms"],
        hierarchical_structure=[],
        generated_at=datetime.utcnow(),
    )

    concepts = [
        Concept(name="Python", description="A programming language", importance=0.9),
        Concept(name="Readability", description="Code clarity", importance=0.7),
    ]

    return ProcessedContent(
        id="content-1",
        original_content="Python is a high-level programming language known for its simplicity and readability.",
        summary=summary,
        key_points=["High-level language", "Code readability", "Multiple paradigms"],
        concepts=concepts,
        language="en",
        processing_time=1.5,
        metadata={},
    )


class TestQuizGenerator:
    """Test suite for QuizGenerator."""

    def test_initialization(self, mock_bedrock_client):
        """Test quiz generator initialization."""
        generator = QuizGenerator(bedrock_client=mock_bedrock_client)
        assert generator.bedrock_client == mock_bedrock_client
        assert generator.DEFAULT_QUESTION_COUNT == 10

    def test_generate_quiz_empty_content(self, quiz_generator):
        """Test quiz generation with empty content raises error."""
        # Create a minimal summary for the empty content
        empty_summary = Summary(
            id="summary-empty",
            content_id="empty",
            type=SummaryType.BRIEF,
            text="",
            key_points=[],
            hierarchical_structure=[],
            generated_at=datetime.utcnow(),
        )
        
        empty_content = ProcessedContent(
            id="empty",
            original_content="",
            summary=empty_summary,
            key_points=[],
            concepts=[],
            language="en",
            processing_time=0,
            metadata={},
        )

        with pytest.raises(ContentProcessingError) as exc_info:
            quiz_generator.generate_quiz(empty_content)
        
        assert "Content cannot be empty" in str(exc_info.value)

    def test_generate_quiz_none_content(self, quiz_generator):
        """Test quiz generation with None content raises error."""
        with pytest.raises(ContentProcessingError):
            quiz_generator.generate_quiz(None)

    def test_calculate_question_type_counts(self, quiz_generator):
        """Test question type distribution calculation."""
        counts = quiz_generator._calculate_question_type_counts(10)
        
        # Should have all three types
        assert QuestionType.MULTIPLE_CHOICE in counts
        assert QuestionType.TRUE_FALSE in counts
        assert QuestionType.FILL_IN_BLANK in counts
        
        # Total should equal requested count
        assert sum(counts.values()) == 10
        
        # Multiple choice should be the most common (50%)
        assert counts[QuestionType.MULTIPLE_CHOICE] >= 5

    def test_calculate_difficulty_counts(self, quiz_generator):
        """Test difficulty distribution calculation."""
        counts = quiz_generator._calculate_difficulty_counts(10)
        
        # Should have all three difficulty levels
        assert DifficultyLevel.EASY in counts
        assert DifficultyLevel.MEDIUM in counts
        assert DifficultyLevel.HARD in counts
        
        # Total should equal requested count
        assert sum(counts.values()) == 10
        
        # Medium should be the most common (50%)
        assert counts[DifficultyLevel.MEDIUM] >= 5

    def test_parse_difficulty(self, quiz_generator):
        """Test difficulty parsing from string."""
        assert quiz_generator._parse_difficulty("easy") == DifficultyLevel.EASY
        assert quiz_generator._parse_difficulty("EASY") == DifficultyLevel.EASY
        assert quiz_generator._parse_difficulty("medium") == DifficultyLevel.MEDIUM
        assert quiz_generator._parse_difficulty("hard") == DifficultyLevel.HARD
        assert quiz_generator._parse_difficulty("invalid") == DifficultyLevel.MEDIUM

    def test_parse_multiple_choice_questions(self, quiz_generator):
        """Test parsing multiple choice questions from LLM response."""
        response = """
QUESTION 1
Text: What is Python?
A) A snake
B) A programming language
C) A type of food
D) A mathematical concept
Correct: B
Explanation: Python is a high-level programming language.
Difficulty: easy

QUESTION 2
Text: What does Python emphasize?
A) Speed
B) Complexity
C) Readability
D) Size
Correct: C
Explanation: Python emphasizes code readability and simplicity.
Difficulty: medium
"""
        
        questions = quiz_generator._parse_multiple_choice_questions(response)
        
        assert len(questions) == 2
        assert all(q.type == QuestionType.MULTIPLE_CHOICE for q in questions)
        assert all(len(q.options) == 4 for q in questions)
        assert questions[0].difficulty == DifficultyLevel.EASY
        assert questions[1].difficulty == DifficultyLevel.MEDIUM

    def test_parse_true_false_questions(self, quiz_generator):
        """Test parsing true/false questions from LLM response."""
        response = """
QUESTION 1
Statement: Python is a high-level programming language.
Answer: True
Explanation: Python is indeed a high-level language.
Difficulty: easy

QUESTION 2
Statement: Python only supports procedural programming.
Answer: False
Explanation: Python supports multiple programming paradigms.
Difficulty: medium
"""
        
        questions = quiz_generator._parse_true_false_questions(response)
        
        assert len(questions) == 2
        assert all(q.type == QuestionType.TRUE_FALSE for q in questions)
        assert all(q.options == ["True", "False"] for q in questions)
        assert questions[0].correct_answer == "True"
        assert questions[1].correct_answer == "False"

    def test_parse_fill_in_blank_questions(self, quiz_generator):
        """Test parsing fill-in-blank questions from LLM response."""
        response = """
QUESTION 1
Text: Python is a _____ programming language.
Answer: high-level
Explanation: Python is classified as a high-level programming language.
Difficulty: easy

QUESTION 2
Text: Python emphasizes code _____.
Answer: readability
Explanation: One of Python's key features is code readability.
Difficulty: medium
"""
        
        questions = quiz_generator._parse_fill_in_blank_questions(response)
        
        assert len(questions) == 2
        assert all(q.type == QuestionType.FILL_IN_BLANK for q in questions)
        assert all(q.options is None for q in questions)
        assert "_____" in questions[0].text or "____" in questions[0].text

    def test_generate_fallback_questions(self, quiz_generator, sample_content):
        """Test fallback question generation."""
        questions = quiz_generator._generate_fallback_questions(sample_content, 5)
        
        assert len(questions) <= 5
        assert all(isinstance(q, Question) for q in questions)
        # Should generate from key points and concepts
        assert any(q.type == QuestionType.TRUE_FALSE for q in questions)

    def test_balance_difficulty(self, quiz_generator):
        """Test difficulty balancing."""
        # Create questions with unbalanced difficulty
        questions = [
            Question(
                id=f"q{i}",
                type=QuestionType.MULTIPLE_CHOICE,
                text=f"Question {i}",
                options=["A", "B", "C", "D"],
                correct_answer="A",
                explanation="Test",
                points=1,
                difficulty=DifficultyLevel.EASY if i < 7 else DifficultyLevel.HARD,
            )
            for i in range(10)
        ]
        
        target_counts = {
            DifficultyLevel.EASY: 3,
            DifficultyLevel.MEDIUM: 5,
            DifficultyLevel.HARD: 2,
        }
        
        balanced = quiz_generator._balance_difficulty(questions, target_counts)
        
        # Should return questions (may not perfectly match due to availability)
        assert len(balanced) > 0
        assert all(isinstance(q, Question) for q in balanced)

    @patch.object(QuizGenerator, '_generate_questions')
    def test_generate_quiz_success(self, mock_generate_questions, quiz_generator, sample_content):
        """Test successful quiz generation."""
        # Mock question generation
        mock_questions = [
            Question(
                id=f"q{i}",
                type=QuestionType.MULTIPLE_CHOICE,
                text=f"Question {i}",
                options=["A", "B", "C", "D"],
                correct_answer="A",
                explanation="Test",
                points=1,
                difficulty=DifficultyLevel.MEDIUM,
            )
            for i in range(10)
        ]
        mock_generate_questions.return_value = mock_questions
        
        quiz = quiz_generator.generate_quiz(
            content=sample_content,
            title="Test Quiz",
            question_count=10,
            time_limit=600,
            passing_score=70,
        )
        
        assert isinstance(quiz, Quiz)
        assert quiz.title == "Test Quiz"
        assert len(quiz.questions) == 10
        assert quiz.time_limit == 600
        assert quiz.passing_score == 70
        assert quiz.content_id == sample_content.id

    @patch.object(QuizGenerator, '_generate_questions')
    def test_generate_quiz_default_values(self, mock_generate_questions, quiz_generator, sample_content):
        """Test quiz generation with default values."""
        mock_questions = [
            Question(
                id=f"q{i}",
                type=QuestionType.TRUE_FALSE,
                text=f"Statement {i}",
                options=["True", "False"],
                correct_answer="True",
                explanation="Test",
                points=1,
                difficulty=DifficultyLevel.EASY,
            )
            for i in range(10)
        ]
        mock_generate_questions.return_value = mock_questions
        
        quiz = quiz_generator.generate_quiz(content=sample_content)
        
        assert isinstance(quiz, Quiz)
        assert len(quiz.questions) == 10  # Default count
        assert quiz.passing_score == 70  # Default passing score
        assert quiz.time_limit is None  # No default time limit

    def test_generate_multiple_choice_questions_with_mock(self, quiz_generator, sample_content):
        """Test multiple choice question generation with mocked Bedrock."""
        mock_response = """
QUESTION 1
Text: What is Python?
A) A snake
B) A programming language
C) A type of food
D) A mathematical concept
Correct: B
Explanation: Python is a high-level programming language.
Difficulty: easy

QUESTION 2
Text: What does Python emphasize?
A) Speed
B) Complexity
C) Readability
D) Size
Correct: C
Explanation: Python emphasizes code readability.
Difficulty: medium
"""
        
        quiz_generator.bedrock_client.invoke_claude.return_value = mock_response
        
        questions = quiz_generator._generate_multiple_choice_questions(sample_content, 2)
        
        assert len(questions) == 2
        assert all(q.type == QuestionType.MULTIPLE_CHOICE for q in questions)
        quiz_generator.bedrock_client.invoke_claude.assert_called_once()

    def test_generate_true_false_questions_with_mock(self, quiz_generator, sample_content):
        """Test true/false question generation with mocked Bedrock."""
        mock_response = """
QUESTION 1
Statement: Python is a high-level programming language.
Answer: True
Explanation: Python is indeed a high-level language.
Difficulty: easy

QUESTION 2
Statement: Python only supports procedural programming.
Answer: False
Explanation: Python supports multiple paradigms.
Difficulty: medium
"""
        
        quiz_generator.bedrock_client.invoke_claude.return_value = mock_response
        
        questions = quiz_generator._generate_true_false_questions(sample_content, 2)
        
        assert len(questions) == 2
        assert all(q.type == QuestionType.TRUE_FALSE for q in questions)
        quiz_generator.bedrock_client.invoke_claude.assert_called_once()

    def test_generate_fill_in_blank_questions_with_mock(self, quiz_generator, sample_content):
        """Test fill-in-blank question generation with mocked Bedrock."""
        mock_response = """
QUESTION 1
Text: Python is a _____ programming language.
Answer: high-level
Explanation: Python is classified as a high-level language.
Difficulty: easy

QUESTION 2
Text: Python emphasizes code _____.
Answer: readability
Explanation: Code readability is a key feature.
Difficulty: medium
"""
        
        quiz_generator.bedrock_client.invoke_claude.return_value = mock_response
        
        questions = quiz_generator._generate_fill_in_blank_questions(sample_content, 2)
        
        assert len(questions) == 2
        assert all(q.type == QuestionType.FILL_IN_BLANK for q in questions)
        quiz_generator.bedrock_client.invoke_claude.assert_called_once()

    def test_log_quiz_statistics(self, quiz_generator, sample_content):
        """Test quiz statistics logging."""
        questions = [
            Question(
                id="q1",
                type=QuestionType.MULTIPLE_CHOICE,
                text="Question 1",
                options=["A", "B", "C", "D"],
                correct_answer="A",
                explanation="Test",
                points=1,
                difficulty=DifficultyLevel.EASY,
            ),
            Question(
                id="q2",
                type=QuestionType.TRUE_FALSE,
                text="Statement 2",
                options=["True", "False"],
                correct_answer="True",
                explanation="Test",
                points=1,
                difficulty=DifficultyLevel.MEDIUM,
            ),
            Question(
                id="q3",
                type=QuestionType.FILL_IN_BLANK,
                text="Fill _____ blank",
                options=None,
                correct_answer="in the",
                explanation="Test",
                points=1,
                difficulty=DifficultyLevel.HARD,
            ),
        ]
        
        quiz = Quiz(
            id="quiz-1",
            content_id=sample_content.id,
            title="Test Quiz",
            questions=questions,
            time_limit=600,
            passing_score=70,
            created_at=datetime.utcnow(),
        )
        
        # Should not raise any errors
        quiz_generator._log_quiz_statistics(quiz)

    def test_question_type_distribution(self, quiz_generator):
        """Test that question type distribution is properly configured."""
        distribution = quiz_generator.QUESTION_TYPE_DISTRIBUTION
        
        # Should have all three types
        assert QuestionType.MULTIPLE_CHOICE in distribution
        assert QuestionType.TRUE_FALSE in distribution
        assert QuestionType.FILL_IN_BLANK in distribution
        
        # Ratios should sum to 1.0
        assert abs(sum(distribution.values()) - 1.0) < 0.01

    def test_difficulty_distribution(self, quiz_generator):
        """Test that difficulty distribution is properly configured."""
        distribution = quiz_generator.DIFFICULTY_DISTRIBUTION
        
        # Should have all three levels
        assert DifficultyLevel.EASY in distribution
        assert DifficultyLevel.MEDIUM in distribution
        assert DifficultyLevel.HARD in distribution
        
        # Ratios should sum to 1.0
        assert abs(sum(distribution.values()) - 1.0) < 0.01

    def test_parse_malformed_multiple_choice(self, quiz_generator):
        """Test parsing malformed multiple choice questions."""
        malformed_response = """
QUESTION 1
Text: What is Python?
A) A snake
B) A programming language
Correct: B
Explanation: Python is a language.
Difficulty: easy
"""
        
        questions = quiz_generator._parse_multiple_choice_questions(malformed_response)
        
        # Should handle gracefully and skip malformed questions
        assert len(questions) == 0

    def test_parse_malformed_true_false(self, quiz_generator):
        """Test parsing malformed true/false questions."""
        malformed_response = """
QUESTION 1
Statement: Python is a language.
Explanation: Yes it is.
Difficulty: easy
"""
        
        questions = quiz_generator._parse_true_false_questions(malformed_response)
        
        # Should handle gracefully and skip malformed questions
        assert len(questions) == 0

    def test_parse_fill_in_blank_without_blank(self, quiz_generator):
        """Test parsing fill-in-blank questions without blank marker."""
        response = """
QUESTION 1
Text: Python is a programming language.
Answer: high-level
Explanation: Python is high-level.
Difficulty: easy
"""
        
        questions = quiz_generator._parse_fill_in_blank_questions(response)
        
        # Should skip questions without blank markers
        assert len(questions) == 0

    def test_generate_quiz_with_varied_types(self, quiz_generator, sample_content):
        """Test that generated quiz contains varied question types."""
        # Mock responses for different question types
        mc_response = """
QUESTION 1
Text: What is Python?
A) A snake
B) A programming language
C) A food
D) A concept
Correct: B
Explanation: Python is a programming language.
Difficulty: medium
"""
        
        tf_response = """
QUESTION 1
Statement: Python is readable.
Answer: True
Explanation: Python emphasizes readability.
Difficulty: easy
"""
        
        fib_response = """
QUESTION 1
Text: Python is a _____ language.
Answer: high-level
Explanation: Python is high-level.
Difficulty: medium
"""
        
        # Set up mock to return different responses
        quiz_generator.bedrock_client.invoke_claude.side_effect = [
            mc_response * 5,  # Multiple choice
            tf_response * 3,  # True/false
            fib_response * 2,  # Fill-in-blank
        ]
        
        quiz = quiz_generator.generate_quiz(sample_content, question_count=10)
        
        # Check that we have varied types
        types = [q.type for q in quiz.questions]
        assert QuestionType.MULTIPLE_CHOICE in types
        assert QuestionType.TRUE_FALSE in types
        assert QuestionType.FILL_IN_BLANK in types
