"""
Example usage of the Voice Interface Service for speech-to-text processing.

This example demonstrates:
1. Real-time speech transcription
2. Support for Indian languages with 90%+ accuracy
3. Audio quality enhancement and noise reduction
4. Language detection from audio
"""

import os
from pathlib import Path

from src.services.voice_interface import (
    VoiceInterfaceService,
    SpeechToTextService,
    AudioProcessor,
)
from src.shared.aws_clients.transcribe_client import TranscribeClient
from src.shared.aws_clients.s3_client import S3Client


def example_transcribe_english_audio():
    """Example: Transcribe English audio with enhancements."""
    print("\n=== Example 1: Transcribe English Audio ===")
    
    # Initialize the voice interface service
    voice_service = VoiceInterfaceService()
    
    # Simulate audio data (in production, this would be actual audio bytes)
    # For demonstration, we'll show the API usage
    audio_data = b"simulated audio data"  # Replace with actual audio
    
    try:
        # Process voice input with audio enhancements
        result = voice_service.process_voice_input(
            audio_data=audio_data,
            language_code="en-US",
            audio_format="mp3",
            enable_noise_reduction=True,
            enable_quality_enhancement=True,
        )
        
        print(f"Transcribed Text: {result.text}")
        print(f"Confidence: {result.confidence:.2%}")
        print(f"Language: {result.language}")
        print(f"Processing Time: {result.metadata.get('processing_time', 0):.2f}s")
        
        # Display word-level timestamps
        if result.timestamps:
            print("\nWord-level Timestamps:")
            for ts in result.timestamps[:5]:  # Show first 5 words
                print(f"  {ts['word']}: {ts['start_time']:.2f}s - {ts['end_time']:.2f}s "
                      f"(confidence: {ts['confidence']:.2%})")
    
    except Exception as e:
        print(f"Error: {e}")


def example_transcribe_hindi_audio():
    """Example: Transcribe Hindi audio (Indian language)."""
    print("\n=== Example 2: Transcribe Hindi Audio ===")
    
    voice_service = VoiceInterfaceService()
    
    # Simulate Hindi audio data
    audio_data = b"simulated hindi audio data"
    
    try:
        # Process Hindi voice input
        result = voice_service.process_voice_input(
            audio_data=audio_data,
            language_code="hi-IN",  # Hindi (India)
            audio_format="mp3",
            enable_noise_reduction=True,
            enable_quality_enhancement=True,
        )
        
        print(f"Transcribed Text (Hindi): {result.text}")
        print(f"Confidence: {result.confidence:.2%}")
        print(f"Language: {result.language}")
        
        # Verify 90%+ accuracy requirement for Indian languages
        if result.confidence >= 0.90:
            print("✓ Meets 90%+ accuracy requirement for Indian languages")
        else:
            print("⚠ Below 90% accuracy threshold")
    
    except Exception as e:
        print(f"Error: {e}")


def example_transcribe_multiple_indian_languages():
    """Example: Transcribe audio in multiple Indian languages."""
    print("\n=== Example 3: Multiple Indian Languages ===")
    
    voice_service = VoiceInterfaceService()
    
    # Get supported languages
    supported_languages = voice_service.get_supported_languages()
    
    print("Supported Indian Languages:")
    for lang_code, full_code in supported_languages.items():
        if voice_service.is_indian_language(full_code):
            print(f"  {lang_code}: {full_code}")
    
    # Example languages to transcribe
    test_languages = [
        ("hi-IN", "Hindi"),
        ("ta-IN", "Tamil"),
        ("te-IN", "Telugu"),
        ("bn-IN", "Bengali"),
    ]
    
    for lang_code, lang_name in test_languages:
        print(f"\nTranscribing {lang_name} audio...")
        audio_data = f"simulated {lang_name} audio".encode()
        
        try:
            result = voice_service.process_voice_input(
                audio_data=audio_data,
                language_code=lang_code,
                audio_format="mp3",
            )
            print(f"  Language: {lang_name}")
            print(f"  Confidence: {result.confidence:.2%}")
            print(f"  Status: {'✓ Pass' if result.confidence >= 0.90 else '⚠ Low confidence'}")
        
        except Exception as e:
            print(f"  Error: {e}")


def example_audio_quality_assessment():
    """Example: Assess audio quality before transcription."""
    print("\n=== Example 4: Audio Quality Assessment ===")
    
    voice_service = VoiceInterfaceService()
    
    # Simulate different quality audio samples
    audio_samples = [
        (b"x" * 5000, "Low quality (5KB)"),
        (b"x" * 30000, "Medium quality (30KB)"),
        (b"x" * 60000, "High quality (60KB)"),
    ]
    
    for audio_data, description in audio_samples:
        print(f"\n{description}:")
        
        # Assess audio quality
        assessment = voice_service.validate_audio_quality(
            audio_data=audio_data,
            audio_format="mp3",
        )
        
        print(f"  Quality: {assessment['quality']}")
        print(f"  Size: {assessment['size_kb']:.2f} KB")
        
        if assessment.get('recommendations'):
            print("  Recommendations:")
            for rec in assessment['recommendations']:
                print(f"    - {rec}")


def example_audio_enhancement():
    """Example: Audio enhancement with noise reduction."""
    print("\n=== Example 5: Audio Enhancement ===")
    
    # Initialize audio processor
    audio_processor = AudioProcessor()
    
    # Simulate noisy audio
    noisy_audio = b"simulated noisy audio data" * 100
    
    print(f"Original audio size: {len(noisy_audio)} bytes")
    
    # Enhance audio with both noise reduction and quality enhancement
    enhanced_audio, metadata = audio_processor.enhance_audio(
        audio_data=noisy_audio,
        audio_format="mp3",
        enable_noise_reduction=True,
        enable_quality_enhancement=True,
    )
    
    print(f"Enhanced audio size: {len(enhanced_audio)} bytes")
    print(f"Noise reduction applied: {metadata['noise_reduction_applied']}")
    print(f"Quality enhancement applied: {metadata['quality_enhancement_applied']}")
    
    # Note: In production, you would use libraries like pydub, librosa, or noisereduce
    # for actual audio processing. This is a placeholder implementation.
    if 'enhancement_note' in metadata:
        print(f"\nNote: {metadata['enhancement_note']}")


def example_language_detection():
    """Example: Detect language from audio."""
    print("\n=== Example 6: Language Detection ===")
    
    voice_service = VoiceInterfaceService()
    
    # Simulate audio in unknown language
    audio_data = b"simulated audio in unknown language"
    
    try:
        # Detect language
        detected_language = voice_service.detect_language(
            audio_data=audio_data,
            audio_format="mp3",
        )
        
        print(f"Detected Language: {detected_language}")
        
        # Check if it's an Indian language
        if voice_service.is_indian_language(detected_language):
            print("✓ Detected as Indian language")
        else:
            print("ℹ Not an Indian language")
    
    except Exception as e:
        print(f"Error: {e}")


def example_real_time_transcription():
    """Example: Real-time speech transcription workflow."""
    print("\n=== Example 7: Real-time Transcription Workflow ===")
    
    voice_service = VoiceInterfaceService()
    
    # Simulate a real-time transcription workflow
    print("Workflow Steps:")
    print("1. Receive audio stream from user")
    print("2. Assess audio quality")
    print("3. Enhance audio if needed")
    print("4. Transcribe to text")
    print("5. Return results with confidence scores")
    
    # Simulate audio stream
    from io import BytesIO
    audio_stream = BytesIO(b"simulated audio stream data")
    
    try:
        # Step 1: Assess quality
        audio_data = audio_stream.getvalue()
        assessment = voice_service.validate_audio_quality(audio_data, "mp3")
        print(f"\nAudio Quality: {assessment['quality']}")
        
        # Step 2: Transcribe with enhancements
        audio_stream.seek(0)  # Reset stream
        result = voice_service.transcribe_audio_stream(
            audio_stream=audio_stream,
            language_code="en-US",
            audio_format="mp3",
            enable_enhancements=True,
        )
        
        print(f"Transcription: {result.text}")
        print(f"Confidence: {result.confidence:.2%}")
        print(f"Processing Time: {result.metadata.get('processing_time', 0):.2f}s")
        
        # Step 3: Verify accuracy
        if result.confidence >= 0.90:
            print("✓ High confidence transcription")
        else:
            print("⚠ Low confidence - may need review")
    
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples."""
    print("=" * 70)
    print("Voice Interface Service Examples")
    print("=" * 70)
    
    print("\nNote: These examples use simulated audio data.")
    print("In production, replace with actual audio files or streams.")
    print("Ensure AWS credentials are configured for Amazon Transcribe.")
    
    # Run examples
    example_transcribe_english_audio()
    example_transcribe_hindi_audio()
    example_transcribe_multiple_indian_languages()
    example_audio_quality_assessment()
    example_audio_enhancement()
    example_language_detection()
    example_real_time_transcription()
    
    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
