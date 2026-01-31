"""Example usage of quiz session and scoring system."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from src.services.quiz_generation.quiz_session_service import (
    QuizSessionService,
    PerformanceAnalytics,
)
from src.services.quiz_generation.quiz_generator import QuizGenerator
from src.shared.aws_clients.bedrock_client import BedrockClient
from src.shared.models.content import ProcessedContent, Summary, SummaryType, Concept


def create_sample_content():
    """Create sample processed content for quiz generation."""
    summary = Summary(
        id="summary-1",
        content_id="content-1",
        type=SummaryType.BRIEF,
        text="""
        Python is a high-level, interpreted programming language known for its simplicity 
        and readability. It supports multiple programming paradigms including procedural, 
        object-oriented, and functional programming. Python's extensive standard library 
        and large ecosystem of third-party packages make it suitable for various applications 
        from web development to data science and machine learning.
        """,
        key_points=[
            "High-level interpreted language",
            "Emphasizes code readability",
            "Supports multiple programming paradigms",
            "Extensive standard library",
            "Large ecosystem of packages",
        ],
        hierarchical_structure=[],
        generated_at=datetime.utcnow(),
    )

    concepts = [
        Concept(
            name="Python",
            description="A high-level programming language",
            importance=0.9,
            related_concepts=["Programming", "Interpreted Language"],
        ),
        Concept(
            name="Programming Paradigms",
            description="Different approaches to programming",
            importance=0.8,
            related_concepts=["OOP", "Functional Programming"],
        ),
    ]

    return ProcessedContent(
        id="content-1",
        original_content="Python programming language overview...",
        summary=summary,
        key_points=summary.key_points,
        concepts=concepts,
        language="en",
        processing_time=1.5,
        metadata={"word_count": 150},
    )


def example_quiz_session():
    """Demonstrate quiz session management and scoring."""
    print("=" * 80)
    print("Quiz Session and Scoring System Example")
    print("=" * 80)
    print()

    # Initialize services
    print("1. Initializing services...")
    bedrock_client = BedrockClient()
    quiz_generator = QuizGenerator(bedrock_client=bedrock_client)
    session_service = QuizSessionService()
    analytics = PerformanceAnalytics()
    print("   ✓ Services initialized")
    print()

    # Create sample content
    print("2. Creating sample content...")
    content = create_sample_content()
    print(f"   ✓ Content created: {content.id}")
    print(f"   ✓ Summary: {content.summary.text[:100]}...")
    print()

    # Generate a quiz
    print("3. Generating quiz from content...")
    try:
        quiz = quiz_generator.generate_quiz(
            content=content,
            title="Python Basics Quiz",
            question_count=5,
            time_limit=300,  # 5 minutes
            passing_score=70,
        )
        print(f"   ✓ Quiz generated: {quiz.title}")
        print(f"   ✓ Questions: {len(quiz.questions)}")
        print(f"   ✓ Time limit: {quiz.time_limit} seconds")
        print(f"   ✓ Passing score: {quiz.passing_score}%")
        print()
    except Exception as e:
        print(f"   ✗ Error generating quiz: {e}")
        print("   Note: This example requires AWS credentials and Bedrock access")
        print("   Using a mock quiz for demonstration...")
        
        # Create a simple mock quiz for demonstration
        from src.shared.models.quiz import Quiz, Question, QuestionType, DifficultyLevel
        
        quiz = Quiz(
            id="quiz-demo",
            content_id=content.id,
            title="Python Basics Quiz",
            questions=[
                Question(
                    id="q1",
                    type=QuestionType.MULTIPLE_CHOICE,
                    text="What is Python?",
                    options=[
                        "A snake",
                        "A programming language",
                        "A type of food",
                        "A mathematical concept",
                    ],
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
                    explanation="Python is an interpreted language, not compiled.",
                    points=1,
                    difficulty=DifficultyLevel.MEDIUM,
                ),
                Question(
                    id="q3",
                    type=QuestionType.FILL_IN_BLANK,
                    text="Python emphasizes code _____.",
                    options=None,
                    correct_answer="readability",
                    explanation="Python emphasizes code readability and simplicity.",
                    points=1,
                    difficulty=DifficultyLevel.EASY,
                ),
            ],
            time_limit=300,
            passing_score=70,
            created_at=datetime.utcnow(),
        )
        print(f"   ✓ Mock quiz created: {quiz.title}")
        print()

    # Start a quiz session
    print("4. Starting quiz session...")
    user_id = "user-demo-123"
    session = session_service.start_session(quiz=quiz, user_id=user_id)
    print(f"   ✓ Session started: {session.session_id}")
    print(f"   ✓ User: {user_id}")
    print()

    # Display quiz questions and simulate taking the quiz
    print("5. Taking the quiz...")
    print()
    
    # Simulate user answers - answer all questions correctly
    for i, question in enumerate(quiz.questions, 1):
        print(f"   Question {i}/{len(quiz.questions)}:")
        print(f"   {question.text}")
        
        if question.options:
            for option in question.options:
                print(f"      - {option}")
        
        # For demo, always answer correctly
        user_answer = question.correct_answer
        print(f"   Your answer: {user_answer}")
        
        # Get immediate feedback
        feedback = session_service.submit_answer(
            session_id=session.session_id,
            question_id=question.id,
            answer=user_answer,
        )
        
        if feedback["is_correct"]:
            print(f"   ✓ Correct! (+{feedback['points_earned']} point)")
        else:
            print(f"   ✗ Incorrect. Correct answer: {feedback['correct_answer']}")
        
        print(f"   Explanation: {feedback['explanation']}")
        print()

    # Check progress
    print("6. Checking progress...")
    progress = session_service.get_session_progress(session.session_id)
    print(f"   ✓ Answered: {progress['answered_questions']}/{progress['total_questions']}")
    print(f"   ✓ Progress: {progress['progress_percentage']:.1f}%")
    print(f"   ✓ Time elapsed: {progress['time_elapsed_seconds']:.1f} seconds")
    print()

    # Complete the session
    print("7. Completing quiz session...")
    result = session_service.complete_session(session.session_id)
    print(f"   ✓ Quiz completed!")
    print(f"   ✓ Score: {result.score}%")
    print(f"   ✓ Correct answers: {result.correct_count}/{result.total_questions}")
    print(f"   ✓ Time taken: {result.time_taken} seconds")
    
    if result.score >= quiz.passing_score:
        print(f"   🎉 PASSED! (Required: {quiz.passing_score}%)")
    else:
        print(f"   ❌ FAILED (Required: {quiz.passing_score}%)")
    print()

    # Record result for analytics
    print("8. Recording result for analytics...")
    analytics.record_result(result)
    print("   ✓ Result recorded")
    print()

    # Simulate additional quiz attempts for analytics
    print("9. Simulating additional quiz attempts...")
    from src.shared.models.quiz import QuizResult
    
    additional_results = [
        QuizResult(
            quiz_id=quiz.id,
            user_id=user_id,
            answers={"q1": "A", "q2": "True", "q3": "speed"},
            score=33,
            correct_count=1,
            total_questions=3,
            time_taken=180,
            completed_at=datetime.utcnow(),
        ),
        QuizResult(
            quiz_id=quiz.id,
            user_id=user_id,
            answers={"q1": "A programming language", "q2": "False", "q3": "simplicity"},
            score=66,
            correct_count=2,
            total_questions=3,
            time_taken=240,
            completed_at=datetime.utcnow(),
        ),
    ]
    
    for res in additional_results:
        analytics.record_result(res)
    
    print(f"   ✓ Recorded {len(additional_results)} additional attempts")
    print()

    # Get user performance analytics
    print("10. User Performance Analytics:")
    print("-" * 80)
    performance = analytics.get_user_performance(user_id)
    print(f"   Total quizzes completed: {performance['total_quizzes']}")
    print(f"   Average score: {performance['average_score']}%")
    print(f"   Total questions answered: {performance['total_questions_answered']}")
    print(f"   Total correct: {performance['total_correct']}")
    print(f"   Accuracy rate: {performance['accuracy_rate']}%")
    print(f"   Average time: {performance['average_time']:.1f} seconds")
    print(f"   Best score: {performance['best_score']}%")
    print()
    
    print("   Recent scores:")
    for i, score in enumerate(performance['recent_scores'][:3], 1):
        print(f"      {i}. Quiz {score['quiz_id']}: {score['score']}% "
              f"({score['correct']}/{score['total']} correct)")
    print()

    # Get quiz statistics
    print("11. Quiz Statistics:")
    print("-" * 80)
    quiz_stats = analytics.get_quiz_statistics(quiz.id)
    print(f"   Total attempts: {quiz_stats['total_attempts']}")
    print(f"   Average score: {quiz_stats['average_score']}%")
    print(f"   Pass rate: {quiz_stats['pass_rate']}%")
    print(f"   Average time: {quiz_stats['average_time']:.1f} seconds")
    print()
    
    print("   Score distribution:")
    for range_key, count in sorted(quiz_stats['score_distribution'].items()):
        print(f"      {range_key}: {count} attempt(s)")
    print()

    # Get overall statistics
    print("12. Overall System Statistics:")
    print("-" * 80)
    overall = analytics.get_overall_statistics()
    print(f"   Total quizzes completed: {overall['total_quizzes_completed']}")
    print(f"   Total questions answered: {overall['total_questions_answered']}")
    print(f"   Overall accuracy: {overall['overall_accuracy']}%")
    print(f"   Unique users: {overall['unique_users']}")
    print(f"   Average score: {overall['average_score']}%")
    print()

    print("=" * 80)
    print("Quiz Session Example Complete!")
    print("=" * 80)


def example_session_abandonment():
    """Demonstrate session abandonment."""
    print("\n" + "=" * 80)
    print("Session Abandonment Example")
    print("=" * 80)
    print()

    from src.shared.models.quiz import Quiz, Question, QuestionType, DifficultyLevel

    # Create a simple quiz
    quiz = Quiz(
        id="quiz-abandon",
        content_id="content-1",
        title="Test Quiz",
        questions=[
            Question(
                id="q1",
                type=QuestionType.TRUE_FALSE,
                text="Test question",
                options=["True", "False"],
                correct_answer="True",
                explanation="Test",
                points=1,
                difficulty=DifficultyLevel.EASY,
            ),
        ],
        time_limit=300,
        passing_score=70,
        created_at=datetime.utcnow(),
    )

    session_service = QuizSessionService()
    
    print("1. Starting quiz session...")
    session = session_service.start_session(quiz=quiz, user_id="user-123")
    print(f"   ✓ Session started: {session.session_id}")
    print()

    print("2. User decides to abandon the quiz...")
    session_service.abandon_session(session.session_id)
    print("   ✓ Session abandoned")
    print()

    print("3. Verifying session is removed...")
    retrieved = session_service.get_session(session.session_id)
    if retrieved is None:
        print("   ✓ Session successfully removed from active sessions")
    else:
        print("   ✗ Session still exists")
    print()


if __name__ == "__main__":
    # Run the main example
    example_quiz_session()
    
    # Run the abandonment example
    example_session_abandonment()
