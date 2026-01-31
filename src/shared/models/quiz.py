"""Quiz and flashcard data models."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """Types of quiz questions."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_IN_BLANK = "fill_in_blank"
    SHORT_ANSWER = "short_answer"


class DifficultyLevel(str, Enum):
    """Difficulty levels for questions and flashcards."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Question(BaseModel):
    """A quiz question."""
    id: str = Field(..., description="Unique question identifier")
    type: QuestionType = Field(..., description="Question type")
    text: str = Field(..., description="Question text")
    options: Optional[List[str]] = Field(None, description="Answer options (for multiple choice)")
    correct_answer: str = Field(..., description="Correct answer")
    explanation: str = Field(..., description="Explanation of the answer")
    points: int = Field(default=1, ge=1, description="Points awarded for correct answer")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM, description="Difficulty level")


class Quiz(BaseModel):
    """A quiz generated from content."""
    id: str = Field(..., description="Unique quiz identifier")
    content_id: str = Field(..., description="Source content ID")
    title: str = Field(..., description="Quiz title")
    questions: List[Question] = Field(..., description="Quiz questions")
    time_limit: Optional[int] = Field(None, description="Time limit in seconds")
    passing_score: int = Field(default=70, ge=0, le=100, description="Passing score percentage")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class SpacedRepetitionData(BaseModel):
    """Data for spaced repetition algorithm."""
    ease_factor: float = Field(default=2.5, ge=1.3, description="Ease factor for scheduling")
    interval: int = Field(default=1, ge=0, description="Current interval in days")
    repetitions: int = Field(default=0, ge=0, description="Number of successful repetitions")
    last_reviewed: Optional[datetime] = Field(None, description="Last review timestamp")
    next_review: Optional[datetime] = Field(None, description="Next scheduled review")


class Flashcard(BaseModel):
    """A flashcard for learning."""
    id: str = Field(..., description="Unique flashcard identifier")
    content_id: str = Field(..., description="Source content ID")
    question: str = Field(..., description="Question/front of card")
    answer: str = Field(..., description="Answer/back of card")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.MEDIUM, description="Difficulty level")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    repetition_data: SpacedRepetitionData = Field(
        default_factory=SpacedRepetitionData,
        description="Spaced repetition scheduling data"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class QuizResult(BaseModel):
    """Result of a completed quiz."""
    quiz_id: str = Field(..., description="Quiz identifier")
    user_id: str = Field(..., description="User identifier")
    answers: Dict[str, str] = Field(..., description="User answers (question_id -> answer)")
    score: int = Field(..., ge=0, le=100, description="Score percentage")
    correct_count: int = Field(..., ge=0, description="Number of correct answers")
    total_questions: int = Field(..., ge=1, description="Total number of questions")
    time_taken: Optional[int] = Field(None, description="Time taken in seconds")
    completed_at: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")


class RepetitionSchedule(BaseModel):
    """Schedule for next flashcard review."""
    flashcard_id: str = Field(..., description="Flashcard identifier")
    next_review: datetime = Field(..., description="Next review date/time")
    interval_days: int = Field(..., ge=0, description="Interval in days")
    ease_factor: float = Field(..., ge=1.3, description="Current ease factor")
