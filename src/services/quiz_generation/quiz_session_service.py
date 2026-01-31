"""Quiz session management and scoring service."""

import logging
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ...shared.models.quiz import (
    Quiz,
    Question,
    QuestionType,
    QuizResult,
)
from ...shared.utils.errors import ContentProcessingError

logger = logging.getLogger(__name__)


class QuizSession:
    """
    Represents an active quiz session.
    
    Manages the state of a quiz being taken by a user, including:
    - Current question tracking
    - Answer recording
    - Time tracking
    - Session metadata
    """

    def __init__(
        self,
        session_id: str,
        quiz: Quiz,
        user_id: str,
        started_at: datetime,
    ):
        """
        Initialize a quiz session.

        Args:
            session_id: Unique session identifier
            quiz: Quiz being taken
            user_id: User taking the quiz
            started_at: Session start timestamp
        """
        self.session_id = session_id
        self.quiz = quiz
        self.user_id = user_id
        self.started_at = started_at
        self.answers: Dict[str, str] = {}  # question_id -> user_answer
        self.current_question_index = 0
        self.completed = False
        self.completed_at: Optional[datetime] = None

    def get_current_question(self) -> Optional[Question]:
        """
        Get the current question in the quiz.

        Returns:
            Current Question object or None if quiz is complete
        """
        if self.current_question_index < len(self.quiz.questions):
            return self.quiz.questions[self.current_question_index]
        return None

    def submit_answer(self, question_id: str, answer: str) -> bool:
        """
        Submit an answer for a question.

        Args:
            question_id: Question identifier
            answer: User's answer

        Returns:
            True if answer was recorded successfully

        Raises:
            ValueError: If question_id is invalid or answer is empty
        """
        if not question_id:
            raise ValueError("Question ID cannot be empty")
        
        if not answer:
            raise ValueError("Answer cannot be empty")

        # Verify question exists in quiz
        question_ids = [q.id for q in self.quiz.questions]
        if question_id not in question_ids:
            raise ValueError(f"Question {question_id} not found in quiz")

        # Record answer
        self.answers[question_id] = answer
        logger.debug(f"Recorded answer for question {question_id} in session {self.session_id}")
        
        return True

    def next_question(self) -> Optional[Question]:
        """
        Move to the next question.

        Returns:
            Next Question object or None if no more questions
        """
        self.current_question_index += 1
        return self.get_current_question()

    def previous_question(self) -> Optional[Question]:
        """
        Move to the previous question.

        Returns:
            Previous Question object or None if at first question
        """
        if self.current_question_index > 0:
            self.current_question_index -= 1
            return self.get_current_question()
        return None

    def get_progress(self) -> Dict[str, any]:
        """
        Get session progress information.

        Returns:
            Dictionary with progress metrics
        """
        total_questions = len(self.quiz.questions)
        answered_questions = len(self.answers)
        
        return {
            "session_id": self.session_id,
            "total_questions": total_questions,
            "answered_questions": answered_questions,
            "current_question_index": self.current_question_index,
            "progress_percentage": (answered_questions / total_questions * 100) if total_questions > 0 else 0,
            "completed": self.completed,
            "time_elapsed_seconds": (datetime.utcnow() - self.started_at).total_seconds(),
        }

    def is_complete(self) -> bool:
        """
        Check if all questions have been answered.

        Returns:
            True if all questions answered
        """
        return len(self.answers) == len(self.quiz.questions)

    def mark_complete(self) -> None:
        """Mark the session as completed."""
        self.completed = True
        self.completed_at = datetime.utcnow()


class QuizSessionService:
    """Service for managing quiz sessions and scoring."""

    def __init__(self):
        """Initialize quiz session service."""
        self.active_sessions: Dict[str, QuizSession] = {}
        logger.info("Initialized QuizSessionService")

    def start_session(self, quiz: Quiz, user_id: str) -> QuizSession:
        """
        Start a new quiz session.

        Args:
            quiz: Quiz to take
            user_id: User taking the quiz

        Returns:
            QuizSession object

        Raises:
            ContentProcessingError: If session creation fails
        """
        try:
            if not quiz:
                raise ValueError("Quiz cannot be None")
            
            if not user_id:
                raise ValueError("User ID cannot be empty")

            if not quiz.questions:
                raise ValueError("Quiz must have at least one question")

            session_id = str(uuid.uuid4())
            session = QuizSession(
                session_id=session_id,
                quiz=quiz,
                user_id=user_id,
                started_at=datetime.utcnow(),
            )

            self.active_sessions[session_id] = session
            
            logger.info(
                f"Started quiz session {session_id} for user {user_id} "
                f"(quiz: {quiz.id}, questions: {len(quiz.questions)})"
            )

            return session

        except Exception as e:
            logger.error(f"Error starting quiz session: {e}")
            raise ContentProcessingError(
                message=f"Failed to start quiz session: {str(e)}",
                content_type="quiz_session",
            )

    def get_session(self, session_id: str) -> Optional[QuizSession]:
        """
        Get an active quiz session.

        Args:
            session_id: Session identifier

        Returns:
            QuizSession object or None if not found
        """
        return self.active_sessions.get(session_id)

    def submit_answer(
        self,
        session_id: str,
        question_id: str,
        answer: str,
    ) -> Dict[str, any]:
        """
        Submit an answer for a question in a session.

        Provides immediate feedback on the answer.

        Args:
            session_id: Session identifier
            question_id: Question identifier
            answer: User's answer

        Returns:
            Dictionary with feedback including:
            - is_correct: Whether answer is correct
            - correct_answer: The correct answer
            - explanation: Explanation of the answer
            - points_earned: Points earned for this question

        Raises:
            ContentProcessingError: If submission fails
        """
        try:
            session = self.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Submit answer to session
            session.submit_answer(question_id, answer)

            # Get the question
            question = next((q for q in session.quiz.questions if q.id == question_id), None)
            if not question:
                raise ValueError(f"Question {question_id} not found")

            # Check if answer is correct
            is_correct = self._check_answer(question, answer)

            # Prepare feedback
            feedback = {
                "question_id": question_id,
                "is_correct": is_correct,
                "correct_answer": question.correct_answer,
                "explanation": question.explanation,
                "points_earned": question.points if is_correct else 0,
                "user_answer": answer,
            }

            logger.info(
                f"Answer submitted for session {session_id}, question {question_id}: "
                f"{'correct' if is_correct else 'incorrect'}"
            )

            return feedback

        except ValueError as e:
            logger.error(f"Validation error submitting answer: {e}")
            raise ContentProcessingError(
                message=str(e),
                content_type="quiz_session",
            )
        except Exception as e:
            logger.error(f"Error submitting answer: {e}")
            raise ContentProcessingError(
                message=f"Failed to submit answer: {str(e)}",
                content_type="quiz_session",
            )

    def _check_answer(self, question: Question, user_answer: str) -> bool:
        """
        Check if a user's answer is correct.

        Handles different question types with appropriate comparison logic.

        Args:
            question: Question object
            user_answer: User's answer

        Returns:
            True if answer is correct
        """
        correct_answer = question.correct_answer.strip()
        user_answer = user_answer.strip()

        # For multiple choice and true/false, exact match (case-insensitive)
        if question.type in [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE]:
            return user_answer.lower() == correct_answer.lower()

        # For fill-in-blank, more flexible matching
        if question.type == QuestionType.FILL_IN_BLANK:
            # Case-insensitive comparison
            if user_answer.lower() == correct_answer.lower():
                return True
            
            # Check if user answer contains the correct answer
            if correct_answer.lower() in user_answer.lower():
                return True
            
            # Check if correct answer contains user answer (for partial credit)
            if user_answer.lower() in correct_answer.lower() and len(user_answer) > 3:
                return True

            return False

        # For short answer, case-insensitive exact match
        return user_answer.lower() == correct_answer.lower()

    def complete_session(self, session_id: str) -> QuizResult:
        """
        Complete a quiz session and calculate final score.

        Args:
            session_id: Session identifier

        Returns:
            QuizResult object with final score and statistics

        Raises:
            ContentProcessingError: If completion fails
        """
        try:
            session = self.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            if session.completed:
                raise ValueError(f"Session {session_id} is already completed")

            # Calculate score
            score_data = self._calculate_score(session)

            # Mark session as complete
            session.mark_complete()

            # Calculate time taken
            time_taken = int((session.completed_at - session.started_at).total_seconds())

            # Create quiz result
            result = QuizResult(
                quiz_id=session.quiz.id,
                user_id=session.user_id,
                answers=session.answers,
                score=score_data["score_percentage"],
                correct_count=score_data["correct_count"],
                total_questions=score_data["total_questions"],
                time_taken=time_taken,
                completed_at=session.completed_at,
            )

            logger.info(
                f"Completed quiz session {session_id}: "
                f"score={result.score}%, correct={result.correct_count}/{result.total_questions}, "
                f"time={time_taken}s"
            )

            # Remove from active sessions
            del self.active_sessions[session_id]

            return result

        except ValueError as e:
            logger.error(f"Validation error completing session: {e}")
            raise ContentProcessingError(
                message=str(e),
                content_type="quiz_session",
            )
        except Exception as e:
            logger.error(f"Error completing session: {e}")
            raise ContentProcessingError(
                message=f"Failed to complete session: {str(e)}",
                content_type="quiz_session",
            )

    def _calculate_score(self, session: QuizSession) -> Dict[str, any]:
        """
        Calculate the score for a quiz session.

        Args:
            session: QuizSession object

        Returns:
            Dictionary with score data:
            - correct_count: Number of correct answers
            - total_questions: Total number of questions
            - total_points: Total points earned
            - max_points: Maximum possible points
            - score_percentage: Score as percentage
        """
        correct_count = 0
        total_points = 0
        max_points = 0

        for question in session.quiz.questions:
            max_points += question.points
            
            # Check if question was answered
            if question.id in session.answers:
                user_answer = session.answers[question.id]
                if self._check_answer(question, user_answer):
                    correct_count += 1
                    total_points += question.points

        total_questions = len(session.quiz.questions)
        
        # Calculate percentage score
        score_percentage = int((total_points / max_points * 100)) if max_points > 0 else 0

        return {
            "correct_count": correct_count,
            "total_questions": total_questions,
            "total_points": total_points,
            "max_points": max_points,
            "score_percentage": score_percentage,
        }

    def get_session_progress(self, session_id: str) -> Dict[str, any]:
        """
        Get progress information for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with progress information

        Raises:
            ContentProcessingError: If session not found
        """
        try:
            session = self.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            return session.get_progress()

        except Exception as e:
            logger.error(f"Error getting session progress: {e}")
            raise ContentProcessingError(
                message=f"Failed to get session progress: {str(e)}",
                content_type="quiz_session",
            )

    def abandon_session(self, session_id: str) -> None:
        """
        Abandon an active quiz session.

        Args:
            session_id: Session identifier

        Raises:
            ContentProcessingError: If abandonment fails
        """
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                logger.info(
                    f"Abandoning quiz session {session_id} for user {session.user_id} "
                    f"(answered {len(session.answers)}/{len(session.quiz.questions)} questions)"
                )
                del self.active_sessions[session_id]
            else:
                logger.warning(f"Attempted to abandon non-existent session {session_id}")

        except Exception as e:
            logger.error(f"Error abandoning session: {e}")
            raise ContentProcessingError(
                message=f"Failed to abandon session: {str(e)}",
                content_type="quiz_session",
            )


class PerformanceAnalytics:
    """Service for tracking and analyzing quiz performance."""

    def __init__(self):
        """Initialize performance analytics service."""
        self.quiz_results: List[QuizResult] = []
        logger.info("Initialized PerformanceAnalytics")

    def record_result(self, result: QuizResult) -> None:
        """
        Record a quiz result for analytics.

        Args:
            result: QuizResult object
        """
        self.quiz_results.append(result)
        logger.debug(f"Recorded quiz result for user {result.user_id}, quiz {result.quiz_id}")

    def get_user_performance(self, user_id: str) -> Dict[str, any]:
        """
        Get performance analytics for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with performance metrics:
            - total_quizzes: Total quizzes completed
            - average_score: Average score percentage
            - total_questions_answered: Total questions answered
            - total_correct: Total correct answers
            - accuracy_rate: Overall accuracy percentage
            - average_time: Average time per quiz in seconds
            - best_score: Highest score achieved
            - recent_scores: List of recent scores
        """
        user_results = [r for r in self.quiz_results if r.user_id == user_id]

        if not user_results:
            return {
                "total_quizzes": 0,
                "average_score": 0,
                "total_questions_answered": 0,
                "total_correct": 0,
                "accuracy_rate": 0,
                "average_time": 0,
                "best_score": 0,
                "recent_scores": [],
            }

        total_quizzes = len(user_results)
        total_questions = sum(r.total_questions for r in user_results)
        total_correct = sum(r.correct_count for r in user_results)
        total_time = sum(r.time_taken for r in user_results if r.time_taken)
        
        average_score = sum(r.score for r in user_results) / total_quizzes
        accuracy_rate = (total_correct / total_questions * 100) if total_questions > 0 else 0
        average_time = total_time / total_quizzes if total_quizzes > 0 else 0
        best_score = max(r.score for r in user_results)
        
        # Get recent scores (last 10)
        recent_results = sorted(user_results, key=lambda r: r.completed_at, reverse=True)[:10]
        recent_scores = [
            {
                "quiz_id": r.quiz_id,
                "score": r.score,
                "correct": r.correct_count,
                "total": r.total_questions,
                "completed_at": r.completed_at.isoformat(),
            }
            for r in recent_results
        ]

        return {
            "total_quizzes": total_quizzes,
            "average_score": round(average_score, 2),
            "total_questions_answered": total_questions,
            "total_correct": total_correct,
            "accuracy_rate": round(accuracy_rate, 2),
            "average_time": round(average_time, 2),
            "best_score": best_score,
            "recent_scores": recent_scores,
        }

    def get_quiz_statistics(self, quiz_id: str) -> Dict[str, any]:
        """
        Get statistics for a specific quiz.

        Args:
            quiz_id: Quiz identifier

        Returns:
            Dictionary with quiz statistics:
            - total_attempts: Total number of attempts
            - average_score: Average score across all attempts
            - pass_rate: Percentage of attempts that passed
            - average_time: Average completion time
            - score_distribution: Distribution of scores
        """
        quiz_results = [r for r in self.quiz_results if r.quiz_id == quiz_id]

        if not quiz_results:
            return {
                "total_attempts": 0,
                "average_score": 0,
                "pass_rate": 0,
                "average_time": 0,
                "score_distribution": {},
            }

        total_attempts = len(quiz_results)
        average_score = sum(r.score for r in quiz_results) / total_attempts
        
        # Assuming passing score is 70% (could be retrieved from quiz object)
        passing_attempts = sum(1 for r in quiz_results if r.score >= 70)
        pass_rate = (passing_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        total_time = sum(r.time_taken for r in quiz_results if r.time_taken)
        average_time = total_time / total_attempts if total_attempts > 0 else 0

        # Score distribution (grouped by 10% ranges)
        score_distribution = {}
        for result in quiz_results:
            bucket = (result.score // 10) * 10
            bucket_key = f"{bucket}-{bucket + 9}%"
            score_distribution[bucket_key] = score_distribution.get(bucket_key, 0) + 1

        return {
            "total_attempts": total_attempts,
            "average_score": round(average_score, 2),
            "pass_rate": round(pass_rate, 2),
            "average_time": round(average_time, 2),
            "score_distribution": score_distribution,
        }

    def get_overall_statistics(self) -> Dict[str, any]:
        """
        Get overall system statistics.

        Returns:
            Dictionary with overall statistics:
            - total_quizzes_completed: Total quizzes completed
            - total_questions_answered: Total questions answered
            - overall_accuracy: Overall accuracy rate
            - unique_users: Number of unique users
            - average_score: Average score across all quizzes
        """
        if not self.quiz_results:
            return {
                "total_quizzes_completed": 0,
                "total_questions_answered": 0,
                "overall_accuracy": 0,
                "unique_users": 0,
                "average_score": 0,
            }

        total_quizzes = len(self.quiz_results)
        total_questions = sum(r.total_questions for r in self.quiz_results)
        total_correct = sum(r.correct_count for r in self.quiz_results)
        unique_users = len(set(r.user_id for r in self.quiz_results))
        average_score = sum(r.score for r in self.quiz_results) / total_quizzes

        overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0

        return {
            "total_quizzes_completed": total_quizzes,
            "total_questions_answered": total_questions,
            "overall_accuracy": round(overall_accuracy, 2),
            "unique_users": unique_users,
            "average_score": round(average_score, 2),
        }
