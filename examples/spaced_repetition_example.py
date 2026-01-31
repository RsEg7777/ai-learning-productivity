"""Example usage of the spaced repetition service.

This example demonstrates:
1. Creating flashcards with spaced repetition data
2. Calculating next review schedules based on user performance
3. Getting due flashcards for review
4. Tracking user statistics
5. Adjusting difficulty based on performance
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.quiz_generation import (
    FlashcardGenerator,
    SpacedRepetitionService,
    ReviewQuality,
)
from src.shared.models.quiz import (
    Flashcard,
    SpacedRepetitionData,
    DifficultyLevel,
)
from src.shared.models.content import (
    ProcessedContent,
    Summary,
    SummaryType,
    Concept,
)
from src.shared.aws_clients.bedrock_client import BedrockClient


def create_sample_flashcards() -> list[Flashcard]:
    """Create sample flashcards for demonstration."""
    flashcards = [
        Flashcard(
            id="card-1",
            content_id="content-123",
            question="What is Python?",
            answer="Python is a high-level, interpreted programming language known for its simplicity and readability.",
            difficulty=DifficultyLevel.EASY,
            tags=["programming", "python", "basics"],
            repetition_data=SpacedRepetitionData(),
            created_at=datetime.utcnow(),
        ),
        Flashcard(
            id="card-2",
            content_id="content-123",
            question="What is a decorator in Python?",
            answer="A decorator is a design pattern that allows you to modify the behavior of a function or class without permanently modifying it.",
            difficulty=DifficultyLevel.MEDIUM,
            tags=["programming", "python", "advanced"],
            repetition_data=SpacedRepetitionData(),
            created_at=datetime.utcnow(),
        ),
        Flashcard(
            id="card-3",
            content_id="content-123",
            question="Explain the Global Interpreter Lock (GIL) in Python.",
            answer="The GIL is a mutex that protects access to Python objects, preventing multiple threads from executing Python bytecode simultaneously.",
            difficulty=DifficultyLevel.HARD,
            tags=["programming", "python", "concurrency"],
            repetition_data=SpacedRepetitionData(),
            created_at=datetime.utcnow(),
        ),
    ]
    return flashcards


def simulate_review_session(
    service: SpacedRepetitionService,
    flashcard: Flashcard,
    user_id: str,
    quality: int,
) -> None:
    """Simulate a single flashcard review."""
    print(f"\n{'='*60}")
    print(f"Reviewing Flashcard: {flashcard.id}")
    print(f"Question: {flashcard.question}")
    print(f"Difficulty: {flashcard.difficulty.value}")
    print(f"Current Repetitions: {flashcard.repetition_data.repetitions}")
    print(f"Current Interval: {flashcard.repetition_data.interval} days")
    print(f"Current Ease Factor: {flashcard.repetition_data.ease_factor:.2f}")
    
    # Calculate next review
    schedule = service.calculate_next_review(
        flashcard=flashcard,
        user_id=user_id,
        quality=quality,
    )
    
    print(f"\nReview Quality: {quality}/5")
    print(f"Next Review: {schedule.next_review.strftime('%Y-%m-%d %H:%M')}")
    print(f"New Interval: {schedule.interval_days} days")
    print(f"New Ease Factor: {schedule.ease_factor:.2f}")
    print(f"New Repetitions: {flashcard.repetition_data.repetitions}")


def main():
    """Run spaced repetition examples."""
    print("="*60)
    print("Spaced Repetition Service Example")
    print("="*60)
    
    # Initialize service
    service = SpacedRepetitionService()
    user_id = "user-demo-123"
    
    # Create sample flashcards
    flashcards = create_sample_flashcards()
    
    print("\n1. Initial Flashcard State")
    print("-" * 60)
    for card in flashcards:
        print(f"\nCard: {card.id}")
        print(f"  Question: {card.question[:50]}...")
        print(f"  Difficulty: {card.difficulty.value}")
        print(f"  Repetitions: {card.repetition_data.repetitions}")
        print(f"  Interval: {card.repetition_data.interval} days")
    
    # Example 2: First review - Perfect response
    print("\n\n2. First Review - Perfect Response")
    print("-" * 60)
    simulate_review_session(
        service=service,
        flashcard=flashcards[0],
        user_id=user_id,
        quality=ReviewQuality.PERFECT,
    )
    
    # Example 3: Second review - Good response
    print("\n\n3. Second Review - Good Response")
    print("-" * 60)
    simulate_review_session(
        service=service,
        flashcard=flashcards[0],
        user_id=user_id,
        quality=ReviewQuality.CORRECT_HESITATION,
    )
    
    # Example 4: Third review - Perfect response
    print("\n\n4. Third Review - Perfect Response")
    print("-" * 60)
    simulate_review_session(
        service=service,
        flashcard=flashcards[0],
        user_id=user_id,
        quality=ReviewQuality.PERFECT,
    )
    
    # Example 5: Failed review - Reset progress
    print("\n\n5. Failed Review - Progress Reset")
    print("-" * 60)
    simulate_review_session(
        service=service,
        flashcard=flashcards[1],
        user_id=user_id,
        quality=ReviewQuality.INCORRECT_HARD,
    )
    
    # Example 6: Build performance history
    print("\n\n6. Building Performance History")
    print("-" * 60)
    print("Simulating multiple reviews to build performance history...")
    
    # Simulate high performance on card 2
    for i in range(5):
        quality = ReviewQuality.PERFECT if i % 2 == 0 else ReviewQuality.CORRECT_HESITATION
        service.calculate_next_review(
            flashcard=flashcards[1],
            user_id=user_id,
            quality=quality,
        )
    
    print(f"\nCard 2 after 5 reviews:")
    print(f"  Repetitions: {flashcards[1].repetition_data.repetitions}")
    print(f"  Interval: {flashcards[1].repetition_data.interval} days")
    print(f"  Ease Factor: {flashcards[1].repetition_data.ease_factor:.2f}")
    
    # Example 7: Get due flashcards
    print("\n\n7. Getting Due Flashcards")
    print("-" * 60)
    
    # Set some cards as due
    flashcards[0].repetition_data.next_review = datetime.utcnow() - timedelta(days=1)
    flashcards[1].repetition_data.next_review = datetime.utcnow() + timedelta(days=5)
    flashcards[2].repetition_data.next_review = None  # Never reviewed
    
    due_cards = service.get_due_flashcards(flashcards, user_id)
    
    print(f"Total flashcards: {len(flashcards)}")
    print(f"Due for review: {len(due_cards)}")
    print("\nDue cards:")
    for card in due_cards:
        print(f"  - {card.id}: {card.question[:40]}...")
    
    # Example 8: User statistics
    print("\n\n8. User Statistics")
    print("-" * 60)
    
    stats = service.get_user_statistics(user_id, flashcards)
    
    print(f"Total Cards: {stats['total_cards']}")
    print(f"Due Today: {stats['due_today']}")
    print(f"Due This Week: {stats['due_this_week']}")
    print(f"Mastered Cards: {stats['mastered_cards']}")
    print(f"Average Ease Factor: {stats['average_ease_factor']:.2f}")
    print(f"Total Reviews: {stats['total_reviews']}")
    print(f"Average Quality: {stats['average_quality']:.2f}")
    
    # Example 9: Adaptive difficulty adjustment
    print("\n\n9. Adaptive Difficulty Adjustment")
    print("-" * 60)
    
    # Build high performance history for card 3
    print("Building high performance history for card 3...")
    for _ in range(10):
        service.calculate_next_review(
            flashcard=flashcards[2],
            user_id=user_id,
            quality=ReviewQuality.PERFECT,
        )
    
    original_difficulty = flashcards[2].difficulty
    new_difficulty = service.adjust_difficulty(flashcards[2], user_id)
    
    print(f"\nCard 3 difficulty adjustment:")
    print(f"  Original: {original_difficulty.value}")
    print(f"  Recommended: {new_difficulty.value}")
    print(f"  Reason: Consistently high performance")
    
    # Example 10: Reset flashcard
    print("\n\n10. Reset Flashcard")
    print("-" * 60)
    
    print(f"Card 1 before reset:")
    print(f"  Repetitions: {flashcards[0].repetition_data.repetitions}")
    print(f"  Interval: {flashcards[0].repetition_data.interval} days")
    print(f"  Ease Factor: {flashcards[0].repetition_data.ease_factor:.2f}")
    
    service.reset_flashcard(flashcards[0])
    
    print(f"\nCard 1 after reset:")
    print(f"  Repetitions: {flashcards[0].repetition_data.repetitions}")
    print(f"  Interval: {flashcards[0].repetition_data.interval} days")
    print(f"  Ease Factor: {flashcards[0].repetition_data.ease_factor:.2f}")
    
    # Example 11: Long-term retention optimization
    print("\n\n11. Long-Term Retention Optimization")
    print("-" * 60)
    print("Demonstrating adaptive adjustments based on performance trends...")
    
    # Create a new card for this example
    test_card = Flashcard(
        id="card-test",
        content_id="content-123",
        question="Test question for retention optimization",
        answer="Test answer",
        difficulty=DifficultyLevel.MEDIUM,
        tags=["test"],
        repetition_data=SpacedRepetitionData(),
        created_at=datetime.utcnow(),
    )
    
    # Simulate declining performance
    print("\nSimulating declining performance...")
    qualities = [5, 5, 4, 4, 3, 3, 2, 2, 1, 1]
    for i, quality in enumerate(qualities):
        schedule = service.calculate_next_review(
            flashcard=test_card,
            user_id=user_id,
            quality=quality,
        )
        if i == 0:
            print(f"  Review 1: Quality={quality}, Interval={schedule.interval_days} days")
        elif i == len(qualities) - 1:
            print(f"  Review {i+1}: Quality={quality}, Interval={schedule.interval_days} days")
    
    print(f"\nAdaptive adjustment applied:")
    print(f"  Intervals reduced to optimize retention")
    print(f"  Ease factor adjusted: {test_card.repetition_data.ease_factor:.2f}")
    
    print("\n" + "="*60)
    print("Example completed successfully!")
    print("="*60)


if __name__ == "__main__":
    main()
