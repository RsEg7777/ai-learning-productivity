# Text-to-Speech Implementation

## Overview

This document describes the implementation of text-to-speech (TTS) functionality using Amazon Polly for the AI Learning Assistant. The implementation provides audio response generation in multiple languages with support for bilingual voices, particularly for Indian languages.

## Architecture

### Components

1. **TextToSpeechService** (`src/services/voice_interface/text_to_speech_service.py`)
   - Core service for text-to-speech synthesis
   - Handles voice selection and language mapping
   - Manages bilingual voice support
   - Integrates with Amazon Polly

2. **VoiceInterfaceService** (`src/services/voice_interface/voice_interface_service.py`)
   - Unified interface for speech-to-text and text-to-speech
   - Provides voice round-trip processing
   - Manages user voice preferences
   - Coordinates audio processing

3. **PollyClient** (`src/shared/aws_clients/polly_client.py`)
   - AWS Polly client wrapper
   - Handles API calls to Amazon Polly
   - Manages voice synthesis requests

## Features

### 1. Multi-Language Support

The service supports multiple languages including:

- **English variants**: en-US, en-GB, en-IN, en-AU
- **Indian languages**: Hindi (hi-IN), Tamil (ta-IN), Telugu (te-IN), Bengali (bn-IN), Marathi (mr-IN), Gujarati (gu-IN), Kannada (kn-IN), Malayalam (ml-IN), Punjabi (pa-IN)
- **Other languages**: Spanish, French, German, Italian, Portuguese, Japanese, Korean, Chinese

### 2. Bilingual Voice Support

Special support for bilingual voices that can speak multiple languages:

- **Aditi**: Supports both English (Indian) and Hindi
- **Kajal**: Supports both English (Indian) and Tamil

These voices are ideal for Indian users who may switch between English and their native language.

### 3. Automatic Voice Selection

The service automatically selects appropriate voices based on language:

```python
# Automatic voice selection
result = tts_service.synthesize_speech(
    text="Hello, world!",
    language_code="en-US",
    # voice_id is automatically selected as "Joanna"
)
```

Voice mapping:
- `en-US` → Joanna
- `hi-IN` → Aditi (bilingual)
- `ta-IN` → Kajal (bilingual)
- `en-GB` → Emma
- And more...

### 4. User Preference Management

Users can specify their preferred voice and language:

```python
user_preferences = {
    "language": "hi",
    "voice_id": "Aditi",
}

result = tts_service.synthesize_with_preferences(
    text="नमस्ते",
    user_preferences=user_preferences,
)
```

### 5. Voice Round-Trip Processing

Complete voice interaction flow:

```python
result = voice_service.process_voice_round_trip(
    audio_input=audio_data,
    input_language="en-US",
    output_language="hi-IN",
)
# Returns both transcription and synthesis results
```

## API Reference

### TextToSpeechService

#### `synthesize_speech(text, language_code, voice_id, audio_format, engine)`

Synthesize speech from text.

**Parameters:**
- `text` (str): Text to convert to speech
- `language_code` (str): Language code (e.g., 'en-US', 'hi-IN')
- `voice_id` (str, optional): Specific voice ID
- `audio_format` (str): Output format ('mp3', 'ogg_vorbis', 'pcm')
- `engine` (str): Speech engine ('neural', 'standard')

**Returns:**
- `SynthesisResult`: Contains audio data and metadata

**Example:**
```python
result = tts_service.synthesize_speech(
    text="Hello, world!",
    language_code="en-US",
    audio_format="mp3",
    engine="neural",
)
```

#### `synthesize_with_preferences(text, user_preferences, audio_format)`

Synthesize speech using user preferences.

**Parameters:**
- `text` (str): Text to convert to speech
- `user_preferences` (dict): User preferences including language and voice_id
- `audio_format` (str): Output format

**Returns:**
- `SynthesisResult`: Contains audio data and metadata

**Example:**
```python
preferences = {
    "language": "hi",
    "voice_id": "Aditi",
}
result = tts_service.synthesize_with_preferences(
    text="नमस्ते",
    user_preferences=preferences,
)
```

#### `get_available_voices(language_code, include_bilingual)`

Get available voices for a language.

**Parameters:**
- `language_code` (str, optional): Language code to filter by
- `include_bilingual` (bool): Include bilingual voices

**Returns:**
- `List[Dict]`: List of voice information dictionaries

#### `get_indian_language_voices()`

Get voices for Indian languages.

**Returns:**
- `Dict[str, List[Dict]]`: Dictionary mapping language codes to voice information

#### `get_bilingual_voices()`

Get bilingual voices and their supported languages.

**Returns:**
- `Dict[str, List[str]]`: Dictionary mapping voice IDs to supported language codes

#### `validate_voice_for_language(voice_id, language_code)`

Validate if a voice supports a language.

**Parameters:**
- `voice_id` (str): Voice ID
- `language_code` (str): Language code

**Returns:**
- `bool`: True if voice supports the language

### VoiceInterfaceService

#### `generate_audio_response(text, language_code, voice_id, audio_format)`

Generate audio response from text.

**Parameters:**
- `text` (str): Text to convert to speech
- `language_code` (str): Language code
- `voice_id` (str, optional): Specific voice ID
- `audio_format` (str): Output format

**Returns:**
- `SynthesisResult`: Contains audio data and metadata

#### `generate_audio_with_preferences(text, user_preferences, audio_format)`

Generate audio response using user preferences.

**Parameters:**
- `text` (str): Text to convert to speech
- `user_preferences` (dict): User preferences
- `audio_format` (str): Output format

**Returns:**
- `SynthesisResult`: Contains audio data and metadata

#### `process_voice_round_trip(audio_input, input_language, output_language, voice_id, audio_format)`

Process complete voice round-trip: speech-to-text and text-to-speech.

**Parameters:**
- `audio_input` (bytes): Input audio data
- `input_language` (str): Input audio language code
- `output_language` (str, optional): Output audio language code
- `voice_id` (str, optional): Specific voice ID for output
- `audio_format` (str): Audio format

**Returns:**
- `Dict`: Contains transcription and synthesis results

## Data Models

### SynthesisResult

```python
@dataclass
class SynthesisResult:
    audio_data: bytes          # Generated audio data
    voice_id: str              # Voice used for synthesis
    language_code: str         # Language code
    text_length: int           # Length of input text
    audio_format: str          # Audio format (mp3, ogg_vorbis, pcm)
    engine: str                # Speech engine (neural, standard)
    metadata: Dict[str, Any]   # Additional metadata
```

Metadata includes:
- `is_bilingual`: Whether the voice is bilingual
- `is_indian_language`: Whether the language is an Indian language
- `audio_size_bytes`: Size of audio data in bytes

## Usage Examples

### Basic Synthesis

```python
from src.services.voice_interface import TextToSpeechService

tts_service = TextToSpeechService()

result = tts_service.synthesize_speech(
    text="Hello, welcome to the AI Learning Assistant!",
    language_code="en-US",
)

# Save audio to file
with open("output.mp3", "wb") as f:
    f.write(result.audio_data)
```

### Indian Language Synthesis

```python
# Hindi synthesis with bilingual voice
result = tts_service.synthesize_speech(
    text="नमस्ते! आपका स्वागत है।",
    language_code="hi-IN",
)

print(f"Voice: {result.voice_id}")  # Aditi
print(f"Is bilingual: {result.metadata['is_bilingual']}")  # True
```

### Using Bilingual Voices

```python
# Get bilingual voices
bilingual = tts_service.get_bilingual_voices()
print(bilingual)
# {'Aditi': ['en-IN', 'hi-IN'], 'Kajal': ['en-IN', 'ta-IN']}

# Use Aditi for English
english_result = tts_service.synthesize_speech(
    text="Hello from India",
    language_code="en-IN",
    voice_id="Aditi",
)

# Use Aditi for Hindi
hindi_result = tts_service.synthesize_speech(
    text="भारत से नमस्कार",
    language_code="hi-IN",
    voice_id="Aditi",
)
```

### Voice Preference Management

```python
# User preferences
user_prefs = {
    "language": "hi",
    "voice_id": "Aditi",
    "voice_enabled": True,
}

# Synthesize with preferences
result = tts_service.synthesize_with_preferences(
    text="यह एक परीक्षण है।",
    user_preferences=user_prefs,
)
```

### Complete Voice Interface

```python
from src.services.voice_interface import VoiceInterfaceService

voice_service = VoiceInterfaceService()

# Generate audio response
result = voice_service.generate_audio_response(
    text="I understand your question. Let me help you.",
    language_code="en-US",
)

# Voice round-trip (speech-to-text + text-to-speech)
result = voice_service.process_voice_round_trip(
    audio_input=audio_data,
    input_language="en-US",
    output_language="hi-IN",
)

print(result["transcription"]["text"])
print(result["synthesis"]["voice_id"])
```

## Requirements Validation

This implementation satisfies **Requirement 5.3**:

> "WHEN the system responds to voice input, THE Voice_Interface SHALL provide audio responses in the user's preferred language"

### How Requirements Are Met:

1. ✅ **Audio response generation**: `generate_audio_response()` method
2. ✅ **Multiple languages**: Support for 20+ languages including Indian languages
3. ✅ **Bilingual voices**: Aditi and Kajal support multiple languages
4. ✅ **Voice preference management**: `synthesize_with_preferences()` and `validate_voice_for_language()`
5. ✅ **User's preferred language**: Respects user preferences from UserPreferences model

## Testing

### Unit Tests

Located in `tests/unit/test_text_to_speech_service.py`:

- Basic synthesis
- Language-specific synthesis
- Bilingual voice support
- User preference handling
- Voice selection logic
- Error handling
- Voice validation

### Integration Tests

Located in `tests/unit/test_voice_interface_service.py`:

- Audio response generation
- Voice round-trip processing
- Preference-based synthesis
- Multi-language support

Run tests:
```bash
pytest tests/unit/test_text_to_speech_service.py -v
pytest tests/unit/test_voice_interface_service.py -v
```

## Error Handling

The service implements comprehensive error handling:

1. **Empty text validation**: Raises `VoiceProcessingError` for empty input
2. **Synthesis failures**: Catches and wraps Polly client errors
3. **Invalid preferences**: Handles missing or invalid user preferences
4. **Voice validation**: Validates voice-language combinations

Example:
```python
try:
    result = tts_service.synthesize_speech(text="")
except VoiceProcessingError as e:
    print(f"Error: {e}")
    # Error: Text cannot be empty
```

## Performance Considerations

1. **Neural vs Standard Engine**:
   - Neural engine: Higher quality, slightly slower
   - Standard engine: Faster, lower quality
   - Default: Neural engine for best quality

2. **Audio Format**:
   - MP3: Good compression, widely supported (default)
   - OGG Vorbis: Better compression, less compatible
   - PCM: Uncompressed, largest size

3. **Caching**: Consider caching frequently used audio responses

## AWS Configuration

### Required AWS Services

- Amazon Polly

### IAM Permissions

Required IAM permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "polly:SynthesizeSpeech",
        "polly:DescribeVoices"
      ],
      "Resource": "*"
    }
  ]
}
```

### AWS Credentials

Configure AWS credentials:
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

Or use AWS CLI:
```bash
aws configure
```

## Future Enhancements

1. **SSML Support**: Add Speech Synthesis Markup Language for advanced control
2. **Audio Caching**: Cache frequently synthesized audio
3. **Streaming**: Support streaming audio synthesis for long texts
4. **Custom Lexicons**: Add pronunciation customization
5. **Voice Cloning**: Integrate custom voice models
6. **Real-time Synthesis**: Optimize for real-time voice interactions

## References

- [Amazon Polly Documentation](https://docs.aws.amazon.com/polly/)
- [Polly Voice List](https://docs.aws.amazon.com/polly/latest/dg/voicelist.html)
- [Neural TTS](https://docs.aws.amazon.com/polly/latest/dg/NTTS-main.html)
- [SSML Support](https://docs.aws.amazon.com/polly/latest/dg/supportedtags.html)
