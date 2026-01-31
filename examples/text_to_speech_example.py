"""Example usage of text-to-speech service."""

import os
from pathlib import Path

from src.services.voice_interface import (
    TextToSpeechService,
    VoiceInterfaceService,
)


def example_basic_synthesis():
    """Example: Basic text-to-speech synthesis."""
    print("\n=== Basic Text-to-Speech Synthesis ===")
    
    tts_service = TextToSpeechService()
    
    # Synthesize English text
    text = "Hello! Welcome to the AI Learning Assistant."
    result = tts_service.synthesize_speech(
        text=text,
        language_code="en-US",
    )
    
    print(f"Text: {text}")
    print(f"Voice: {result.voice_id}")
    print(f"Language: {result.language_code}")
    print(f"Audio size: {len(result.audio_data)} bytes")
    print(f"Audio format: {result.audio_format}")
    
    # Save to file
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "basic_synthesis.mp3"
    with open(output_file, "wb") as f:
        f.write(result.audio_data)
    print(f"Audio saved to: {output_file}")


def example_indian_language_synthesis():
    """Example: Text-to-speech with Indian languages."""
    print("\n=== Indian Language Text-to-Speech ===")
    
    tts_service = TextToSpeechService()
    
    # Hindi synthesis with bilingual voice (Aditi)
    hindi_text = "नमस्ते! आपका स्वागत है।"
    result = tts_service.synthesize_speech(
        text=hindi_text,
        language_code="hi-IN",
    )
    
    print(f"Text: {hindi_text}")
    print(f"Voice: {result.voice_id}")
    print(f"Language: {result.language_code}")
    print(f"Is bilingual: {result.metadata.get('is_bilingual', False)}")
    print(f"Audio size: {len(result.audio_data)} bytes")
    
    # Save to file
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "hindi_synthesis.mp3"
    with open(output_file, "wb") as f:
        f.write(result.audio_data)
    print(f"Audio saved to: {output_file}")


def example_bilingual_voices():
    """Example: Using bilingual voices."""
    print("\n=== Bilingual Voices ===")
    
    tts_service = TextToSpeechService()
    
    # Get bilingual voices
    bilingual_voices = tts_service.get_bilingual_voices()
    print("Available bilingual voices:")
    for voice_id, languages in bilingual_voices.items():
        print(f"  {voice_id}: {', '.join(languages)}")
    
    # Use Aditi for both English and Hindi
    print("\nUsing Aditi for English:")
    english_result = tts_service.synthesize_speech(
        text="Hello from India",
        language_code="en-IN",
        voice_id="Aditi",
    )
    print(f"  Voice: {english_result.voice_id}")
    print(f"  Language: {english_result.language_code}")
    
    print("\nUsing Aditi for Hindi:")
    hindi_result = tts_service.synthesize_speech(
        text="भारत से नमस्कार",
        language_code="hi-IN",
        voice_id="Aditi",
    )
    print(f"  Voice: {hindi_result.voice_id}")
    print(f"  Language: {hindi_result.language_code}")


def example_user_preferences():
    """Example: Text-to-speech with user preferences."""
    print("\n=== Text-to-Speech with User Preferences ===")
    
    tts_service = TextToSpeechService()
    
    # User preferences
    user_preferences = {
        "language": "hi",  # Short code
        "voice_id": "Aditi",
        "voice_enabled": True,
    }
    
    text = "यह एक परीक्षण है।"
    result = tts_service.synthesize_with_preferences(
        text=text,
        user_preferences=user_preferences,
    )
    
    print(f"Text: {text}")
    print(f"User preferred language: {user_preferences['language']}")
    print(f"User preferred voice: {user_preferences['voice_id']}")
    print(f"Synthesized with voice: {result.voice_id}")
    print(f"Synthesized in language: {result.language_code}")


def example_voice_round_trip():
    """Example: Complete voice round-trip (speech-to-text and text-to-speech)."""
    print("\n=== Voice Round-Trip Example ===")
    
    voice_service = VoiceInterfaceService()
    
    # Simulate audio input (in real scenario, this would be actual audio)
    print("Note: This example requires actual audio input.")
    print("In a real scenario, you would:")
    print("1. Capture audio from microphone")
    print("2. Process it with voice_service.process_voice_input()")
    print("3. Generate audio response with voice_service.generate_audio_response()")
    print("4. Or use voice_service.process_voice_round_trip() for complete flow")
    
    # Example of generating audio response
    response_text = "I understand your question. Let me help you with that."
    result = voice_service.generate_audio_response(
        text=response_text,
        language_code="en-US",
    )
    
    print(f"\nGenerated audio response:")
    print(f"  Text: {response_text}")
    print(f"  Voice: {result.voice_id}")
    print(f"  Audio size: {len(result.audio_data)} bytes")


def example_available_voices():
    """Example: Get available voices."""
    print("\n=== Available Voices ===")
    
    tts_service = TextToSpeechService()
    
    # Get all available voices
    print("Getting available voices (this may take a moment)...")
    
    # Get Indian language voices
    indian_voices = tts_service.get_indian_language_voices()
    print(f"\nIndian language voices available for {len(indian_voices)} languages:")
    for lang_code, voices in indian_voices.items():
        print(f"\n{lang_code}:")
        for voice in voices:
            voice_id = voice.get("Id", "Unknown")
            gender = voice.get("Gender", "Unknown")
            is_bilingual = voice.get("IsBilingual", False)
            bilingual_str = " (Bilingual)" if is_bilingual else ""
            print(f"  - {voice_id} ({gender}){bilingual_str}")


def example_voice_validation():
    """Example: Validate voice preferences."""
    print("\n=== Voice Preference Validation ===")
    
    tts_service = TextToSpeechService()
    
    # Test valid combinations
    test_cases = [
        ("Aditi", "hi-IN", "Valid - Aditi supports Hindi"),
        ("Aditi", "en-IN", "Valid - Aditi supports Indian English"),
        ("Kajal", "ta-IN", "Valid - Kajal supports Tamil"),
        ("Joanna", "en-US", "Valid - Joanna supports US English"),
        ("Aditi", "ta-IN", "Invalid - Aditi doesn't support Tamil"),
        ("Joanna", "hi-IN", "Invalid - Joanna doesn't support Hindi"),
    ]
    
    print("Testing voice-language combinations:")
    for voice_id, language_code, description in test_cases:
        is_valid = tts_service.validate_voice_for_language(
            voice_id=voice_id,
            language_code=language_code,
        )
        status = "✓" if is_valid else "✗"
        print(f"  {status} {voice_id} + {language_code}: {description}")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Text-to-Speech Service Examples")
    print("=" * 60)
    
    try:
        # Note: These examples will work with actual AWS credentials
        # For demonstration, we'll show the structure
        
        print("\nNote: These examples require AWS credentials to be configured.")
        print("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
        print("Or configure AWS CLI with 'aws configure'.")
        
        # Check if AWS credentials are available
        if not os.environ.get("AWS_ACCESS_KEY_ID"):
            print("\nWarning: AWS credentials not found in environment.")
            print("Examples will show structure but may not execute fully.")
        
        # Run examples
        example_basic_synthesis()
        example_indian_language_synthesis()
        example_bilingual_voices()
        example_user_preferences()
        example_voice_round_trip()
        example_available_voices()
        example_voice_validation()
        
        print("\n" + "=" * 60)
        print("Examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure AWS credentials are configured correctly.")


if __name__ == "__main__":
    main()
