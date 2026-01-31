# Video Processing Implementation

## Overview

The Video Processing service provides comprehensive video content analysis using Amazon Transcribe for speech-to-text conversion and Amazon Bedrock for content summarization. This implementation fulfills **Requirement 1.2** from the AI Learning Assistant specification.

## Architecture

### Components

1. **VideoProcessor** (`src/services/content_processing/video_processor.py`)
   - Main service for video processing
   - Handles video upload, audio extraction, transcription, and summarization
   - Integrates with AWS services (S3, Transcribe, Bedrock)

2. **Dependencies**
   - **TextProcessor**: Processes transcribed text and generates summaries
   - **TranscribeClient**: Interfaces with Amazon Transcribe for speech-to-text
   - **S3Client**: Manages temporary audio file storage
   - **ffmpeg**: External tool for audio extraction from video

### Processing Flow

```
Video Upload
    ↓
Validate Format (.mp4, .avi, .mov, .mkv, .webm)
    ↓
Extract Audio (ffmpeg)
    ↓
Upload Audio to S3
    ↓
Transcribe Audio (Amazon Transcribe)
    ↓
Process Text (TextProcessor + Bedrock)
    ↓
Generate Summary & Extract Concepts
    ↓
Return ProcessedContent
    ↓
Cleanup (Delete temporary files)
```

## Features

### 1. Video Processing

**Method**: `process_video(video_file, filename, language, summary_type)`

Processes video content end-to-end:
- Extracts audio from video using ffmpeg
- Transcribes audio using Amazon Transcribe
- Generates summaries and extracts key concepts
- Returns structured ProcessedContent

**Parameters**:
- `video_file`: BytesIO object containing video data
- `filename`: Original filename (used for format detection)
- `language`: Language code (e.g., "en-US", "hi-IN")
- `summary_type`: Optional summary type (BRIEF, DETAILED, HIERARCHICAL)

**Returns**: `ProcessedContent` object with:
- Transcribed text
- Generated summary
- Key points
- Extracted concepts
- Processing metadata

**Time Limit**: 5 minutes (300 seconds) as per Requirement 1.2

### 2. Audio Extraction

**Method**: `extract_audio_only(video_file, filename)`

Extracts audio track from video without transcription:
- Useful for separate audio processing
- Returns audio as MP3 format
- No transcription or summarization

**Parameters**:
- `video_file`: BytesIO object containing video data
- `filename`: Original filename

**Returns**: BytesIO object containing MP3 audio data

### 3. Metadata Extraction

**Method**: `get_video_metadata(video_file, filename)`

Extracts video metadata without processing:
- Duration, file size, bit rate
- Video codec, resolution, frame rate
- Uses ffprobe for detailed information

**Parameters**:
- `video_file`: BytesIO object containing video data
- `filename`: Original filename

**Returns**: Dictionary with video metadata

## Supported Formats

### Video Formats
- MP4 (`.mp4`)
- AVI (`.avi`)
- MOV (`.mov`)
- MKV (`.mkv`)
- WebM (`.webm`)

### Audio Output
- MP3 format (16kHz, mono, 64kbps)
- Optimized for speech recognition

### Languages

Supports all Amazon Transcribe languages including:
- English: `en-US`, `en-GB`, `en-AU`, etc.
- Indian Languages: `hi-IN`, `ta-IN`, `te-IN`, `bn-IN`, `mr-IN`, `gu-IN`, `kn-IN`, `ml-IN`, `pa-IN`, `or-IN`
- Other Languages: Spanish, French, German, Japanese, Chinese, etc.

## Implementation Details

### Audio Extraction

Uses ffmpeg with optimized settings for speech:
```bash
ffmpeg -i video.mp4 -vn -acodec libmp3lame -ar 16000 -ac 1 -ab 64k audio.mp3
```

**Parameters**:
- `-vn`: No video (audio only)
- `-acodec libmp3lame`: MP3 codec
- `-ar 16000`: 16kHz sample rate (optimal for speech)
- `-ac 1`: Mono audio
- `-ab 64k`: 64kbps bitrate

### Transcription

Uses Amazon Transcribe with:
- Automatic language detection support
- Job-based processing with polling
- Automatic cleanup of transcription jobs
- Error handling and retry logic

### Temporary File Management

- Video and audio files stored in system temp directory
- Automatic cleanup in finally block
- S3 audio files deleted after transcription
- Robust error handling prevents file leaks

### Error Handling

Comprehensive error handling for:
1. **Validation Errors**: Invalid formats, missing files
2. **Processing Timeouts**: Exceeds 5-minute limit
3. **Audio Extraction Errors**: ffmpeg failures
4. **Transcription Errors**: Amazon Transcribe API errors
5. **Empty Transcriptions**: No speech detected in video

## Usage Examples

### Basic Video Processing

```python
from src.services.content_processing import VideoProcessor, TextProcessor
from src.shared.aws_clients import BedrockClient, TranscribeClient, S3Client
from io import BytesIO

# Initialize clients
bedrock_client = BedrockClient(region="us-east-1")
transcribe_client = TranscribeClient(region="us-east-1")
s3_client = S3Client(bucket_name="my-bucket", region="us-east-1")

# Initialize processors
text_processor = TextProcessor(bedrock_client=bedrock_client)
video_processor = VideoProcessor(
    text_processor=text_processor,
    transcribe_client=transcribe_client,
    s3_client=s3_client,
)

# Process video
with open("lecture.mp4", "rb") as f:
    video_data = BytesIO(f.read())

processed_content = video_processor.process_video(
    video_file=video_data,
    filename="lecture.mp4",
    language="en-US",
)

print(f"Summary: {processed_content.summary.text}")
print(f"Key Points: {processed_content.key_points}")
```

### Multilingual Processing

```python
# Process Hindi video
processed_content = video_processor.process_video(
    video_file=video_data,
    filename="hindi_lecture.mp4",
    language="hi-IN",  # Hindi (India)
)

# Process Tamil video
processed_content = video_processor.process_video(
    video_file=video_data,
    filename="tamil_lecture.mp4",
    language="ta-IN",  # Tamil (India)
)
```

### Extract Audio Only

```python
# Extract audio without transcription
audio_data = video_processor.extract_audio_only(
    video_file=video_data,
    filename="lecture.mp4",
)

# Save audio file
with open("extracted_audio.mp3", "wb") as f:
    f.write(audio_data.getvalue())
```

### Get Video Metadata

```python
# Extract metadata
metadata = video_processor.get_video_metadata(
    video_file=video_data,
    filename="lecture.mp4",
)

print(f"Duration: {metadata['duration']} seconds")
print(f"Resolution: {metadata['width']}x{metadata['height']}")
print(f"Codec: {metadata['video_codec']}")
```

### Error Handling

```python
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
    print(f"Supported formats: {e.details['supported_formats']}")
except ProcessingTimeoutError as e:
    print(f"Processing timeout: {e.message}")
    print(f"Time limit: {e.details['time_limit']}s")
except ContentProcessingError as e:
    print(f"Processing error: {e.message}")
```

## Testing

### Unit Tests

Comprehensive unit tests in `tests/unit/test_video_processor.py`:
- 27 test cases covering all functionality
- 91% code coverage
- Mocked AWS services and ffmpeg
- Tests for success and error scenarios

**Test Categories**:
1. Initialization and configuration
2. File extension and format validation
3. Language code conversion
4. Timeout checking
5. Temporary file management
6. Audio extraction (success and errors)
7. S3 upload operations
8. Transcription (success, timeout, errors)
9. End-to-end video processing
10. Audio-only extraction
11. Metadata extraction
12. Integration tests

### Running Tests

```bash
# Run all video processor tests
pytest tests/unit/test_video_processor.py -v

# Run with coverage
pytest tests/unit/test_video_processor.py --cov=src/services/content_processing/video_processor

# Run specific test
pytest tests/unit/test_video_processor.py::TestVideoProcessor::test_process_video_success -v
```

## Requirements Validation

### Requirement 1.2 Compliance

**Requirement**: "WHEN a user uploads video content, THE Content_Processor SHALL extract audio, transcribe it, and create a summary within 5 minutes"

**Implementation**:
✅ Video upload support (multiple formats)
✅ Audio extraction using ffmpeg
✅ Transcription using Amazon Transcribe
✅ Summary generation using Amazon Bedrock
✅ 5-minute timeout enforcement (300 seconds)
✅ Comprehensive error handling
✅ Cleanup of temporary resources

### Performance Characteristics

- **Audio Extraction**: ~5-15 seconds (depends on video length)
- **S3 Upload**: ~2-5 seconds (depends on audio size)
- **Transcription**: ~30-120 seconds (depends on audio length)
- **Summarization**: ~10-30 seconds (depends on text length)
- **Total**: Typically 1-3 minutes for standard lecture videos

## Dependencies

### System Requirements

1. **ffmpeg**: Required for audio extraction
   - Install: `sudo apt-get install ffmpeg` (Linux)
   - Install: `brew install ffmpeg` (macOS)
   - Install: Download from https://ffmpeg.org/ (Windows)

2. **ffprobe**: Included with ffmpeg, used for metadata extraction

### Python Dependencies

```
boto3>=1.34.0          # AWS SDK
botocore>=1.34.0       # AWS SDK core
pydantic>=2.5.0        # Data validation
```

### AWS Services

1. **Amazon S3**: Temporary audio file storage
2. **Amazon Transcribe**: Speech-to-text conversion
3. **Amazon Bedrock**: Text summarization and concept extraction

### AWS Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket/temp/transcribe/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "transcribe:StartTranscriptionJob",
        "transcribe:GetTranscriptionJob",
        "transcribe:DeleteTranscriptionJob"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*:*:model/*"
    }
  ]
}
```

## Configuration

### Environment Variables

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# S3 Configuration
AWS_S3_BUCKET=ai-learning-assistant-content

# Transcribe Configuration (optional)
TRANSCRIBE_MAX_WAIT_SECONDS=300
TRANSCRIBE_POLL_INTERVAL=5
```

### VideoProcessor Configuration

```python
# Custom timeout (default: 300 seconds)
video_processor.VIDEO_PROCESSING_TIMEOUT = 600  # 10 minutes

# Supported formats (default: .mp4, .avi, .mov, .mkv, .webm)
video_processor.SUPPORTED_VIDEO_FORMATS = [".mp4", ".mov"]
```

## Limitations

1. **File Size**: Maximum 500 MB per video (configurable)
2. **Duration**: Optimal for videos under 60 minutes
3. **Format**: Only supports common video formats
4. **Audio**: Requires audio track in video
5. **Language**: Limited to Amazon Transcribe supported languages
6. **Processing Time**: Maximum 5 minutes (enforced timeout)

## Future Enhancements

1. **Parallel Processing**: Process multiple videos concurrently
2. **Streaming Support**: Process video streams in real-time
3. **Speaker Diarization**: Identify different speakers in video
4. **Subtitle Generation**: Generate SRT/VTT subtitle files
5. **Video Segmentation**: Split long videos into chapters
6. **Custom Vocabulary**: Support domain-specific terminology
7. **Quality Detection**: Assess audio quality before transcription
8. **Batch Processing**: Process multiple videos in batch

## Troubleshooting

### Common Issues

1. **ffmpeg not found**
   - Ensure ffmpeg is installed and in PATH
   - Test: `ffmpeg -version`

2. **Transcription timeout**
   - Check video length (longer videos take more time)
   - Verify Amazon Transcribe service availability
   - Check AWS credentials and permissions

3. **Empty transcription**
   - Verify video has audio track
   - Check audio quality (clear speech required)
   - Try different language code

4. **S3 upload errors**
   - Verify S3 bucket exists and is accessible
   - Check AWS credentials and permissions
   - Ensure sufficient S3 storage quota

5. **Processing timeout**
   - Video may be too long (>60 minutes)
   - Network issues with AWS services
   - Consider increasing timeout limit

## References

- [Amazon Transcribe Documentation](https://docs.aws.amazon.com/transcribe/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [ffmpeg Documentation](https://ffmpeg.org/documentation.html)
- [AI Learning Assistant Requirements](../requirements.md)
- [AI Learning Assistant Design](../design.md)
