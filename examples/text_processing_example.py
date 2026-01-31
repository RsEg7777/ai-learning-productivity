"""
Example usage of the TextProcessor for content analysis and summarization.

This example demonstrates:
1. Processing short text with brief summary
2. Processing medium text with detailed summary
3. Processing large text with hierarchical summary
4. Extracting key concepts from content
"""

from src.services.content_processing.text_processor import TextProcessor
from src.shared.aws_clients.bedrock_client import BedrockClient
from src.shared.models.content import SummaryType


def example_brief_summary():
    """Example: Process short text with brief summary."""
    print("=" * 80)
    print("Example 1: Brief Summary for Short Text")
    print("=" * 80)
    
    # Initialize clients
    bedrock_client = BedrockClient(region="us-east-1")
    text_processor = TextProcessor(bedrock_client=bedrock_client)
    
    # Short text content
    text = """
    Machine learning is a subset of artificial intelligence that enables systems 
    to learn and improve from experience without being explicitly programmed. 
    It focuses on developing computer programs that can access data and use it 
    to learn for themselves.
    """
    
    # Process text
    result = text_processor.process_text(
        text=text,
        language="en",
        summary_type=SummaryType.BRIEF,
    )
    
    print(f"\nOriginal Text Length: {len(text)} characters")
    print(f"Word Count: {result.metadata['word_count']}")
    print(f"Processing Time: {result.processing_time:.2f} seconds")
    print(f"\nSummary Type: {result.summary.type.value}")
    print(f"\nSummary:\n{result.summary.text}")
    print(f"\nKey Points:")
    for i, point in enumerate(result.key_points, 1):
        print(f"  {i}. {point}")
    print(f"\nConcepts Extracted:")
    for concept in result.concepts:
        print(f"  - {concept.name} (importance: {concept.importance:.2f})")
        print(f"    {concept.description}")


def example_detailed_summary():
    """Example: Process medium text with detailed summary."""
    print("\n" + "=" * 80)
    print("Example 2: Detailed Summary for Medium Text")
    print("=" * 80)
    
    # Initialize clients
    bedrock_client = BedrockClient(region="us-east-1")
    text_processor = TextProcessor(bedrock_client=bedrock_client)
    
    # Medium-length text content
    text = """
    Deep learning is a subset of machine learning that uses neural networks with 
    multiple layers (hence "deep") to progressively extract higher-level features 
    from raw input. For example, in image processing, lower layers may identify 
    edges, while higher layers may identify concepts relevant to a human such as 
    digits, letters, or faces.
    
    The key advantage of deep learning is that it can automatically discover the 
    representations needed for feature detection or classification from raw data. 
    This replaces manual feature engineering and allows a machine to both learn 
    the features and use them to perform a specific task.
    
    Deep learning models are trained using large amounts of labeled data and neural 
    network architectures that contain many layers. The "deep" in deep learning 
    refers to the number of layers through which the data is transformed. More 
    layers enable the model to learn more complex patterns.
    """ * 10  # Repeat to make it longer
    
    # Process text
    result = text_processor.process_text(
        text=text,
        language="en",
        summary_type=SummaryType.DETAILED,
    )
    
    print(f"\nOriginal Text Length: {len(text)} characters")
    print(f"Word Count: {result.metadata['word_count']}")
    print(f"Processing Time: {result.processing_time:.2f} seconds")
    print(f"\nSummary Type: {result.summary.type.value}")
    print(f"\nSummary:\n{result.summary.text}")


def example_hierarchical_summary():
    """Example: Process large text with hierarchical summary."""
    print("\n" + "=" * 80)
    print("Example 3: Hierarchical Summary for Large Text")
    print("=" * 80)
    
    # Initialize clients
    bedrock_client = BedrockClient(region="us-east-1")
    text_processor = TextProcessor(bedrock_client=bedrock_client)
    
    # Large text content (>10,000 words)
    text = """
    Artificial Intelligence (AI) is transforming the world in unprecedented ways.
    From healthcare to finance, from transportation to entertainment, AI is 
    revolutionizing how we live and work. This comprehensive guide explores the 
    various aspects of AI and its impact on society.
    """ * 3000  # Repeat to exceed 10,000 words
    
    # Process text (will automatically use hierarchical summary)
    result = text_processor.process_text(
        text=text,
        language="en",
    )
    
    print(f"\nOriginal Text Length: {len(text)} characters")
    print(f"Word Count: {result.metadata['word_count']}")
    print(f"Processing Time: {result.processing_time:.2f} seconds")
    print(f"\nSummary Type: {result.summary.type.value}")
    print(f"\nHierarchical Structure:")
    for node in result.summary.hierarchical_structure:
        print(f"\n{node.text}")
        for child in node.children:
            print(f"  - {child.text}")


def example_multilingual_processing():
    """Example: Process text in different languages."""
    print("\n" + "=" * 80)
    print("Example 4: Multilingual Text Processing")
    print("=" * 80)
    
    # Initialize clients
    bedrock_client = BedrockClient(region="us-east-1")
    text_processor = TextProcessor(bedrock_client=bedrock_client)
    
    # French text
    french_text = """
    L'intelligence artificielle est une branche de l'informatique qui vise à 
    créer des machines capables de simuler l'intelligence humaine. Elle englobe 
    diverses techniques telles que l'apprentissage automatique, le traitement 
    du langage naturel et la vision par ordinateur.
    """
    
    # Process French text
    result = text_processor.process_text(
        text=french_text,
        language="fr",
    )
    
    print(f"\nLanguage: {result.language}")
    print(f"Word Count: {result.metadata['word_count']}")
    print(f"Processing Time: {result.processing_time:.2f} seconds")
    print(f"\nSummary:\n{result.summary.text}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Text Processing Examples with Amazon Bedrock")
    print("=" * 80)
    print("\nNote: These examples require AWS credentials and Bedrock access.")
    print("Make sure you have configured your AWS credentials properly.")
    print("=" * 80)
    
    try:
        # Run examples
        example_brief_summary()
        example_detailed_summary()
        example_hierarchical_summary()
        example_multilingual_processing()
        
        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("\nMake sure you have:")
        print("1. AWS credentials configured")
        print("2. Access to Amazon Bedrock")
        print("3. Appropriate IAM permissions")
