"""Example demonstrating flashcard generation from content."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.quiz_generation.flashcard_generator import FlashcardGenerator
from src.shared.aws_clients.bedrock_client import BedrockClient
from src.shared.models.content import ProcessedContent, Summary, SummaryType, Concept
from datetime import datetime
import uuid


def main():
    """Demonstrate flashcard generation."""
    print("=" * 80)
    print("Flashcard Generation Example")
    print("=" * 80)
    print()

    # Initialize Bedrock client
    print("Initializing Bedrock client...")
    bedrock_client = BedrockClient(region="us-east-1")
    
    # Initialize flashcard generator
    flashcard_generator = FlashcardGenerator(bedrock_client=bedrock_client)
    print("✓ Flashcard generator initialized")
    print()

    # Sample content about machine learning
    content_text = """
    Machine learning is a subset of artificial intelligence that focuses on 
    developing algorithms and statistical models that enable computers to 
    learn from and make predictions or decisions based on data. Unlike 
    traditional programming where explicit instructions are provided, machine 
    learning systems improve their performance through experience.
    
    There are three main types of machine learning: supervised learning, 
    unsupervised learning, and reinforcement learning. Supervised learning 
    uses labeled data to train models, unsupervised learning finds patterns 
    in unlabeled data, and reinforcement learning learns through trial and 
    error with rewards and penalties.
    
    Common applications of machine learning include image recognition, natural 
    language processing, recommendation systems, fraud detection, and autonomous 
    vehicles. The field continues to evolve rapidly with advances in deep 
    learning and neural networks.
    """

    # Create processed content
    print("Creating processed content...")
    summary = Summary(
        id=str(uuid.uuid4()),
        content_id="ml-content-001",
        type=SummaryType.BRIEF,
        text="Machine learning enables computers to learn from data and improve through experience.",
        key_points=[
            "Machine learning is a subset of AI",
            "Systems learn from data without explicit programming",
            "Three main types: supervised, unsupervised, and reinforcement learning",
            "Applications include image recognition, NLP, and recommendation systems",
        ],
        hierarchical_structure=[],
        generated_at=datetime.utcnow(),
    )

    concepts = [
        Concept(
            name="Machine Learning",
            description="A method of data analysis that automates analytical model building",
            importance=0.9,
            related_concepts=["AI", "Deep Learning"],
        ),
        Concept(
            name="Supervised Learning",
            description="Learning from labeled training data",
            importance=0.7,
            related_concepts=["Classification", "Regression"],
        ),
        Concept(
            name="Neural Networks",
            description="Computing systems inspired by biological neural networks",
            importance=0.8,
            related_concepts=["Deep Learning", "AI"],
        ),
    ]

    processed_content = ProcessedContent(
        id="ml-content-001",
        original_content=content_text,
        summary=summary,
        key_points=summary.key_points,
        concepts=concepts,
        language="en",
        processing_time=1.5,
        metadata={"word_count": 150},
    )
    print("✓ Processed content created")
    print()

    # Generate flashcards
    print("Generating flashcards...")
    print("(This will use Amazon Bedrock to generate intelligent Q&A pairs)")
    print()
    
    try:
        flashcards = flashcard_generator.generate_flashcards(
            content=processed_content,
            count=12,  # Request 12 flashcards
        )
        
        print(f"✓ Successfully generated {len(flashcards)} flashcards")
        print()
        
        # Display flashcards
        print("=" * 80)
        print("Generated Flashcards")
        print("=" * 80)
        print()
        
        # Group by difficulty
        easy_cards = [f for f in flashcards if f.difficulty.value == "easy"]
        medium_cards = [f for f in flashcards if f.difficulty.value == "medium"]
        hard_cards = [f for f in flashcards if f.difficulty.value == "hard"]
        
        print(f"Difficulty Distribution:")
        print(f"  Easy: {len(easy_cards)}")
        print(f"  Medium: {len(medium_cards)}")
        print(f"  Hard: {len(hard_cards)}")
        print()
        
        # Display each flashcard
        for i, flashcard in enumerate(flashcards, 1):
            print(f"Flashcard {i}")
            print(f"  ID: {flashcard.id}")
            print(f"  Difficulty: {flashcard.difficulty.value.upper()}")
            print(f"  Tags: {', '.join(flashcard.tags)}")
            print(f"  Question: {flashcard.question}")
            print(f"  Answer: {flashcard.answer}")
            print(f"  Spaced Repetition:")
            print(f"    - Ease Factor: {flashcard.repetition_data.ease_factor}")
            print(f"    - Interval: {flashcard.repetition_data.interval} day(s)")
            print(f"    - Repetitions: {flashcard.repetition_data.repetitions}")
            print()
        
        print("=" * 80)
        print("Example completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"✗ Error generating flashcards: {e}")
        print()
        print("Note: This example requires AWS credentials and access to Amazon Bedrock.")
        print("Make sure you have:")
        print("  1. AWS credentials configured (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
        print("  2. Access to Amazon Bedrock in your AWS account")
        print("  3. Appropriate IAM permissions for Bedrock")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
