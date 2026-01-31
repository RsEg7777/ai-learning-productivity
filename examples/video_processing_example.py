"""Example usage of video processing with Amazon Transcribe."""

import os
import sys
from io import BytesIO
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.content_processing import VideoProcessor, TextProcessor
from src.shared.aws_clients.bedrock_client import BedrockClient
from src.shared.aws_clients.transcribe_client import TranscribeClient
from src.shared.aws_clients.s3_client import S3Client
from src.shared.models.content import SummaryType


def main():
    """Demonstrate video processing functionality."""
    
    print("=" * 80)
    print("Video Processing with Amazon Transcribe - Example")
    print("=" * 80)
    print()
    
    # Initialize AWS clients
    print("Initializing AWS clients...")
    bedrock_client = BedrockClient(region="us-east-1")
    transcribe_client = TranscribeClient(region="us-east-1")
    s3_client = S3Client(
        bucket_name=os.getenv("AWS_S3_BUCKET", "ai-learning-assistant-content"),
        region="us-east-1",
    )
    
    # Initialize processors
    text_processor = TextProcessor(bedrock_client=bedrock_client)
    video_processor = VideoProcessor(
        text_processor=text_processor,
        transcribe_client=transcribe_client,
        s3_client=s3_client,
    )
    
    print("✓ AWS clients initialized")
    print()
    
    # Example 1: Process a video file
    print("-" * 80)
    print("Example 1: Process Video File")
    print("-" * 80)
    
    # In a real scenario, you would load a video file
    # For this example, we'll show the expected usage
    
    video_file_path = "path/to/your/video.mp4"
    
    if os.path.exists(video_file_path):
        print(f"Processing video: {video_file_path}")
        
        with open(video_file_path, "rb") as f:
            video_data = BytesIO(f.read())
        
        try:
            # Process video with transcription and summarization
            processed_content = video_processor.process_video(
                video_file=video_data,
                filename="lecture_video.mp4",
                language="en-US",  # English (US)
                summary_type=SummaryType.DETAILED,
            )
            
            print(f"✓ Video processed successfully!")
            print()
            print(f"Processing time: {processed_content.processing_time:.2f} seconds")
            print(f"Language: {processed_content.language}")
            print()
            
            print("Summary:")
            print("-" * 40)
            print(processed_content.summary.text)
            print()
            
            print("Key Points:")
            print("-" * 40)
            for i, point in enumerate(processed_content.key_points, 1):
                print(f"{i}. {point}")
            print()
            
            print("Extracted Concepts:")
            print("-" * 40)
            for concept in processed_content.concepts:
                print(f"- {concept.name} (importance: {concept.importance:.2f})")
                print(f"  {concept.description}")
            print()
            
            print("Metadata:")
            print("-" * 40)
            for key, value in processed_content.metadata.items():
                print(f"  {key}: {value}")
            print()
            
        except Exception as e:
            print(f"✗ Error processing video: {e}")
    else:
        print(f"Note: Video file not found at {video_file_path}")
        print("This is a demonstration of the expected usage.")
    
    print()
    
    # Example 2: Extract audio only
    print("-" * 80)
    print("Example 2: Extract Audio from Video")
    print("-" * 80)
    
    if os.path.exists(video_file_path):
        print(f"Extracting audio from: {video_file_path}")
        
        with open(video_file_path, "rb") as f:
            video_data = BytesIO(f.read())
        
        try:
            # Extract audio without transcription
            audio_data = video_processor.extract_audio_only(
                video_file=video_data,
                filename="lecture_video.mp4",
            )
            
            print(f"✓ Audio extracted successfully!")
            print(f"Audio size: {len(audio_data.getvalue())} bytes")
            
            # Save audio to file
            output_path = "extracted_audio.mp3"
            with open(output_path, "wb") as f:
                f.write(audio_data.getvalue())
            
            print(f"✓ Audio saved to: {output_path}")
            print()
            
        except Exception as e:
            print(f"✗ Error extracting audio: {e}")
    else:
        print("Note: This example shows how to extract audio from video.")
        print("The audio is saved as an MP3 file for further processing.")
    
    print()
    
    # Example 3: Get video metadata
    print("-" * 80)
    print("Example 3: Extract Video Metadata")
    print("-" * 80)
    
    if os.path.exists(video_file_path):
        print(f"Extracting metadata from: {video_file_path}")
        
        with open(video_file_path, "rb") as f:
            video_data = BytesIO(f.read())
        
        try:
            # Get video metadata
            metadata = video_processor.get_video_metadata(
                video_file=video_data,
                filename="lecture_video.mp4",
            )
            
            print(f"✓ Metadata extracted successfully!")
            print()
            print("Video Information:")
            print("-" * 40)
            for key, value in metadata.items():
                print(f"  {key}: {value}")
            print()
            
        except Exception as e:
            print(f"✗ Error extracting metadata: {e}")
    else:
        print("Note: This example shows how to extract video metadata.")
        print("Metadata includes duration, resolution, codec, etc.")
    
    print()
    
    # Example 4: Process video in different languages
    print("-" * 80)
    print("Example 4: Multilingual Video Processing")
    print("-" * 80)
    
    print("Supported languages for transcription:")
    print("-" * 40)
    
    languages = [
        ("en-US", "English (US)"),
        ("en-GB", "English (UK)"),
        ("hi-IN", "Hindi (India)"),
        ("ta-IN", "Tamil (India)"),
        ("te-IN", "Telugu (India)"),
        ("bn-IN", "Bengali (India)"),
        ("es-ES", "Spanish (Spain)"),
        ("fr-FR", "French (France)"),
        ("de-DE", "German (Germany)"),
        ("ja-JP", "Japanese (Japan)"),
    ]
    
    for code, name in languages:
        print(f"  {code}: {name}")
    
    print()
    print("Example usage for Hindi video:")
    print("-" * 40)
    print("""
    processed_content = video_processor.process_video(
        video_file=video_data,
        filename="hindi_lecture.mp4",
        language="hi-IN",  # Hindi (India)
        summary_type=SummaryType.DETAILED,
    )
    """)
    print()
    
    # Example 5: Error handling
    print("-" * 80)
    print("Example 5: Error Handling")
    print("-" * 80)
    
    print("The video processor handles various error scenarios:")
    print("-" * 40)
    print("1. Unsupported video formats")
    print("   - Supported: .mp4, .avi, .mov, .mkv, .webm")
    print()
    print("2. Processing timeouts")
    print("   - Maximum processing time: 5 minutes (300 seconds)")
    print()
    print("3. Empty transcriptions")
    print("   - Returns error if no speech detected in video")
    print()
    print("4. Audio extraction failures")
    print("   - Handles ffmpeg errors gracefully")
    print()
    print("5. Transcription service errors")
    print("   - Handles Amazon Transcribe API errors")
    print()
    
    print("Example error handling:")
    print("-" * 40)
    print("""
    from src.shared.utils.errors import (
        ContentProcessingError,
        ProcessingTimeoutError,
        ValidationError,
    )
    
    try:
        processed_content = video_processor.process_video(
            video_file=video_data,
            filename="video.mp4",
            language="en-US",
        )
    except ValidationError as e:
        print(f"Validation error: {e.message}")
        print(f"Details: {e.details}")
    except ProcessingTimeoutError as e:
        print(f"Processing timeout: {e.message}")
        print(f"Time limit: {e.details['time_limit']}s")
    except ContentProcessingError as e:
        print(f"Processing error: {e.message}")
        print(f"Error code: {e.error_code}")
    """)
    print()
    
    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print("The VideoProcessor provides three main capabilities:")
    print()
    print("1. Full Video Processing (process_video)")
    print("   - Extracts audio from video")
    print("   - Transcribes audio using Amazon Transcribe")
    print("   - Generates summaries and extracts key concepts")
    print("   - Supports multiple languages including Indian languages")
    print()
    print("2. Audio Extraction (extract_audio_only)")
    print("   - Extracts audio track from video")
    print("   - Returns audio as MP3 format")
    print("   - Useful for separate audio processing")
    print()
    print("3. Metadata Extraction (get_video_metadata)")
    print("   - Extracts video properties (duration, resolution, codec)")
    print("   - Uses ffprobe for detailed metadata")
    print("   - No transcription or processing required")
    print()
    print("Requirements:")
    print("  - ffmpeg installed and available in PATH")
    print("  - AWS credentials configured")
    print("  - S3 bucket for temporary audio storage")
    print("  - Amazon Transcribe access")
    print("  - Amazon Bedrock access for summarization")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
