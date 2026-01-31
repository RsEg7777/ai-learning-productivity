"""Unit tests for data models."""

import pytest
from datetime import datetime
from src.shared.models.content import Content, ContentType, Summary, SummaryType
from src.shared.models.quiz import Quiz, Question, QuestionType, Flashcard
from src.shared.models.code import CodeSnippet, ProgrammingLanguage
from src.shared.models.user import User, UserPreferences


class TestContentModels:
    """Test content-related models."""

    def test_content_creation(self):
        """Test creating a Content instance."""
        content = Content(
            id="test-123",
            user_id="user-456",
            title="Test Content",
            type=ContentType.TEXT,
            original_text="This is test content",
            language="en",
        )

        assert content.id == "test-123"
        assert content.user_id == "user-456"
        assert content.type == ContentType.TEXT
        assert content.language == "en"

    def test_summary_creation(self):
        """Test creating a Summary instance."""
        summary = Summary(
            id="summary-123",
            content_id="content-456",
            type=SummaryType.BRIEF,
            text="This is a brief summary",
            key_points=["Point 1", "Point 2"],
        )

        assert summary.id == "summary-123"
        assert summary.type == SummaryType.BRIEF
        assert len(summary.key_points) == 2


class TestQuizModels:
    """Test quiz-related models."""

    def test_question_creation(self):
        """Test creating a Question instance."""
        question = Question(
            id="q-123",
            type=QuestionType.MULTIPLE_CHOICE,
            text="What is 2+2?",
            options=["3", "4", "5", "6"],
            correct_answer="4",
            explanation="2+2 equals 4",
        )

        assert question.id == "q-123"
        assert question.type == QuestionType.MULTIPLE_CHOICE
        assert len(question.options) == 4
        assert question.correct_answer == "4"

    def test_flashcard_creation(self):
        """Test creating a Flashcard instance."""
        flashcard = Flashcard(
            id="fc-123",
            content_id="content-456",
            question="What is Python?",
            answer="A high-level programming language",
        )

        assert flashcard.id == "fc-123"
        assert flashcard.content_id == "content-456"
        assert flashcard.question == "What is Python?"


class TestCodeModels:
    """Test code-related models."""

    def test_code_snippet_creation(self):
        """Test creating a CodeSnippet instance."""
        snippet = CodeSnippet(
            id="code-123",
            user_id="user-456",
            code="print('Hello, World!')",
            language=ProgrammingLanguage.PYTHON,
        )

        assert snippet.id == "code-123"
        assert snippet.language == ProgrammingLanguage.PYTHON
        assert "Hello" in snippet.code


class TestUserModels:
    """Test user-related models."""

    def test_user_creation(self):
        """Test creating a User instance."""
        user = User(
            id="user-123",
            email="test@example.com",
            username="testuser",
        )

        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.is_active is True

    def test_user_preferences(self):
        """Test UserPreferences."""
        prefs = UserPreferences(
            language="hi",
            voice_enabled=True,
            daily_goal_minutes=60,
        )

        assert prefs.language == "hi"
        assert prefs.voice_enabled is True
        assert prefs.daily_goal_minutes == 60
