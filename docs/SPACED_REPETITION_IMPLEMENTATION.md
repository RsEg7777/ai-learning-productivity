# Spaced Repetition Algorithm Implementation

## Overview

This document describes the implementation of the spaced repetition algorithm for the AI Learning Assistant. The implementation is based on the SuperMemo 2 (SM-2) algorithm with enhancements for adaptive difficulty and long-term retention optimization.

## Architecture

### Core Components

1. **SpacedRepetitionService**: Main service that implements the SM-2 algorithm
2. **SpacedRepetitionData**: Data model for tracking repetition state
3. **RepetitionSchedule**: Model for next review scheduling
4. **ReviewQuality**: Enum for quality ratings (0-5)

### File Structure

```
src/services/quiz_generation/
├── spaced_repetition_service.py    # Main service implementation
├── flashcard_generator.py          # Flashcard generation (uses SpacedRepetitionData)
└── __init__.py                      # Service exports

src/shared/models/
└── quiz.py                          # Data models (SpacedRepetitionData, RepetitionSchedule)

tests/unit/
└── test_spaced_repetition_service.py  # Unit tests

examples/
└── spaced_repetition_example.py    # Usage examples
```

## Algorithm Details

### SuperMemo 2 (SM-2) Algorithm

The SM-2 algorithm uses three key parameters:

1. **Ease Factor (EF)**: Determines how quickly intervals increase
   - Range: 1.3 to 3.0
   - Default: 2.5
   - Adjusted based on review quality

2. **Interval**: Days until next review
   - First review: 1 day
   - Second review: 6 days
   - Subsequent: previous_interval × ease_factor

3. **Repetitions**: Number of successful consecutive reviews
   - Resets to 0 on failed review (quality < 3)
   - Increments on successful review (quality ≥ 3)

### Review Quality Scale

Quality ratings range from 0 to 5:

- **0 (Blackout)**: Complete blackout, no recall
- **1 (Incorrect - Hard)**: Incorrect response, but correct answer remembered
- **2 (Incorrect - Easy)**: Incorrect response, but correct answer seemed easy
- **3 (Correct - Hard)**: Correct response with significant difficulty
- **4 (Correct - Hesitation)**: Correct response after some hesitation
- **5 (Perfect)**: Perfect response, immediate recall

### Ease Factor Calculation

The ease factor is updated using the formula:

```
EF' = EF + (0.1 - (5 - q) × (0.08 + (5 - q) × 0.02))
```

Where:
- `EF'` is the new ease factor
- `EF` is the current ease factor
- `q` is the quality rating (0-5)

The ease factor is clamped to the range [1.3, 3.0].

## Adaptive Enhancements

### Performance Tracking

The service tracks user performance history for each flashcard:
- Stores recent quality scores (last 30 reviews)
- Calculates average quality and success rate
- Detects performance trends (improving, stable, declining)

### Adaptive Adjustments

Based on performance trends, the service applies adjustments:

#### High Performance (avg_quality ≥ 4.5, success_rate ≥ 0.9)
- Increase interval by 20%
- Increase ease factor by 0.1
- Optimizes for efficiency

#### Improving Trend (trend > 0.5, success_rate ≥ 0.7)
- Maintain current schedule
- Encourages continued progress

#### Low Performance (avg_quality < 3.0 or success_rate < 0.5)
- Reduce interval by 30%
- Reduce ease factor by 0.1
- Optimizes for retention

#### Declining Trend (trend < -0.5)
- Reduce interval by 20%
- Early intervention to prevent forgetting

### Difficulty Adjustment

The service can recommend difficulty adjustments based on performance:

- **Increase Difficulty**: avg_quality ≥ 4.5 and success_rate ≥ 0.9
  - Easy → Medium → Hard
  
- **Decrease Difficulty**: avg_quality < 2.5 or success_rate < 0.4
  - Hard → Medium → Easy

Requires at least 5 reviews before adjustment.

## API Reference

### SpacedRepetitionService

#### `calculate_next_review(flashcard, user_id, quality) -> RepetitionSchedule`

Calculate the next review schedule based on user performance.

**Parameters:**
- `flashcard` (Flashcard): Flashcard to schedule
- `user_id` (str): User identifier
- `quality` (int): Review quality (0-5)

**Returns:**
- `RepetitionSchedule`: Next review date and updated parameters

**Example:**
```python
service = SpacedRepetitionService()
schedule = service.calculate_next_review(
    flashcard=my_flashcard,
    user_id="user-123",
    quality=ReviewQuality.PERFECT,
)
print(f"Next review: {schedule.next_review}")
print(f"Interval: {schedule.interval_days} days")
```

#### `get_due_flashcards(flashcards, user_id) -> List[Flashcard]`

Get flashcards that are due for review.

**Parameters:**
- `flashcards` (List[Flashcard]): List of flashcards to check
- `user_id` (str): User identifier

**Returns:**
- `List[Flashcard]`: Flashcards due for review

**Example:**
```python
due_cards = service.get_due_flashcards(all_flashcards, "user-123")
print(f"You have {len(due_cards)} cards to review")
```

#### `get_user_statistics(user_id, flashcards) -> Dict`

Get spaced repetition statistics for a user.

**Parameters:**
- `user_id` (str): User identifier
- `flashcards` (List[Flashcard]): User's flashcards

**Returns:**
- `Dict`: Statistics including:
  - `total_cards`: Total number of flashcards
  - `due_today`: Cards due today
  - `due_this_week`: Cards due this week
  - `mastered_cards`: Cards with 5+ repetitions
  - `average_ease_factor`: Average ease factor
  - `total_reviews`: Total reviews performed
  - `average_quality`: Average review quality

**Example:**
```python
stats = service.get_user_statistics("user-123", flashcards)
print(f"Mastered: {stats['mastered_cards']}/{stats['total_cards']}")
```

#### `adjust_difficulty(flashcard, user_id) -> DifficultyLevel`

Recommend difficulty adjustment based on performance.

**Parameters:**
- `flashcard` (Flashcard): Flashcard to adjust
- `user_id` (str): User identifier

**Returns:**
- `DifficultyLevel`: Recommended difficulty level

**Example:**
```python
new_difficulty = service.adjust_difficulty(flashcard, "user-123")
if new_difficulty != flashcard.difficulty:
    print(f"Recommend changing difficulty to {new_difficulty}")
```

#### `reset_flashcard(flashcard) -> None`

Reset a flashcard's spaced repetition data.

**Parameters:**
- `flashcard` (Flashcard): Flashcard to reset

**Example:**
```python
service.reset_flashcard(flashcard)
# Flashcard now has default repetition data
```

## Data Models

### SpacedRepetitionData

```python
class SpacedRepetitionData(BaseModel):
    ease_factor: float = 2.5        # Ease factor (1.3 to 3.0)
    interval: int = 1               # Current interval in days
    repetitions: int = 0            # Number of successful repetitions
    last_reviewed: Optional[datetime] = None  # Last review timestamp
    next_review: Optional[datetime] = None    # Next scheduled review
```

### RepetitionSchedule

```python
class RepetitionSchedule(BaseModel):
    flashcard_id: str               # Flashcard identifier
    next_review: datetime           # Next review date/time
    interval_days: int              # Interval in days
    ease_factor: float              # Current ease factor
```

## Usage Examples

### Basic Review Session

```python
from src.services.quiz_generation import SpacedRepetitionService, ReviewQuality

service = SpacedRepetitionService()

# User reviews a flashcard
schedule = service.calculate_next_review(
    flashcard=flashcard,
    user_id="user-123",
    quality=ReviewQuality.PERFECT,
)

print(f"Great! Review again in {schedule.interval_days} days")
```

### Daily Review Workflow

```python
# Get cards due today
due_cards = service.get_due_flashcards(all_flashcards, user_id)

# Review each card
for card in due_cards:
    print(f"Q: {card.question}")
    user_answer = input("Your answer: ")
    
    # Determine quality based on correctness
    quality = ReviewQuality.PERFECT if user_answer == card.answer else ReviewQuality.CORRECT_HARD
    
    # Schedule next review
    schedule = service.calculate_next_review(card, user_id, quality)
    print(f"Next review: {schedule.next_review.strftime('%Y-%m-%d')}")
```

### Performance Monitoring

```python
# Get user statistics
stats = service.get_user_statistics(user_id, flashcards)

print(f"Progress Report:")
print(f"  Total Cards: {stats['total_cards']}")
print(f"  Mastered: {stats['mastered_cards']}")
print(f"  Due Today: {stats['due_today']}")
print(f"  Average Quality: {stats['average_quality']:.2f}/5.0")
```

### Adaptive Difficulty

```python
# Check if difficulty should be adjusted
for card in flashcards:
    new_difficulty = service.adjust_difficulty(card, user_id)
    
    if new_difficulty != card.difficulty:
        print(f"Card {card.id}: {card.difficulty} → {new_difficulty}")
        card.difficulty = new_difficulty
```

## Testing

The implementation includes comprehensive unit tests covering:

1. **Basic SM-2 Algorithm**
   - First, second, and subsequent reviews
   - Failed reviews and progress reset
   - Ease factor adjustments

2. **Adaptive Features**
   - High performance adjustments
   - Low performance adjustments
   - Performance trend detection

3. **Utility Functions**
   - Getting due flashcards
   - User statistics calculation
   - Difficulty adjustment
   - Flashcard reset

4. **Edge Cases**
   - Invalid quality values
   - Ease factor bounds
   - Interval limits
   - Performance history limits

Run tests with:
```bash
python -m pytest tests/unit/test_spaced_repetition_service.py -v
```

## Performance Considerations

### Memory Management

- Performance history is limited to 30 recent reviews per card
- Prevents memory bloat for long-term users
- Sufficient for trend analysis

### Interval Limits

- Maximum interval: 365 days (1 year)
- Prevents date overflow errors
- Reasonable for practical learning scenarios

### Computational Complexity

- `calculate_next_review`: O(1) - constant time
- `get_due_flashcards`: O(n) - linear in number of cards
- `get_user_statistics`: O(n) - linear in number of cards
- `adjust_difficulty`: O(1) - constant time

## Integration with Quiz Generation Service

The spaced repetition service integrates with the flashcard generator:

```python
from src.services.quiz_generation import FlashcardGenerator, SpacedRepetitionService

# Generate flashcards
generator = FlashcardGenerator(bedrock_client)
flashcards = generator.generate_flashcards(content, count=10)

# Each flashcard has initialized SpacedRepetitionData
for card in flashcards:
    assert card.repetition_data.ease_factor == 2.5
    assert card.repetition_data.interval == 1
    assert card.repetition_data.repetitions == 0

# Use spaced repetition for scheduling
service = SpacedRepetitionService()
schedule = service.calculate_next_review(flashcards[0], user_id, quality)
```

## Future Enhancements

Potential improvements for future versions:

1. **Personalized Learning Curves**
   - Adjust algorithm parameters per user
   - Learn optimal intervals from user data

2. **Context-Aware Scheduling**
   - Consider time of day preferences
   - Account for study session length

3. **Forgetting Curve Integration**
   - Model individual forgetting curves
   - Predict optimal review timing

4. **Multi-Modal Learning**
   - Different schedules for different content types
   - Adjust for audio, visual, text content

5. **Social Learning Features**
   - Compare performance with peers
   - Collaborative flashcard decks

## References

- [SuperMemo 2 Algorithm](https://www.supermemo.com/en/archives1990-2015/english/ol/sm2)
- [Spaced Repetition Research](https://en.wikipedia.org/wiki/Spaced_repetition)
- [Ebbinghaus Forgetting Curve](https://en.wikipedia.org/wiki/Forgetting_curve)

## Requirement Validation

This implementation satisfies **Requirement 2.5**:

> "WHEN a user reviews flashcards, THE System SHALL implement spaced repetition algorithms to optimize learning retention"

The implementation provides:
- ✅ Spaced repetition scheduling based on SM-2 algorithm
- ✅ Adaptive difficulty based on user performance
- ✅ Long-term retention optimization through performance tracking
- ✅ Comprehensive testing and documentation
- ✅ Integration with flashcard generation service
