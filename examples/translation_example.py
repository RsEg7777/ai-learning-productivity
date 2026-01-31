"""
Example usage of the Translation Service with Amazon Translate.

This example demonstrates:
1. Basic translation between languages
2. Technical term preservation during translation
3. Context maintenance across language switches
4. Batch translation
5. Translation quality validation
"""

import logging
from src.services.multilingual.translation_service import TranslationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_basic_translation():
    """Example 1: Basic translation from English to Hindi."""
    print("\n" + "="*80)
    print("Example 1: Basic Translation (English to Hindi)")
    print("="*80)
    
    service = TranslationService()
    
    text = "Machine learning is a powerful technology that enables computers to learn from data."
    
    result = service.translate(
        text=text,
        source_language="en",
        target_language="hi",
        preserve_technical_terms=True
    )
    
    print(f"\nOriginal (English):")
    print(f"  {text}")
    print(f"\nTranslated (Hindi):")
    print(f"  {result['translated_text']}")
    print(f"\nTechnical Terms Preserved:")
    for term in result['technical_terms_preserved']:
        print(f"  - {term}")


def example_technical_term_preservation():
    """Example 2: Translation with technical term preservation."""
    print("\n" + "="*80)
    print("Example 2: Technical Term Preservation")
    print("="*80)
    
    service = TranslationService()
    
    text = "Use the REST API with SDK version 2.5.1 to call getData() and fetchUser() functions."
    
    result = service.translate(
        text=text,
        source_language="en",
        target_language="hi",
        preserve_technical_terms=True
    )
    
    print(f"\nOriginal (English):")
    print(f"  {text}")
    print(f"\nTranslated (Hindi):")
    print(f"  {result['translated_text']}")
    print(f"\nTechnical Terms Preserved:")
    for term in result['technical_terms_preserved']:
        print(f"  - {term}")
    
    # Validate translation quality
    validation = service.validate_translation_quality(
        text,
        result['translated_text'],
        result['technical_terms_preserved']
    )
    
    print(f"\nTranslation Quality:")
    print(f"  Preservation Rate: {validation['preservation_rate']:.2%}")
    print(f"  Quality Score: {validation['quality_score']:.2%}")
    print(f"  Length Reasonable: {validation['length_reasonable']}")


def example_context_maintenance():
    """Example 3: Maintaining context across language switches."""
    print("\n" + "="*80)
    print("Example 3: Context Maintenance Across Language Switches")
    print("="*80)
    
    service = TranslationService()
    session_id = "demo_session_123"
    
    # First message in English
    text1 = "Let's discuss the REST API implementation"
    result1 = service.translate_with_context(
        text=text1,
        source_language="en",
        target_language="hi",
        session_id=session_id
    )
    
    print(f"\nMessage 1 (English to Hindi):")
    print(f"  Original: {text1}")
    print(f"  Translated: {result1['translated_text']}")
    print(f"  Context Maintained: {result1['context_maintained']}")
    
    # Second message continues the conversation
    text2 = "The API uses OAuth authentication for security"
    result2 = service.translate_with_context(
        text=text2,
        source_language="en",
        target_language="hi",
        session_id=session_id
    )
    
    print(f"\nMessage 2 (English to Hindi):")
    print(f"  Original: {text2}")
    print(f"  Translated: {result2['translated_text']}")
    print(f"  Context Maintained: {result2['context_maintained']}")
    
    # Third message - user switches to Hindi
    text3 = "OAuth टोकन कैसे काम करते हैं?"
    result3 = service.translate_with_context(
        text=text3,
        source_language="hi",
        target_language="en",
        session_id=session_id
    )
    
    print(f"\nMessage 3 (Hindi to English - Language Switch):")
    print(f"  Original: {text3}")
    print(f"  Translated: {result3['translated_text']}")
    print(f"  Context Maintained: {result3['context_maintained']}")
    
    # Get final context
    context = service.get_context(session_id)
    print(f"\nFinal Session Context:")
    print(f"  Technical Terms: {context['technical_terms']}")
    print(f"  Last Source Language: {context['last_source_language']}")
    print(f"  Last Target Language: {context['last_target_language']}")
    
    # Clean up
    service.clear_context(session_id)


def example_batch_translation():
    """Example 4: Batch translation of multiple texts."""
    print("\n" + "="*80)
    print("Example 4: Batch Translation")
    print("="*80)
    
    service = TranslationService()
    
    texts = [
        "Install the SDK using pip install sdk-name",
        "Configure your API key in the settings",
        "Call the getData() function to retrieve information",
        "Handle errors using try-except blocks"
    ]
    
    results = service.batch_translate(
        texts=texts,
        source_language="en",
        target_language="hi",
        preserve_technical_terms=True
    )
    
    print(f"\nTranslating {len(texts)} texts from English to Hindi:\n")
    for i, (original, result) in enumerate(zip(texts, results), 1):
        print(f"{i}. Original: {original}")
        print(f"   Translated: {result['translated_text']}")
        print(f"   Terms Preserved: {', '.join(result['technical_terms_preserved'][:3])}")
        print()


def example_multilingual_support():
    """Example 5: Translation across multiple Indian languages."""
    print("\n" + "="*80)
    print("Example 5: Multiple Indian Languages Support")
    print("="*80)
    
    service = TranslationService()
    
    text = "Use the API to access data"
    
    # Translate to different Indian languages
    languages = {
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi"
    }
    
    print(f"\nOriginal (English): {text}\n")
    print("Translations:")
    
    for lang_code, lang_name in languages.items():
        result = service.translate(
            text=text,
            source_language="en",
            target_language=lang_code,
            preserve_technical_terms=True
        )
        print(f"  {lang_name} ({lang_code}): {result['translated_text']}")


def example_bidirectional_translation():
    """Example 6: Bidirectional translation (English ↔ Hindi)."""
    print("\n" + "="*80)
    print("Example 6: Bidirectional Translation")
    print("="*80)
    
    service = TranslationService()
    
    # English to Hindi
    english_text = "The SDK provides methods to interact with the REST API"
    en_to_hi = service.translate(
        text=english_text,
        source_language="en",
        target_language="hi",
        preserve_technical_terms=True
    )
    
    print(f"\nEnglish to Hindi:")
    print(f"  Original: {english_text}")
    print(f"  Translated: {en_to_hi['translated_text']}")
    
    # Hindi to English
    hindi_text = "API का उपयोग करके डेटा प्राप्त करें"
    hi_to_en = service.translate(
        text=hindi_text,
        source_language="hi",
        target_language="en",
        preserve_technical_terms=True
    )
    
    print(f"\nHindi to English:")
    print(f"  Original: {hindi_text}")
    print(f"  Translated: {hi_to_en['translated_text']}")


def example_code_documentation_translation():
    """Example 7: Translating technical documentation with code snippets."""
    print("\n" + "="*80)
    print("Example 7: Technical Documentation Translation")
    print("="*80)
    
    service = TranslationService()
    
    documentation = """
    The getUserData() function retrieves user information from the database.
    It accepts a user_id parameter and returns a JSON object.
    Use the API key for authentication.
    """
    
    result = service.translate(
        text=documentation.strip(),
        source_language="en",
        target_language="hi",
        preserve_technical_terms=True
    )
    
    print(f"\nOriginal Documentation (English):")
    print(documentation)
    print(f"\nTranslated Documentation (Hindi):")
    print(result['translated_text'])
    print(f"\nTechnical Terms Preserved:")
    for term in result['technical_terms_preserved']:
        print(f"  - {term}")


def example_same_language_handling():
    """Example 8: Handling same source and target language."""
    print("\n" + "="*80)
    print("Example 8: Same Language Handling")
    print("="*80)
    
    service = TranslationService()
    
    text = "This text is already in English"
    
    result = service.translate(
        text=text,
        source_language="en",
        target_language="en"
    )
    
    print(f"\nOriginal: {text}")
    print(f"Translated: {result['translated_text']}")
    print(f"Same Language: {result['source_language'] == result['target_language']}")
    print(f"Text Unchanged: {text == result['translated_text']}")


def main():
    """Run all translation examples."""
    print("\n" + "="*80)
    print("TRANSLATION SERVICE EXAMPLES")
    print("Demonstrating Amazon Translate Integration")
    print("="*80)
    
    try:
        # Run all examples
        example_basic_translation()
        example_technical_term_preservation()
        example_context_maintenance()
        example_batch_translation()
        example_multilingual_support()
        example_bidirectional_translation()
        example_code_documentation_translation()
        example_same_language_handling()
        
        print("\n" + "="*80)
        print("All examples completed successfully!")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
