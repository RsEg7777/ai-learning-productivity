"""Unit tests for spaced repetition service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.services.quiz_generation.spaced_repetition_service import (
    SpacedRepetitionService,
    ReviewQuality,
)
from src.shared.models.quiz import (
    Flashcard,
    SpacedRepetitionData,
    DifficultyLevel,
)
from src.shared.utils.errors import ContentProcessingError


@pytest.fixture
def spaced_repetition_service():
    """Create a spaced repetition service instance."""
    return SpacedRepetitionService()


@pytest.fixture
def sample_flashcard():
    """Create a sample flashcard."""
    return Flashcard(
        id="card-123",
        content_id="content-456",
        question="What is Python?",
        answer="A high-level programming language",
        difficulty=DifficultyLevel.MEDIUM,
        tags=["programming", "python"],
        repetition_data=SpacedRepetitionData(),
        created_at=datetime.utcnow(),
    )


class TestSpacedRepetitionService:
    """Test suite for SpacedRepetitionService."""

    def test_initialization(self, spaced_repetition_service):
        """Test service initialization."""
        assert spaced_repetition_service is not None
        assert spaced_repetition_service.performance_history == {}
        assert spaced_repetition_service.MIN_EASE_FACTOR == 1.3
        assert spaced_repetition_service.DEFAULT_EASE_FACTOR == 2.5

    def test_calculate_next_review_first_success(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test calculating next review for first successful review."""
        user_id = "user-123"
        quality = ReviewQuality.PERFECT

        schedule = spaced_repetition_service.calculate_next_review(
            flashcard=sample_flashcard,
            user_id=user_id,
            quality=quality,
        )

        # Verify schedule
        assert schedule.flashcard_id == sample_flashcard.id
        assert schedule.interval_days == 1  # First review interval
        assert schedule.ease_factor >= 2.5  # Should increase from default

        # Verify flashcard data updated
        assert sample_flashcard.repetition_data.repetitions == 1
        assert sample_flashcard.repetition_data.interval == 1
        assert sample_flashcard.repetition_data.last_reviewed is not None
        assert sample_flashcard.repetition_data.next_review is not None

    def test_calculate_next_review_second_success(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test calculating next review for second successful review."""
        user_id = "user-123"
        
        # First review
        sample_flashcard.repetition_data.repetitions = 1
        sample_flashcard.repetition_data.interval = 1
        
        # Second review
        schedule = spaced_repetition_service.calculate_next_review(
            flashcard=sample_flashcard,
            user_id=user_id,
            quality=ReviewQuality.CORRECT_HESITATION,
        )

        # Second review should have 6-day interval
        assert schedule.interval_days == 6
        assert sample_flashcard.repetition_data.repetitions == 2

    def test_calculate_next_review_subsequent_success(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test calculating next review for subsequent successful reviews."""
        user_id = "user-123"
        
        # Set up for third review
        sample_flashcard.repetition_data.repetitions = 2
        sample_flashcard.repetition_data.interval = 6
        sample_flashcard.repetition_data.ease_factor = 2.5
        
        # Third review
        schedule = spaced_repetition_service.calculate_next_review(
            flashcard=sample_flashcard,
            user_id=user_id,
            quality=ReviewQuality.PERFECT,
        )

        # Interval should be previous interval * ease factor
        assert schedule.interval_days >= 6  # Should be larger than previous
        assert sample_flashcard.repetition_data.repetitions == 3

    def test_calculate_next_review_failure(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test calculating next review after failure."""
        user_id = "user-123"
        
        # Set up card with some progress
        sample_flashcard.repetition_data.repetitions = 3
        sample_flashcard.repetition_data.interval = 15
        sample_flashcard.repetition_data.ease_factor = 2.5
        
        # Failed review
        schedule = spaced_repetition_service.calculate_next_review(
            flashcard=sample_flashcard,
            user_id=user_id,
            quality=ReviewQuality.INCORRECT_HARD,
        )

        # Should reset to beginning
        assert schedule.interval_days == 1
        assert sample_flashcard.repetition_data.repetitions == 0
        assert sample_flashcard.repetition_data.ease_factor < 2.5  # Reduced

    def test_calculate_next_review_invalid_quality(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test calculating next review with invalid quality."""
        user_id = "user-123"
        
        with pytest.raises(ValueError, match="Quality must be between 0 and 5"):
            spaced_repetition_service.calculate_next_review(
                flashcard=sample_flashcard,
                user_id=user_id,
                quality=6,
            )
        
        with pytest.raises(ValueError, match="Quality must be between 0 and 5"):
            spaced_repetition_service.calculate_next_review(
                flashcard=sample_flashcard,
                user_id=user_id,
                quality=-1,
            )

    def test_ease_factor_adjustment(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test ease factor adjustment based on quality."""
        user_id = "user-123"
        
        # Perfect response should increase ease factor
        initial_ef = sample_flashcard.repetition_data.ease_factor
        spaced_repetition_service.calculate_next_review(
            flashcard=sample_flashcard,
            user_id=user_id,
            quality=ReviewQuality.PERFECT,
        )
        assert sample_flashcard.repetition_data.ease_factor > initial_ef
        
        # Poor response should decrease ease factor
        sample_flashcard.repetition_data.ease_factor = 2.5
        spaced_repetition_service.calculate_next_review(
            flashcard=sample_flashcard,
            user_id=user_id,
            quality=ReviewQuality.CORRECT_HARD,
        )
        assert sample_flashcard.repetition_data.ease_factor < 2.5

    def test_ease_factor_bounds(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test that ease factor stays within bounds."""
        user_id = "user-123"
        
        # Try to push ease factor above maximum
        for _ in range(10):
            spaced_repetition_service.calculate_next_review(
                flashcard=sample_flashcard,
                user_id=user_id,
                quality=ReviewQuality.PERFECT,
            )
        
        assert sample_flashcard.repetition_data.ease_factor <= spaced_repetition_service.MAX_EASE_FACTOR
        
        # Try to push ease factor below minimum
        sample_flashcard.repetition_data.ease_factor = 1.5
        for _ in range(10):
            spaced_repetition_service.calculate_next_review(
                flashcard=sample_flashcard,
                user_id=user_id,
                quality=ReviewQuality.BLACKOUT,
            )
        
        assert sample_flashcard.repetition_data.ease_factor >= spaced_repetition_service.MIN_EASE_FACTOR

    def test_performance_tracking(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test that performance is tracked correctly."""
        user_id = "user-123"
        
        # Perform several reviews
        qualities = [5, 4, 5, 3, 4]
        for quality in qualities:
            spaced_repetition_service.calculate_next_review(
                flashcard=sample_flashcard,
                user_id=user_id,
                quality=quality,
            )
        
        # Check performance history
        history = spaced_repetition_service._get_performance_history(user_id, sample_flashcard.id)
        assert len(history) == len(qualities)
        assert history == qualities

    def test_adaptive_adjustment_high_performance(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test adaptive adjustment for high performance."""
        user_id = "user-123"
        
        # Build high performance history
        for _ in range(10):
            spaced_repetition_service.calculate_next_review(
                flashcard=sample_flashcard,
                user_id=user_id,
                quality=ReviewQuality.PERFECT,
            )
        
        # Next review should have increased interval
        sample_flashcard.repetition_data.repetitions = 3
        sample_flashcard.repetition_data.interval = 10
        
        schedule = spaced_repetition_service.calculate_next_review(
            flashcard=sample_flashcard,
            user_id=user_id,
            quality=ReviewQuality.PERFECT,
        )
        
        # Should get bonus interval increase for high performance
        # (exact value depends on adaptive logic)
        assert schedule.interval_days >= 10

    def test_adaptive_adjustment_low_performance(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test adaptive adjustment for low performance."""
        user_id = "user-123"
        
        # Build low performance history
        for _ in range(10):
            spaced_repetition_service.calculate_next_review(
                flashcard=sample_flashcard,
                user_id=user_id,
                quality=ReviewQuality.INCORRECT_HARD,
            )
        
        # Should keep intervals short due to poor performance
        assert sample_flashcard.repetition_data.interval <= 1

    def test_get_due_flashcards_never_reviewed(
        self,
        spaced_repetition_service,
    ):
        """Test getting due flashcards that have never been reviewed."""
        user_id = "user-123"
        
        flashcards = [
            Flashcard(
                id=f"card-{i}",
                content_id="content-123",
                question=f"Question {i}",
                answer=f"Answer {i}",
                difficulty=DifficultyLevel.MEDIUM,
                tags=["test"],
                repetition_data=SpacedRepetitionData(),
                created_at=datetime.utcnow(),
            )
            for i in range(5)
        ]
        
        due_cards = spaced_repetition_service.get_due_flashcards(flashcards, user_id)
        
        # All cards should be due (never reviewed)
        assert len(due_cards) == 5

    def test_get_due_flashcards_mixed(
        self,
        spaced_repetition_service,
    ):
        """Test getting due flashcards with mixed review states."""
        user_id = "user-123"
        now = datetime.utcnow()
        
        flashcards = [
            # Due now
            Flashcard(
                id="card-1",
                content_id="content-123",
                question="Question 1",
                answer="Answer 1",
                difficulty=DifficultyLevel.MEDIUM,
                tags=["test"],
                repetition_data=SpacedRepetitionData(
                    next_review=now - timedelta(days=1)
                ),
                created_at=datetime.utcnow(),
            ),
            # Due in future
            Flashcard(
                id="card-2",
                content_id="content-123",
                question="Question 2",
                answer="Answer 2",
                difficulty=DifficultyLevel.MEDIUM,
                tags=["test"],
                repetition_data=SpacedRepetitionData(
                    next_review=now + timedelta(days=5)
                ),
                created_at=datetime.utcnow(),
            ),
            # Never reviewed
            Flashcard(
                id="card-3",
                content_id="content-123",
                question="Question 3",
                answer="Answer 3",
                difficulty=DifficultyLevel.MEDIUM,
                tags=["test"],
                repetition_data=SpacedRepetitionData(),
                created_at=datetime.utcnow(),
            ),
        ]
        
        due_cards = spaced_repetition_service.get_due_flashcards(flashcards, user_id)
        
        # Should have 2 due cards (card-1 and card-3)
        assert len(due_cards) == 2
        due_ids = [card.id for card in due_cards]
        assert "card-1" in due_ids
        assert "card-3" in due_ids
        assert "card-2" not in due_ids

    def test_get_user_statistics(
        self,
        spaced_repetition_service,
    ):
        """Test getting user statistics."""
        user_id = "user-123"
        now = datetime.utcnow()
        
        flashcards = [
            # Mastered card
            Flashcard(
                id="card-1",
                content_id="content-123",
                question="Question 1",
                answer="Answer 1",
                difficulty=DifficultyLevel.MEDIUM,
                tags=["test"],
                repetition_data=SpacedRepetitionData(
                    repetitions=5,
                    ease_factor=2.8,
                    next_review=now + timedelta(days=30),
                ),
                created_at=datetime.utcnow(),
            ),
            # Due today
            Flashcard(
                id="card-2",
                content_id="content-123",
                question="Question 2",
                answer="Answer 2",
                difficulty=DifficultyLevel.MEDIUM,
                tags=["test"],
                repetition_data=SpacedRepetitionData(
                    repetitions=2,
                    ease_factor=2.5,
                    next_review=now - timedelta(hours=1),
                ),
                created_at=datetime.utcnow(),
            ),
            # Due this week
            Flashcard(
                id="card-3",
                content_id="content-123",
                question="Question 3",
                answer="Answer 3",
                difficulty=DifficultyLevel.MEDIUM,
                tags=["test"],
                repetition_data=SpacedRepetitionData(
                    repetitions=1,
                    ease_factor=2.3,
                    next_review=now + timedelta(days=3),
                ),
                created_at=datetime.utcnow(),
            ),
        ]
        
        # Add some performance history
        spaced_repetition_service.performance_history[user_id] = {
            "card-1": [5, 5, 4, 5, 5],
            "card-2": [4, 3, 4],
            "card-3": [3],
        }
        
        stats = spaced_repetition_service.get_user_statistics(user_id, flashcards)
        
        assert stats["total_cards"] == 3
        assert stats["due_today"] == 1
        assert stats["due_this_week"] == 1
        assert stats["mastered_cards"] == 1
        assert stats["total_reviews"] == 8  # 5 + 2 + 1
        assert stats["average_ease_factor"] > 0
        assert stats["average_quality"] > 0

    def test_reset_flashcard(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test resetting a flashcard."""
        # Set up card with progress
        sample_flashcard.repetition_data.repetitions = 5
        sample_flashcard.repetition_data.interval = 30
        sample_flashcard.repetition_data.ease_factor = 2.8
        sample_flashcard.repetition_data.last_reviewed = datetime.utcnow()
        sample_flashcard.repetition_data.next_review = datetime.utcnow() + timedelta(days=30)
        
        # Reset
        spaced_repetition_service.reset_flashcard(sample_flashcard)
        
        # Verify reset to defaults
        assert sample_flashcard.repetition_data.repetitions == 0
        assert sample_flashcard.repetition_data.interval == 1
        assert sample_flashcard.repetition_data.ease_factor == 2.5
        assert sample_flashcard.repetition_data.last_reviewed is None
        assert sample_flashcard.repetition_data.next_review is None

    def test_adjust_difficulty_increase(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test difficulty adjustment for high performance."""
        user_id = "user-123"
        sample_flashcard.difficulty = DifficultyLevel.EASY
        
        # Build high performance history
        spaced_repetition_service.performance_history[user_id] = {
            sample_flashcard.id: [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
        }
        
        new_difficulty = spaced_repetition_service.adjust_difficulty(
            flashcard=sample_flashcard,
            user_id=user_id,
        )
        
        # Should increase difficulty
        assert new_difficulty == DifficultyLevel.MEDIUM

    def test_adjust_difficulty_decrease(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test difficulty adjustment for low performance."""
        user_id = "user-123"
        sample_flashcard.difficulty = DifficultyLevel.HARD
        
        # Build low performance history
        spaced_repetition_service.performance_history[user_id] = {
            sample_flashcard.id: [1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
        }
        
        new_difficulty = spaced_repetition_service.adjust_difficulty(
            flashcard=sample_flashcard,
            user_id=user_id,
        )
        
        # Should decrease difficulty
        assert new_difficulty == DifficultyLevel.MEDIUM

    def test_adjust_difficulty_insufficient_data(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test difficulty adjustment with insufficient data."""
        user_id = "user-123"
        
        # Not enough performance history
        spaced_repetition_service.performance_history[user_id] = {
            sample_flashcard.id: [5, 4]
        }
        
        new_difficulty = spaced_repetition_service.adjust_difficulty(
            flashcard=sample_flashcard,
            user_id=user_id,
        )
        
        # Should keep current difficulty
        assert new_difficulty == sample_flashcard.difficulty

    def test_performance_history_limit(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test that performance history is limited to prevent memory bloat."""
        user_id = "user-123"
        
        # Perform many reviews
        for _ in range(50):
            spaced_repetition_service.calculate_next_review(
                flashcard=sample_flashcard,
                user_id=user_id,
                quality=ReviewQuality.PERFECT,
            )
        
        # History should be limited
        history = spaced_repetition_service._get_performance_history(user_id, sample_flashcard.id)
        max_history = spaced_repetition_service.PERFORMANCE_WINDOW * 3
        assert len(history) <= max_history

    def test_different_users_separate_history(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test that different users have separate performance histories."""
        user1 = "user-1"
        user2 = "user-2"
        
        # User 1 reviews
        spaced_repetition_service.calculate_next_review(
            flashcard=sample_flashcard,
            user_id=user1,
            quality=ReviewQuality.PERFECT,
        )
        
        # User 2 reviews
        spaced_repetition_service.calculate_next_review(
            flashcard=sample_flashcard,
            user_id=user2,
            quality=ReviewQuality.INCORRECT_HARD,
        )
        
        # Check separate histories
        history1 = spaced_repetition_service._get_performance_history(user1, sample_flashcard.id)
        history2 = spaced_repetition_service._get_performance_history(user2, sample_flashcard.id)
        
        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0] == ReviewQuality.PERFECT
        assert history2[0] == ReviewQuality.INCORRECT_HARD

    def test_interval_minimum(
        self,
        spaced_repetition_service,
        sample_flashcard,
    ):
        """Test that interval never goes below 1 day."""
        user_id = "user-123"
        
        # Perform multiple failures
        for _ in range(5):
            spaced_repetition_service.calculate_next_review(
                flashcard=sample_flashcard,
                user_id=user_id,
                quality=ReviewQuality.BLACKOUT,
            )
        
        # Interval should never be less than 1
        assert sample_flashcard.repetition_data.interval >= 1
