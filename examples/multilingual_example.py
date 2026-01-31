"""
Example usage of the multilingual support system.

This example demonstrates:
1. Language detection
2. Content processing in multiple languages
3. Translation with technical term preservation
4. Handling user input in Indian languages
5. Language context switching
"""

from src.services.multilingual.multilingual_service import MultilingualService


def main():
    """Demonstrate multilingual support features."""
    
    # Initialize the service
    service = MultilingualService()
    
    print("=" * 80)
    print("AI Learning Assistant - Multilingual Support Demo")
    print("=" * 80)
    
    # Example 1: Detect and process English content
    print("\n1. Processing English Content")
    print("-" * 80)
    english_text = "Machine learning is a subset of artificial intelligence that enables computers to learn from data."
    
    try:
        result = service.detect_and_process(english_text)
        print(f"Text: {english_text}")
        print(f"Detected Language: {result['detection']['language_name']} ({result['detection']['language_code']})")
        print(f"Confidence: {result['detection']['confidence']:.2f}")
        print(f"Is Indian Language: {result['detection']['is_indian_language']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Detect and process Hindi content
    print("\n2. Processing Hindi Content")
    print("-" * 80)
    hindi_text = "मशीन लर्निंग कृत्रिम बुद्धिमत्ता का एक उपसमुच्चय है"
    
    try:
        result = service.detect_and_process(hindi_text)
        print(f"Text: {hindi_text}")
        print(f"Detected Language: {result['detection']['language_name']} ({result['detection']['language_code']})")
        print(f"Confidence: {result['detection']['confidence']:.2f}")
        print(f"Is Indian Language: {result['detection']['is_indian_language']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Translate Hindi to English
    print("\n3. Translating Hindi to English")
    print("-" * 80)
    
    try:
        result = service.translate_between_languages(
            hindi_text,
            source_language="hi",
            target_language="en",
            preserve_technical_terms=True
        )
        print(f"Original (Hindi): {hindi_text}")
        print(f"Translated (English): {result['translated_text']}")
        print(f"Technical Terms Preserved: {result['technical_terms_preserved']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 4: Handle user input in Tamil
    print("\n4. Handling User Input in Tamil")
    print("-" * 80)
    tamil_text = "இயந்திர கற்றல் என்றால் என்ன?"
    
    try:
        result = service.handle_user_input(tamil_text)
        print(f"User Input: {tamil_text}")
        print(f"Detected Language: {result['detected_language']['language_name']}")
        print(f"Response Language: {result['response_language']}")
        print(f"Should Translate: {result['should_translate']}")
        print("\nNote: System will respond in Tamil since input is in an Indian language")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 5: Language context switching
    print("\n5. Language Context Switching")
    print("-" * 80)
    
    try:
        # User starts in English
        print("Previous conversation was in: English (en)")
        
        # User switches to Bengali
        bengali_text = "এখন বাংলায় কথা বলি"
        result = service.maintain_language_context(
            bengali_text,
            previous_language="en"
        )
        
        print(f"Current Input: {bengali_text}")
        print(f"Current Language: {result['current_language']['language_name']}")
        print(f"Language Switched: {result['language_switched']}")
        print(f"Context Maintained: {result['context_maintained']}")
        if 'switch_message' in result:
            print(f"Message: {result['switch_message']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 6: Get supported languages
    print("\n6. Supported Languages")
    print("-" * 80)
    
    try:
        languages = service.get_supported_languages()
        print(f"Total Supported Languages: {languages['total_count']}")
        print(f"Indian Languages: {languages['indian_count']}")
        print("\nIndian Languages:")
        for code, name in languages['indian_languages'].items():
            print(f"  - {name} ({code})")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 7: Validate language support
    print("\n7. Language Validation")
    print("-" * 80)
    
    test_languages = ["hi", "ta", "en", "fr"]
    for lang_code in test_languages:
        try:
            validation = service.validate_language_support(lang_code)
            print(f"{lang_code}: {validation['language_name']} - "
                  f"Supported: {validation['is_supported']}, "
                  f"Indian: {validation['is_indian_language']}")
        except Exception as e:
            print(f"{lang_code}: Error - {e}")
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
