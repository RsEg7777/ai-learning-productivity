"""Unit tests for quiz session and scoring service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.services.quiz_generation.quiz_session_service import (
    QuizSession,
    QuizSessionService,
    PerformanceAnalytics,
)
from src.shared.models.quiz import (
    Quiz,
    Question,
    QuestionType,
    DifficultyLevel,
    QuizResult,
)
from src.shared.utils.errors import ContentProcessingError


@pytest.fixture
def sample_quiz():
    """Create a sample quiz for testing."""
    questions = [
        Question(
            id="q1",
            type=QuestionType.MULTIPLE_CHOICE,
            text="What is Python?",
            options=["A snake", "A programming language", "A food", "A concept"],
            correct_answer="A programming language",
            explanation="Python is a high-level programming language.",
            points=1,
            difficulty=DifficultyLevel.EASY,
        ),
        Question(
            id="q2",
            type=QuestionType.TRUE_FALSE,
            text="Python is a compiled language.",
            options=["True", "False"],
            correct_answer="False",
            explanation="Python is an interpreted language.",
            points=1,
            difficulty=DifficultyLevel.MEDIUM,
        ),
        Question(
            id="q3",
            type=QuestionType.FILL_IN_BLANK,
            text="Python emphasizes code _____.",
            options=None,
            correct_answer="readability",
            explanation="Python emphasizes code readability.",
            points=1,
            difficulty=DifficultyLevel.EASY,
        ),
    ]

    return Quiz(
        id="quiz-123",
        content_id="content-123",
        title="Python Basics Quiz",
        questions=questions,
        time_limit=600,
        passing_score=70,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def quiz_session_service():
    """Create a QuizSessionService instance."""
    return QuizSessionService()


@pytest.fixture
def performance_analytics():
    """Create a PerformanceAnalytics instance."""
    return PerformanceAnalytics()


class TestQuizSession:
    """Test suite for QuizSession class."""

    def test_initialization(self, sample_quiz):
        """Test quiz session initialization."""
        session_id = "session-123"
        user_id = "user-456"
        started_at = datetime.utcnow()

        session = QuizSession(
            session_id=session_id,
            quiz=sample_quiz,
            user_id=user_id,
            started_at=started_at,
        )

        assert session.session_id == session_id
        assert session.quiz == sample_quiz
        assert session.user_id == user_id
        assert session.started_at == started_at
        assert session.answers == {}
        assert session.current_question_index == 0
        assert session.completed is False
        assert session.completed_at is None

    def test_get_current_question(self, sample_quiz):
        """Test getting current question."""
        session = QuizSession(
            session_id="session-123",
            quiz=sample_quiz,
            user_id="user-456",
            started_at=datetime.utcnow(),
        )

        # First question
        current = session.get_current_question()
        assert current is not None
        assert current.id == "q1"

        # Move to next question
        session.current_question_index = 1
        current = session.get_current_question()
        assert current.id == "q2"

        # Beyond last question
        session.current_question_index = 10
        current = session.get_current_question()
        assert current is None

    def test_submit_answer(self, sample_quiz):
        """Test submitting an answer."""
        session = QuizSession(
            session_id="session-123",
            quiz=sample_quiz,
            user_id="user-456",
            started_at=datetime.utcnow(),
        )

        # Submit valid answer
        result = session.submit_answer("q1", "A programming language")
        assert result is True
        assert "q1" in session.answers
        assert session.answers["q1"] == "A programming language"

    def test_submit_answer_empty_question_id(self, sample_quiz):
        """Test submitting answer with empty question ID."""
        session = QuizSession(
            session_id="session-123",
            quiz=sample_quiz,
            user_id="user-456",
            started_at=datetime.utcnow(),
        )

        with pytest.raises(ValueError) as exc_info:
            session.submit_answer("", "answer")
        assert "Question ID cannot be empty" in str(exc_info.value)

    def test_submit_answer_empty_answer(self, sample_quiz):
        """Test submitting empty answer."""
        session = QuizSession(
            session_id="session-123",
            quiz=sample_quiz,
            user_id="user-456",
            started_at=datetime.utcnow(),
        )

        with pytest.raises(ValueError) as exc_info:
            session.submit_answer("q1", "")
        assert "Answer cannot be empty" in str(exc_info.value)

    def test_submit_answer_invalid_question(self, sample_quiz):
        """Test submitting answer for invalid question."""
        session = QuizSession(
            session_id="session-123",
            quiz=sample_quiz,
            user_id="user-456",
            started_at=datetime.utcnow(),
        )

        with pytest.raises(ValueError) as exc_info:
            session.submit_answer("invalid-q", "answer")
        assert "not found in quiz" in str(exc_info.value)

    def test_next_question(self, sample_quiz):
        """Test moving to next question."""
        session = QuizSession(
            session_id="session-123",
            quiz=sample_quiz,
            user_id="user-456",
            started_at=datetime.utcnow(),
        )

        # Move to next question
        next_q = session.next_question()
        assert next_q is not None
        assert next_q.id == "q2"
        assert session.current_question_index == 1

        # Move to last question
        next_q = session.next_question()
        assert next_q.id == "q3"

        # Beyond last question
        next_q = session.next_question()
        assert next_q is None

    def test_previous_question(self, sample_quiz):
        """Test moving to previous question."""
        session = QuizSession(
            session_id="session-123",
            quiz=sample_quiz,
            user_id="user-456",
            started_at=datetime.utcnow(),
        )

        # At first question, can't go back
        prev_q = session.previous_question()
        assert prev_q is None

        # Move forward then back
        session.current_question_index = 2
        prev_q = session.previous_question()
        assert prev_q is not None
        assert prev_q.id == "q2"
        assert session.current_question_index == 1

    def test_get_progress(self, sample_quiz):
        """Test getting session progress."""
        session = QuizSession(
            session_id="session-123",
            quiz=sample_quiz,
            user_id="user-456",
            started_at=datetime.utcnow(),
        )

        # No answers yet
        progress = session.get_progress()
        assert progress["session_id"] == "session-123"
        assert progress["total_questions"] == 3
        assert progress["answered_questions"] == 0
        assert progress["progress_percentage"] == 0
        assert progress["completed"] is False

        # Answer some questions
        session.submit_answer("q1", "A programming language")
        session.submit_answer("q2", "False")

        progress = session.get_progress()
        assert progress["answered_questions"] == 2
        assert progress["progress_percentage"] == pytest.approx(66.67, rel=0.1)

    def test_is_complete(self, sample_quiz):
        """Test checking if session is complete."""
        session = QuizSession(
            session_id="session-123",
            quiz=sample_quiz,
            user_id="user-456",
            started_at=datetime.utcnow(),
        )

        # Not complete initially
        assert session.is_complete() is False

        # Answer all questions
        session.submit_answer("q1", "A programming language")
        session.submit_answer("q2", "False")
        session.submit_answer("q3", "readability")

        # Now complete
        assert session.is_complete() is True

    def test_mark_complete(self, sample_quiz):
        """Test marking session as complete."""
        session = QuizSession(
            session_id="session-123",
            quiz=sample_quiz,
            user_id="user-456",
            started_at=datetime.utcnow(),
        )

        assert session.completed is False
        assert session.completed_at is None

        session.mark_complete()

        assert session.completed is True
        assert session.completed_at is not None


class TestQuizSessionService:
    """Test suite for QuizSessionService."""

    def test_initialization(self):
        """Test service initialization."""
        service = QuizSessionService()
        assert service.active_sessions == {}

    def test_start_session(self, quiz_session_service, sample_quiz):
        """Test starting a quiz session."""
        user_id = "user-456"
        session = quiz_session_service.start_session(sample_quiz, user_id)

        assert session is not None
        assert session.quiz == sample_quiz
        assert session.user_id == user_id
        assert session.session_id in quiz_session_service.active_sessions

    def test_start_session_none_quiz(self, quiz_session_service):
        """Test starting session with None quiz."""
        with pytest.raises(ContentProcessingError):
            quiz_session_service.start_session(None, "user-456")

    def test_start_session_empty_user_id(self, quiz_session_service, sample_quiz):
        """Test starting session with empty user ID."""
        with pytest.raises(ContentProcessingError):
            quiz_session_service.start_session(sample_quiz, "")

    def test_start_session_no_questions(self, quiz_session_service):
        """Test starting session with quiz that has no questions."""
        empty_quiz = Quiz(
            id="quiz-empty",
            content_id="content-123",
            title="Empty Quiz",
            questions=[],
            time_limit=600,
            passing_score=70,
            created_at=datetime.utcnow(),
        )

        with pytest.raises(ContentProcessingError):
            quiz_session_service.start_session(empty_quiz, "user-456")

    def test_get_session(self, quiz_session_service, sample_quiz):
        """Test getting an active session."""
        user_id = "user-456"
        session = quiz_session_service.start_session(sample_quiz, user_id)

        # Get existing session
        retrieved = quiz_session_service.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id

        # Get non-existent session
        retrieved = quiz_session_service.get_session("non-existent")
        assert retrieved is None

    def test_submit_answer(self, quiz_session_service, sample_quiz):
        """Test submitting an answer."""
        user_id = "user-456"
        session = quiz_session_service.start_session(sample_quiz, user_id)

        # Submit correct answer
        feedback = quiz_session_service.submit_answer(
            session.session_id,
            "q1",
            "A programming language",
        )

        assert feedback["is_correct"] is True
        assert feedback["correct_answer"] == "A programming language"
        assert feedback["points_earned"] == 1
        assert "explanation" in feedback

    def test_submit_answer_incorrect(self, quiz_session_service, sample_quiz):
        """Test submitting an incorrect answer."""
        user_id = "user-456"
        session = quiz_session_service.start_session(sample_quiz, user_id)

        # Submit incorrect answer
        feedback = quiz_session_service.submit_answer(
            session.session_id,
            "q1",
            "A snake",
        )

        assert feedback["is_correct"] is False
        assert feedback["correct_answer"] == "A programming language"
        assert feedback["points_earned"] == 0

    def test_submit_answer_invalid_session(self, quiz_session_service):
        """Test submitting answer for invalid session."""
        with pytest.raises(ContentProcessingError):
            quiz_session_service.submit_answer("invalid-session", "q1", "answer")

    def test_check_answer_multiple_choice(self, quiz_session_service):
        """Test answer checking for multiple choice questions."""
        question = Question(
            id="q1",
            type=QuestionType.MULTIPLE_CHOICE,
            text="What is Python?",
            options=["A", "B", "C", "D"],
            correct_answer="B",
            explanation="Test",
            points=1,
            difficulty=DifficultyLevel.EASY,
        )

        # Correct answer (case-insensitive)
        assert quiz_session_service._check_answer(question, "B") is True
        assert quiz_session_service._check_answer(question, "b") is True

        # Incorrect answer
        assert quiz_session_service._check_answer(question, "A") is False

    def test_check_answer_true_false(self, quiz_session_service):
        """Test answer checking for true/false questions."""
        question = Question(
            id="q1",
            type=QuestionType.TRUE_FALSE,
            text="Python is interpreted.",
            options=["True", "False"],
            correct_answer="True",
            explanation="Test",
            points=1,
            difficulty=DifficultyLevel.EASY,
        )

        # Correct answer (case-insensitive)
        assert quiz_session_service._check_answer(question, "True") is True
        assert quiz_session_service._check_answer(question, "true") is True
        assert quiz_session_service._check_answer(question, "TRUE") is True

        # Incorrect answer
        assert quiz_session_service._check_answer(question, "False") is False

    def test_check_answer_fill_in_blank(self, quiz_session_service):
        """Test answer checking for fill-in-blank questions."""
        question = Question(
            id="q1",
            type=QuestionType.FILL_IN_BLANK,
            text="Python emphasizes _____.",
            options=None,
            correct_answer="readability",
            explanation="Test",
            points=1,
            difficulty=DifficultyLevel.EASY,
        )

        # Exact match (case-insensitive)
        assert quiz_session_service._check_answer(question, "readability") is True
        assert quiz_session_service._check_answer(question, "Readability") is True

        # Contains correct answer
        assert quiz_session_service._check_answer(question, "code readability") is True

        # Partial match (if long enough)
        assert quiz_session_service._check_answer(question, "read") is True

        # Incorrect answer
        assert quiz_session_service._check_answer(question, "speed") is False

    def test_complete_session(self, quiz_session_service, sample_quiz):
        """Test completing a quiz session."""
        user_id = "user-456"
        session = quiz_session_service.start_session(sample_quiz, user_id)

        # Answer all questions
        quiz_session_service.submit_answer(session.session_id, "q1", "A programming language")
        quiz_session_service.submit_answer(session.session_id, "q2", "False")
        quiz_session_service.submit_answer(session.session_id, "q3", "readability")

        # Complete session
        result = quiz_session_service.complete_session(session.session_id)

        assert isinstance(result, QuizResult)
        assert result.quiz_id == sample_quiz.id
        assert result.user_id == user_id
        assert result.score == 100  # All correct
        assert result.correct_count == 3
        assert result.total_questions == 3
        assert result.time_taken is not None

        # Session should be removed from active sessions
        assert session.session_id not in quiz_session_service.active_sessions

    def test_complete_session_partial_score(self, quiz_session_service, sample_quiz):
        """Test completing session with partial score."""
        user_id = "user-456"
        session = quiz_session_service.start_session(sample_quiz, user_id)

        # Answer with some incorrect
        quiz_session_service.submit_answer(session.session_id, "q1", "A programming language")  # Correct
        quiz_session_service.submit_answer(session.session_id, "q2", "True")  # Incorrect
        quiz_session_service.submit_answer(session.session_id, "q3", "readability")  # Correct

        result = quiz_session_service.complete_session(session.session_id)

        assert result.score == 66  # 2 out of 3 correct
        assert result.correct_count == 2
        assert result.total_questions == 3

    def test_complete_session_invalid_session(self, quiz_session_service):
        """Test completing invalid session."""
        with pytest.raises(ContentProcessingError):
            quiz_session_service.complete_session("invalid-session")

    def test_complete_session_already_completed(self, quiz_session_service, sample_quiz):
        """Test completing already completed session."""
        user_id = "user-456"
        session = quiz_session_service.start_session(sample_quiz, user_id)

        # Answer and complete
        quiz_session_service.submit_answer(session.session_id, "q1", "A programming language")
        quiz_session_service.submit_answer(session.session_id, "q2", "False")
        quiz_session_service.submit_answer(session.session_id, "q3", "readability")
        
        quiz_session_service.complete_session(session.session_id)

        # Try to complete again - should fail because session is removed
        with pytest.raises(ContentProcessingError):
            quiz_session_service.complete_session(session.session_id)

    def test_calculate_score(self, quiz_session_service, sample_quiz):
        """Test score calculation."""
        user_id = "user-456"
        session = quiz_session_service.start_session(sample_quiz, user_id)

        # Answer all correctly
        session.submit_answer("q1", "A programming language")
        session.submit_answer("q2", "False")
        session.submit_answer("q3", "readability")

        score_data = quiz_session_service._calculate_score(session)

        assert score_data["correct_count"] == 3
        assert score_data["total_questions"] == 3
        assert score_data["total_points"] == 3
        assert score_data["max_points"] == 3
        assert score_data["score_percentage"] == 100

    def test_get_session_progress(self, quiz_session_service, sample_quiz):
        """Test getting session progress."""
        user_id = "user-456"
        session = quiz_session_service.start_session(sample_quiz, user_id)

        # Get initial progress
        progress = quiz_session_service.get_session_progress(session.session_id)

        assert progress["total_questions"] == 3
        assert progress["answered_questions"] == 0
        assert progress["completed"] is False

        # Answer some questions
        quiz_session_service.submit_answer(session.session_id, "q1", "A programming language")

        progress = quiz_session_service.get_session_progress(session.session_id)
        assert progress["answered_questions"] == 1

    def test_get_session_progress_invalid_session(self, quiz_session_service):
        """Test getting progress for invalid session."""
        with pytest.raises(ContentProcessingError):
            quiz_session_service.get_session_progress("invalid-session")

    def test_abandon_session(self, quiz_session_service, sample_quiz):
        """Test abandoning a session."""
        user_id = "user-456"
        session = quiz_session_service.start_session(sample_quiz, user_id)

        assert session.session_id in quiz_session_service.active_sessions

        # Abandon session
        quiz_session_service.abandon_session(session.session_id)

        assert session.session_id not in quiz_session_service.active_sessions

    def test_abandon_nonexistent_session(self, quiz_session_service):
        """Test abandoning non-existent session."""
        # Should not raise error
        quiz_session_service.abandon_session("non-existent")


class TestPerformanceAnalytics:
    """Test suite for PerformanceAnalytics."""

    def test_initialization(self):
        """Test analytics initialization."""
        analytics = PerformanceAnalytics()
        assert analytics.quiz_results == []

    def test_record_result(self, performance_analytics):
        """Test recording a quiz result."""
        result = QuizResult(
            quiz_id="quiz-123",
            user_id="user-456",
            answers={"q1": "answer1"},
            score=85,
            correct_count=17,
            total_questions=20,
            time_taken=300,
            completed_at=datetime.utcnow(),
        )

        performance_analytics.record_result(result)

        assert len(performance_analytics.quiz_results) == 1
        assert performance_analytics.quiz_results[0] == result

    def test_get_user_performance_no_results(self, performance_analytics):
        """Test getting performance for user with no results."""
        performance = performance_analytics.get_user_performance("user-456")

        assert performance["total_quizzes"] == 0
        assert performance["average_score"] == 0
        assert performance["total_questions_answered"] == 0
        assert performance["total_correct"] == 0
        assert performance["accuracy_rate"] == 0
        assert performance["average_time"] == 0
        assert performance["best_score"] == 0
        assert performance["recent_scores"] == []

    def test_get_user_performance_with_results(self, performance_analytics):
        """Test getting performance for user with results."""
        # Add multiple results
        results = [
            QuizResult(
                quiz_id="quiz-1",
                user_id="user-456",
                answers={},
                score=80,
                correct_count=8,
                total_questions=10,
                time_taken=300,
                completed_at=datetime.utcnow(),
            ),
            QuizResult(
                quiz_id="quiz-2",
                user_id="user-456",
                answers={},
                score=90,
                correct_count=9,
                total_questions=10,
                time_taken=250,
                completed_at=datetime.utcnow(),
            ),
            QuizResult(
                quiz_id="quiz-3",
                user_id="user-456",
                answers={},
                score=70,
                correct_count=7,
                total_questions=10,
                time_taken=350,
                completed_at=datetime.utcnow(),
            ),
        ]

        for result in results:
            performance_analytics.record_result(result)

        performance = performance_analytics.get_user_performance("user-456")

        assert performance["total_quizzes"] == 3
        assert performance["average_score"] == 80.0  # (80 + 90 + 70) / 3
        assert performance["total_questions_answered"] == 30
        assert performance["total_correct"] == 24
        assert performance["accuracy_rate"] == 80.0  # 24/30 * 100
        assert performance["average_time"] == 300.0  # (300 + 250 + 350) / 3
        assert performance["best_score"] == 90
        assert len(performance["recent_scores"]) == 3

    def test_get_quiz_statistics_no_attempts(self, performance_analytics):
        """Test getting statistics for quiz with no attempts."""
        stats = performance_analytics.get_quiz_statistics("quiz-123")

        assert stats["total_attempts"] == 0
        assert stats["average_score"] == 0
        assert stats["pass_rate"] == 0
        assert stats["average_time"] == 0
        assert stats["score_distribution"] == {}

    def test_get_quiz_statistics_with_attempts(self, performance_analytics):
        """Test getting statistics for quiz with attempts."""
        # Add results for same quiz
        results = [
            QuizResult(
                quiz_id="quiz-123",
                user_id="user-1",
                answers={},
                score=85,
                correct_count=17,
                total_questions=20,
                time_taken=300,
                completed_at=datetime.utcnow(),
            ),
            QuizResult(
                quiz_id="quiz-123",
                user_id="user-2",
                answers={},
                score=65,
                correct_count=13,
                total_questions=20,
                time_taken=400,
                completed_at=datetime.utcnow(),
            ),
            QuizResult(
                quiz_id="quiz-123",
                user_id="user-3",
                answers={},
                score=75,
                correct_count=15,
                total_questions=20,
                time_taken=350,
                completed_at=datetime.utcnow(),
            ),
        ]

        for result in results:
            performance_analytics.record_result(result)

        stats = performance_analytics.get_quiz_statistics("quiz-123")

        assert stats["total_attempts"] == 3
        assert stats["average_score"] == 75.0  # (85 + 65 + 75) / 3
        assert stats["pass_rate"] == pytest.approx(66.67, rel=0.1)  # 2 out of 3 passed (>= 70%)
        assert stats["average_time"] == pytest.approx(350.0, rel=0.1)
        assert "60-69%" in stats["score_distribution"]
        assert "70-79%" in stats["score_distribution"]
        assert "80-89%" in stats["score_distribution"]

    def test_get_overall_statistics_no_results(self, performance_analytics):
        """Test getting overall statistics with no results."""
        stats = performance_analytics.get_overall_statistics()

        assert stats["total_quizzes_completed"] == 0
        assert stats["total_questions_answered"] == 0
        assert stats["overall_accuracy"] == 0
        assert stats["unique_users"] == 0
        assert stats["average_score"] == 0

    def test_get_overall_statistics_with_results(self, performance_analytics):
        """Test getting overall statistics with results."""
        # Add results from multiple users
        results = [
            QuizResult(
                quiz_id="quiz-1",
                user_id="user-1",
                answers={},
                score=80,
                correct_count=8,
                total_questions=10,
                time_taken=300,
                completed_at=datetime.utcnow(),
            ),
            QuizResult(
                quiz_id="quiz-2",
                user_id="user-2",
                answers={},
                score=90,
                correct_count=9,
                total_questions=10,
                time_taken=250,
                completed_at=datetime.utcnow(),
            ),
            QuizResult(
                quiz_id="quiz-3",
                user_id="user-1",
                answers={},
                score=70,
                correct_count=7,
                total_questions=10,
                time_taken=350,
                completed_at=datetime.utcnow(),
            ),
        ]

        for result in results:
            performance_analytics.record_result(result)

        stats = performance_analytics.get_overall_statistics()

        assert stats["total_quizzes_completed"] == 3
        assert stats["total_questions_answered"] == 30
        assert stats["overall_accuracy"] == 80.0  # 24/30 * 100
        assert stats["unique_users"] == 2  # user-1 and user-2
        assert stats["average_score"] == 80.0  # (80 + 90 + 70) / 3

    def test_recent_scores_ordering(self, performance_analytics):
        """Test that recent scores are ordered by completion time."""
        # Add results with different timestamps
        base_time = datetime.utcnow()
        
        results = [
            QuizResult(
                quiz_id="quiz-1",
                user_id="user-456",
                answers={},
                score=80,
                correct_count=8,
                total_questions=10,
                time_taken=300,
                completed_at=base_time - timedelta(hours=3),
            ),
            QuizResult(
                quiz_id="quiz-2",
                user_id="user-456",
                answers={},
                score=90,
                correct_count=9,
                total_questions=10,
                time_taken=250,
                completed_at=base_time - timedelta(hours=1),
            ),
            QuizResult(
                quiz_id="quiz-3",
                user_id="user-456",
                answers={},
                score=70,
                correct_count=7,
                total_questions=10,
                time_taken=350,
                completed_at=base_time - timedelta(hours=2),
            ),
        ]

        for result in results:
            performance_analytics.record_result(result)

        performance = performance_analytics.get_user_performance("user-456")
        recent = performance["recent_scores"]

        # Should be ordered by most recent first
        assert recent[0]["quiz_id"] == "quiz-2"  # 1 hour ago
        assert recent[1]["quiz_id"] == "quiz-3"  # 2 hours ago
        assert recent[2]["quiz_id"] == "quiz-1"  # 3 hours ago

    def test_recent_scores_limit(self, performance_analytics):
        """Test that recent scores are limited to 10."""
        # Add 15 results
        for i in range(15):
            result = QuizResult(
                quiz_id=f"quiz-{i}",
                user_id="user-456",
                answers={},
                score=80,
                correct_count=8,
                total_questions=10,
                time_taken=300,
                completed_at=datetime.utcnow() - timedelta(hours=i),
            )
            performance_analytics.record_result(result)

        performance = performance_analytics.get_user_performance("user-456")
        recent = performance["recent_scores"]

        # Should only return 10 most recent
        assert len(recent) == 10
