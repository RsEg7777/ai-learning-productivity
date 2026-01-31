"""Spaced repetition algorithm service for flashcard scheduling.

This service implements the SuperMemo 2 (SM-2) algorithm with enhancements for:
- Adaptive difficulty based on user performance
- Long-term retention optimization
- Personalized scheduling based on user history

The SM-2 algorithm uses:
- Ease Factor (EF): Determines how quickly intervals increase (1.3 to 2.5+)
- Interval: Days until next review
- Repetitions: Number of successful consecutive reviews

Quality ratings (0-5):
- 0: Complete blackout
- 1: Incorrect response, correct answer remembered
- 2: Incorrect response, correct answer seemed easy to recall
- 3: Correct response, but required significant difficulty
- 4: Correct response, after some hesitation
- 5: Perfect response
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from ...shared.models.quiz import (
    Flashcard,
    SpacedRepetitionData,
    RepetitionSchedule,
    DifficultyLevel,
)
from ...shared.utils.errors import ContentProcessingError

logger = logging.getLogger(__name__)


class ReviewQuality(int, Enum):
    """Quality of flashcard review response (0-5 scale)."""
    BLACKOUT = 0  # Complete blackout
    INCORRECT_HARD = 1  # Incorrect, but correct answer remembered
    INCORRECT_EASY = 2  # Incorrect, but correct answer seemed easy
    CORRECT_HARD = 3  # Correct with significant difficulty
    CORRECT_HESITATION = 4  # Correct after some hesitation
    PERFECT = 5  # Perfect response


class SpacedRepetitionService:
    """
    Service for managing spaced repetition scheduling.
    
    Implements the SuperMemo 2 algorithm with adaptive enhancements:
    - Dynamic ease factor adjustment based on performance
    - Difficulty-based initial intervals
    - Long-term retention optimization
    - Performance trend analysis
    """

    # SM-2 Algorithm constants
    MIN_EASE_FACTOR = 1.3
    DEFAULT_EASE_FACTOR = 2.5
    MAX_EASE_FACTOR = 3.0
    
    # Initial intervals based on difficulty
    INITIAL_INTERVALS = {
        DifficultyLevel.EASY: 1,  # 1 day
        DifficultyLevel.MEDIUM: 1,  # 1 day
        DifficultyLevel.HARD: 1,  # 1 day
    }
    
    # Minimum quality for successful review
    MIN_PASSING_QUALITY = 3
    
    # Maximum interval to prevent overflow (1 year)
    MAX_INTERVAL_DAYS = 365
    
    # Performance tracking window (number of recent reviews to consider)
    PERFORMANCE_WINDOW = 10

    def __init__(self):
        """Initialize spaced repetition service."""
        # Track user performance history: user_id -> card_id -> [quality_scores]
        self.performance_history: Dict[str, Dict[str, List[int]]] = {}
        logger.info("Initialized SpacedRepetitionService")

    def calculate_next_review(
        self,
        flashcard: Flashcard,
        user_id: str,
        quality: int,
    ) -> RepetitionSchedule:
        """
        Calculate the next review schedule for a flashcard based on user performance.
        
        This is the main method that implements the spaced repetition algorithm.
        It updates the flashcard's repetition data and returns the next review schedule.

        Args:
            flashcard: Flashcard to schedule
            user_id: User identifier
            quality: Review quality (0-5, where 3+ is passing)

        Returns:
            RepetitionSchedule with next review date and updated parameters

        Raises:
            ContentProcessingError: If calculation fails
            ValueError: If quality is out of range
        """
        try:
            # Validate quality
            if not 0 <= quality <= 5:
                raise ValueError(f"Quality must be between 0 and 5, got {quality}")

            logger.info(
                f"Calculating next review for flashcard {flashcard.id}, "
                f"user {user_id}, quality {quality}"
            )

            # Get current repetition data
            rep_data = flashcard.repetition_data

            # Record performance
            self._record_performance(user_id, flashcard.id, quality)

            # Calculate new parameters based on SM-2 algorithm
            new_ease_factor, new_interval, new_repetitions = self._calculate_sm2_parameters(
                current_ease_factor=rep_data.ease_factor,
                current_interval=rep_data.interval,
                current_repetitions=rep_data.repetitions,
                quality=quality,
                difficulty=flashcard.difficulty,
            )

            # Apply adaptive adjustments based on user performance
            adjusted_ease_factor, adjusted_interval = self._apply_adaptive_adjustments(
                user_id=user_id,
                card_id=flashcard.id,
                ease_factor=new_ease_factor,
                interval=new_interval,
                quality=quality,
            )

            # Update flashcard repetition data
            now = datetime.utcnow()
            next_review_date = now + timedelta(days=adjusted_interval)

            rep_data.ease_factor = adjusted_ease_factor
            rep_data.interval = adjusted_interval
            rep_data.repetitions = new_repetitions
            rep_data.last_reviewed = now
            rep_data.next_review = next_review_date

            # Create schedule
            schedule = RepetitionSchedule(
                flashcard_id=flashcard.id,
                next_review=next_review_date,
                interval_days=adjusted_interval,
                ease_factor=adjusted_ease_factor,
            )

            logger.info(
                f"Next review scheduled for flashcard {flashcard.id}: "
                f"{adjusted_interval} days (ease factor: {adjusted_ease_factor:.2f}, "
                f"repetitions: {new_repetitions})"
            )

            return schedule

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error calculating next review: {e}")
            raise ContentProcessingError(
                message=f"Failed to calculate next review: {str(e)}",
                content_type="spaced_repetition",
            )

    def _calculate_sm2_parameters(
        self,
        current_ease_factor: float,
        current_interval: int,
        current_repetitions: int,
        quality: int,
        difficulty: DifficultyLevel,
    ) -> Tuple[float, int, int]:
        """
        Calculate new SM-2 parameters based on review quality.
        
        Implements the core SuperMemo 2 algorithm:
        1. Update ease factor based on quality
        2. Calculate new interval based on repetitions
        3. Update repetition count

        Args:
            current_ease_factor: Current ease factor
            current_interval: Current interval in days
            current_repetitions: Current repetition count
            quality: Review quality (0-5)
            difficulty: Flashcard difficulty level

        Returns:
            Tuple of (new_ease_factor, new_interval, new_repetitions)
        """
        # Calculate new ease factor
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        ease_factor = current_ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        # Clamp ease factor to valid range
        ease_factor = max(self.MIN_EASE_FACTOR, min(self.MAX_EASE_FACTOR, ease_factor))

        # Determine if review was successful (quality >= 3)
        if quality >= self.MIN_PASSING_QUALITY:
            # Successful review - increase interval
            if current_repetitions == 0:
                # First successful review
                interval = self.INITIAL_INTERVALS.get(difficulty, 1)
                repetitions = 1
            elif current_repetitions == 1:
                # Second successful review
                interval = 6
                repetitions = 2
            else:
                # Subsequent successful reviews
                interval = int(current_interval * ease_factor)
                repetitions = current_repetitions + 1
            
            # Cap interval at maximum to prevent overflow
            interval = min(interval, self.MAX_INTERVAL_DAYS)
        else:
            # Failed review - reset to beginning
            interval = 1
            repetitions = 0
            # Reduce ease factor more aggressively for failures
            ease_factor = max(self.MIN_EASE_FACTOR, ease_factor - 0.2)

        logger.debug(
            f"SM-2 calculation: quality={quality}, "
            f"EF: {current_ease_factor:.2f} -> {ease_factor:.2f}, "
            f"interval: {current_interval} -> {interval}, "
            f"reps: {current_repetitions} -> {repetitions}"
        )

        return ease_factor, interval, repetitions

    def _apply_adaptive_adjustments(
        self,
        user_id: str,
        card_id: str,
        ease_factor: float,
        interval: int,
        quality: int,
    ) -> Tuple[float, int]:
        """
        Apply adaptive adjustments based on user performance trends.
        
        Analyzes recent performance to optimize long-term retention:
        - If user consistently performs well, slightly increase intervals
        - If user struggles, reduce intervals for better retention
        - Adjust ease factor based on performance consistency

        Args:
            user_id: User identifier
            card_id: Flashcard identifier
            ease_factor: Calculated ease factor
            interval: Calculated interval
            quality: Current review quality

        Returns:
            Tuple of (adjusted_ease_factor, adjusted_interval)
        """
        # Get performance history
        performance = self._get_performance_history(user_id, card_id)
        
        if len(performance) < 3:
            # Not enough history for adjustments
            return ease_factor, interval

        # Calculate performance metrics
        recent_performance = performance[-self.PERFORMANCE_WINDOW:]
        avg_quality = sum(recent_performance) / len(recent_performance)
        success_rate = sum(1 for q in recent_performance if q >= self.MIN_PASSING_QUALITY) / len(recent_performance)
        
        # Calculate performance trend (improving, stable, or declining)
        if len(recent_performance) >= 5:
            first_half = recent_performance[:len(recent_performance)//2]
            second_half = recent_performance[len(recent_performance)//2:]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            trend = avg_second - avg_first
        else:
            trend = 0

        # Adjust based on performance
        adjusted_ease_factor = ease_factor
        adjusted_interval = interval

        # High performance - optimize for efficiency
        if avg_quality >= 4.5 and success_rate >= 0.9:
            # User is doing very well - can increase intervals slightly
            adjusted_interval = int(interval * 1.2)
            adjusted_ease_factor = min(self.MAX_EASE_FACTOR, ease_factor + 0.1)
            logger.debug(f"High performance detected - increasing interval by 20%")
        
        # Improving trend - encourage progress
        elif trend > 0.5 and success_rate >= 0.7:
            # User is improving - maintain current pace
            logger.debug(f"Improving trend detected - maintaining current schedule")
        
        # Struggling - optimize for retention
        elif avg_quality < 3.0 or success_rate < 0.5:
            # User is struggling - reduce intervals for better retention
            adjusted_interval = max(1, int(interval * 0.7))
            adjusted_ease_factor = max(self.MIN_EASE_FACTOR, ease_factor - 0.1)
            logger.debug(f"Low performance detected - reducing interval by 30%")
        
        # Declining trend - intervene early
        elif trend < -0.5:
            # Performance is declining - reduce intervals
            adjusted_interval = max(1, int(interval * 0.8))
            logger.debug(f"Declining trend detected - reducing interval by 20%")

        # Ensure minimum interval of 1 day and maximum to prevent overflow
        adjusted_interval = max(1, min(adjusted_interval, self.MAX_INTERVAL_DAYS))

        logger.debug(
            f"Adaptive adjustments: avg_quality={avg_quality:.2f}, "
            f"success_rate={success_rate:.2f}, trend={trend:.2f}, "
            f"interval: {interval} -> {adjusted_interval}, "
            f"EF: {ease_factor:.2f} -> {adjusted_ease_factor:.2f}"
        )

        return adjusted_ease_factor, adjusted_interval

    def _record_performance(self, user_id: str, card_id: str, quality: int) -> None:
        """
        Record a performance data point for a user and flashcard.

        Args:
            user_id: User identifier
            card_id: Flashcard identifier
            quality: Review quality (0-5)
        """
        if user_id not in self.performance_history:
            self.performance_history[user_id] = {}
        
        if card_id not in self.performance_history[user_id]:
            self.performance_history[user_id][card_id] = []
        
        self.performance_history[user_id][card_id].append(quality)
        
        # Keep only recent history to avoid memory bloat
        max_history = self.PERFORMANCE_WINDOW * 3
        if len(self.performance_history[user_id][card_id]) > max_history:
            self.performance_history[user_id][card_id] = \
                self.performance_history[user_id][card_id][-max_history:]

    def _get_performance_history(self, user_id: str, card_id: str) -> List[int]:
        """
        Get performance history for a user and flashcard.

        Args:
            user_id: User identifier
            card_id: Flashcard identifier

        Returns:
            List of quality scores
        """
        if user_id not in self.performance_history:
            return []
        
        if card_id not in self.performance_history[user_id]:
            return []
        
        return self.performance_history[user_id][card_id]

    def get_due_flashcards(
        self,
        flashcards: List[Flashcard],
        user_id: str,
    ) -> List[Flashcard]:
        """
        Get flashcards that are due for review.
        
        Filters flashcards based on their next_review date.

        Args:
            flashcards: List of flashcards to check
            user_id: User identifier

        Returns:
            List of flashcards due for review
        """
        now = datetime.utcnow()
        due_cards = []

        for card in flashcards:
            # If never reviewed, it's due
            if card.repetition_data.next_review is None:
                due_cards.append(card)
            # If next review date has passed, it's due
            elif card.repetition_data.next_review <= now:
                due_cards.append(card)

        logger.info(
            f"Found {len(due_cards)} flashcards due for review "
            f"(out of {len(flashcards)} total) for user {user_id}"
        )

        return due_cards

    def get_user_statistics(
        self,
        user_id: str,
        flashcards: List[Flashcard],
    ) -> Dict[str, any]:
        """
        Get spaced repetition statistics for a user.

        Args:
            user_id: User identifier
            flashcards: User's flashcards

        Returns:
            Dictionary with statistics:
            - total_cards: Total number of flashcards
            - due_today: Number of cards due today
            - due_this_week: Number of cards due this week
            - mastered_cards: Cards with high repetition count
            - average_ease_factor: Average ease factor across cards
            - total_reviews: Total number of reviews performed
            - average_quality: Average review quality
        """
        now = datetime.utcnow()
        week_from_now = now + timedelta(days=7)

        due_today = 0
        due_this_week = 0
        mastered_cards = 0
        total_ease_factor = 0.0
        total_reviews = 0

        for card in flashcards:
            # Count due cards
            if card.repetition_data.next_review is None or card.repetition_data.next_review <= now:
                due_today += 1
            elif card.repetition_data.next_review <= week_from_now:
                due_this_week += 1

            # Count mastered cards (5+ successful repetitions)
            if card.repetition_data.repetitions >= 5:
                mastered_cards += 1

            # Sum ease factors
            total_ease_factor += card.repetition_data.ease_factor

            # Count reviews
            total_reviews += card.repetition_data.repetitions

        # Calculate average ease factor
        avg_ease_factor = total_ease_factor / len(flashcards) if flashcards else 0.0

        # Calculate average quality from performance history
        all_qualities = []
        if user_id in self.performance_history:
            for card_history in self.performance_history[user_id].values():
                all_qualities.extend(card_history)
        
        avg_quality = sum(all_qualities) / len(all_qualities) if all_qualities else 0.0

        stats = {
            "total_cards": len(flashcards),
            "due_today": due_today,
            "due_this_week": due_this_week,
            "mastered_cards": mastered_cards,
            "average_ease_factor": round(avg_ease_factor, 2),
            "total_reviews": total_reviews,
            "average_quality": round(avg_quality, 2),
        }

        logger.info(f"User {user_id} statistics: {stats}")

        return stats

    def reset_flashcard(self, flashcard: Flashcard) -> None:
        """
        Reset a flashcard's spaced repetition data.
        
        Useful when a user wants to start over with a card.

        Args:
            flashcard: Flashcard to reset
        """
        flashcard.repetition_data = SpacedRepetitionData()
        logger.info(f"Reset spaced repetition data for flashcard {flashcard.id}")

    def adjust_difficulty(
        self,
        flashcard: Flashcard,
        user_id: str,
    ) -> DifficultyLevel:
        """
        Adjust flashcard difficulty based on user performance.
        
        Analyzes performance history to determine if difficulty should change:
        - Consistently high performance -> increase difficulty
        - Consistently low performance -> decrease difficulty

        Args:
            flashcard: Flashcard to adjust
            user_id: User identifier

        Returns:
            Recommended difficulty level
        """
        performance = self._get_performance_history(user_id, flashcard.id)
        
        if len(performance) < 5:
            # Not enough data for adjustment
            return flashcard.difficulty

        # Calculate recent performance
        recent_performance = performance[-10:]
        avg_quality = sum(recent_performance) / len(recent_performance)
        success_rate = sum(1 for q in recent_performance if q >= self.MIN_PASSING_QUALITY) / len(recent_performance)

        current_difficulty = flashcard.difficulty
        new_difficulty = current_difficulty

        # Adjust difficulty based on performance
        if avg_quality >= 4.5 and success_rate >= 0.9:
            # Performing very well - increase difficulty
            if current_difficulty == DifficultyLevel.EASY:
                new_difficulty = DifficultyLevel.MEDIUM
            elif current_difficulty == DifficultyLevel.MEDIUM:
                new_difficulty = DifficultyLevel.HARD
        elif avg_quality < 2.5 or success_rate < 0.4:
            # Struggling - decrease difficulty
            if current_difficulty == DifficultyLevel.HARD:
                new_difficulty = DifficultyLevel.MEDIUM
            elif current_difficulty == DifficultyLevel.MEDIUM:
                new_difficulty = DifficultyLevel.EASY

        if new_difficulty != current_difficulty:
            logger.info(
                f"Adjusting difficulty for flashcard {flashcard.id}: "
                f"{current_difficulty} -> {new_difficulty} "
                f"(avg_quality={avg_quality:.2f}, success_rate={success_rate:.2f})"
            )

        return new_difficulty
