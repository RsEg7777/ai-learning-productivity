"""Example demonstrating quiz generation with multiple question types."""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.quiz_generation.quiz_generator import QuizGenerator
from src.shared.aws_clients.bedrock_client import BedrockClient
from src.shared.models.content import ProcessedContent, Summary, SummaryType, Concept
from src.shared.models.quiz import QuestionType, DifficultyLevel


def create_sample_content() -> ProcessedContent:
    """Create sample processed content for demonstration."""
    summary = Summary(
        id="summary-1",
        content_id="content-1",
        type=SummaryType.DETAILED,
        text="""
        Python is a high-level, interpreted programming language known for its simplicity and readability.
        It was created by Guido van Rossum and first released in 1991. Python supports multiple programming
        paradigms including procedural, object-oriented, and functional programming. The language emphasizes
        code readability with its use of significant indentation. Python has a comprehensive standard library
        and a large ecosystem of third-party packages available through PyPI (Python Package Index).
        
        Key features of Python include:
        - Dynamic typing and automatic memory management
        - Support for multiple programming paradigms
        - Extensive standard library
        - Large and active community
        - Cross-platform compatibility
        
        Python is widely used in various domains including web development, data science, machine learning,
        automation, and scientific computing. Popular frameworks include Django and Flask for web development,
        NumPy and Pandas for data analysis, and TensorFlow and PyTorch for machine learning.
        """,
        key_points=[
            "Python is a high-level, interpreted programming language",
            "Created by Guido van Rossum in 1991",
            "Supports multiple programming paradigms",
            "Emphasizes code readability with significant indentation",
            "Has comprehensive standard library and large ecosystem",
            "Used in web development, data science, ML, and automation",
        ],
        hierarchical_structure=[],
        generated_at=datetime.utcnow(),
    )

    concepts = [
        Concept(
            name="Python",
            description="A high-level programming language",
            importance=1.0,
            related_concepts=["Programming", "Interpreted Language"],
        ),
        Concept(
            name="Dynamic Typing",
            description="Type checking performed at runtime",
            importance=0.8,
            related_concepts=["Type System", "Runtime"],
        ),
        Concept(
            name="Object-Oriented Programming",
            description="Programming paradigm based on objects",
            importance=0.7,
            related_concepts=["Classes", "Inheritance", "Encapsulation"],
        ),
        Concept(
            name="Standard Library",
            description="Collection of modules included with Python",
            importance=0.6,
            related_concepts=["Modules", "Packages"],
        ),
    ]

    return ProcessedContent(
        id="content-1",
        original_content="Python programming language overview...",
        summary=summary,
        key_points=summary.key_points,
        concepts=concepts,
        language="en",
        processing_time=2.5,
        metadata={"source": "example"},
    )


def print_quiz(quiz):
    """Print quiz details in a readable format."""
    print("\n" + "=" * 80)
    print(f"QUIZ: {quiz.title}")
    print("=" * 80)
    print(f"Content ID: {quiz.content_id}")
    print(f"Number of Questions: {len(quiz.questions)}")
    print(f"Time Limit: {quiz.time_limit if quiz.time_limit else 'No limit'}")
    print(f"Passing Score: {quiz.passing_score}%")
    print(f"Created: {quiz.created_at}")
    print("=" * 80)

    # Count question types and difficulties
    type_counts = {}
    difficulty_counts = {}
    
    for question in quiz.questions:
        type_counts[question.type] = type_counts.get(question.type, 0) + 1
        difficulty_counts[question.difficulty] = difficulty_counts.get(question.difficulty, 0) + 1

    print("\nQuestion Distribution:")
    print(f"  Multiple Choice: {type_counts.get(QuestionType.MULTIPLE_CHOICE, 0)}")
    print(f"  True/False: {type_counts.get(QuestionType.TRUE_FALSE, 0)}")
    print(f"  Fill-in-Blank: {type_counts.get(QuestionType.FILL_IN_BLANK, 0)}")
    
    print("\nDifficulty Distribution:")
    print(f"  Easy: {difficulty_counts.get(DifficultyLevel.EASY, 0)}")
    print(f"  Medium: {difficulty_counts.get(DifficultyLevel.MEDIUM, 0)}")
    print(f"  Hard: {difficulty_counts.get(DifficultyLevel.HARD, 0)}")

    print("\n" + "-" * 80)
    print("QUESTIONS:")
    print("-" * 80)

    for i, question in enumerate(quiz.questions, 1):
        print(f"\nQuestion {i} [{question.type.value.upper()}] - {question.difficulty.value.capitalize()}")
        print(f"Text: {question.text}")
        
        if question.options:
            print("Options:")
            for j, option in enumerate(question.options):
                print(f"  {chr(65 + j)}) {option}")
        
        print(f"Correct Answer: {question.correct_answer}")
        print(f"Explanation: {question.explanation}")
        print(f"Points: {question.points}")

    print("\n" + "=" * 80)


def main():
    """Main example function."""
    print("Quiz Generation Example")
    print("=" * 80)
    print("\nThis example demonstrates quiz generation with multiple question types.")
    print("Note: This is a demonstration using mock data. In production, it would")
    print("connect to Amazon Bedrock for AI-powered question generation.")
    print()

    # Create sample content
    print("Creating sample content...")
    content = create_sample_content()
    print(f"✓ Created content with {len(content.key_points)} key points")
    print(f"✓ Content has {len(content.concepts)} concepts")

    # Initialize quiz generator
    print("\nInitializing quiz generator...")
    bedrock_client = BedrockClient()
    quiz_generator = QuizGenerator(bedrock_client=bedrock_client)
    print("✓ Quiz generator initialized")

    # Note about AWS credentials
    print("\n" + "!" * 80)
    print("NOTE: This example requires AWS credentials and Bedrock access.")
    print("If you don't have AWS configured, the quiz generation will fail.")
    print("The example demonstrates the API structure and expected behavior.")
    print("!" * 80)

    try:
        # Generate quiz with default settings
        print("\n\nExample 1: Generate quiz with default settings (10 questions)")
        print("-" * 80)
        quiz1 = quiz_generator.generate_quiz(
            content=content,
            title="Python Basics Quiz",
        )
        print_quiz(quiz1)

        # Generate quiz with custom settings
        print("\n\nExample 2: Generate quiz with custom settings (15 questions, 20 min limit)")
        print("-" * 80)
        quiz2 = quiz_generator.generate_quiz(
            content=content,
            title="Python Advanced Quiz",
            question_count=15,
            time_limit=1200,  # 20 minutes
            passing_score=80,
        )
        print_quiz(quiz2)

        # Generate smaller quiz
        print("\n\nExample 3: Generate quick quiz (5 questions)")
        print("-" * 80)
        quiz3 = quiz_generator.generate_quiz(
            content=content,
            title="Python Quick Quiz",
            question_count=5,
            time_limit=300,  # 5 minutes
            passing_score=60,
        )
        print_quiz(quiz3)

        print("\n✓ All examples completed successfully!")

    except Exception as e:
        print(f"\n✗ Error generating quiz: {e}")
        print("\nThis is expected if AWS credentials are not configured.")
        print("The quiz generator requires:")
        print("  1. AWS credentials configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
        print("  2. Access to Amazon Bedrock service")
        print("  3. Appropriate IAM permissions for Bedrock")
        
        # Show what the quiz structure would look like
        print("\n" + "=" * 80)
        print("EXPECTED QUIZ STRUCTURE (if AWS was configured):")
        print("=" * 80)
        print("""
        Quiz:
          - ID: unique identifier
          - Title: "Python Basics Quiz"
          - Content ID: reference to source content
          - Questions: List of Question objects
            * Multiple Choice (50%): 4 options, 1 correct
            * True/False (30%): statement with T/F answer
            * Fill-in-Blank (20%): sentence with blank to fill
          - Difficulty Distribution:
            * Easy (30%): Basic recall questions
            * Medium (50%): Understanding questions
            * Hard (20%): Application questions
          - Time Limit: optional time constraint
          - Passing Score: percentage needed to pass
          - Created At: timestamp
        
        Each Question includes:
          - Unique ID
          - Type (multiple_choice, true_false, fill_in_blank)
          - Question text
          - Options (for multiple choice and true/false)
          - Correct answer
          - Explanation
          - Points value
          - Difficulty level
        """)


if __name__ == "__main__":
    main()
