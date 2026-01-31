# API Gateway Implementation

## Overview

This document describes the REST API endpoints implemented with AWS API Gateway for the AI Learning Assistant. The API provides comprehensive access to all system features including content processing, quiz generation, code analysis, and voice interfaces.

## Architecture

The API follows RESTful principles and is built using:
- **AWS API Gateway**: REST API with Lambda proxy integration
- **AWS Lambda**: Serverless compute for API handlers
- **Amazon Cognito**: User authentication and authorization
- **Rate Limiting**: Request throttling and usage plans
- **Request Validation**: Input validation at the API Gateway level
- **CORS Support**: Cross-origin resource sharing for web clients

## Authentication

All API endpoints require authentication using Amazon Cognito User Pools. Clients must include a valid JWT token in the `Authorization` header:

```
Authorization: Bearer <jwt-token>
```

## Rate Limiting

The API implements rate limiting to ensure fair usage and system stability:

- **Rate Limit**: 1,000 requests per second per API key
- **Burst Limit**: 2,000 requests (burst capacity)
- **Daily Quota**: 100,000 requests per day per API key

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests per second
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## CORS Configuration

The API supports Cross-Origin Resource Sharing (CORS) with the following configuration:

- **Allowed Origins**: All origins (`*`) - configure for production
- **Allowed Methods**: GET, POST, PUT, DELETE, OPTIONS
- **Allowed Headers**: Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token
- **Allow Credentials**: true

## Request Validation

API Gateway performs request validation before invoking Lambda functions:

- **Body Validation**: Validates request body against JSON schema
- **Parameter Validation**: Validates query parameters and path parameters
- **Header Validation**: Validates required headers

Invalid requests receive a `400 Bad Request` response without invoking Lambda.

## API Endpoints

### Content Processing

#### Upload Content

Upload various content types (text, PDF, video, audio) for processing.

**Endpoint**: `POST /content/upload`

**Request**:
```json
{
  "filename": "document.pdf",
  "title": "My Document",
  "language": "en",
  "file_content": "base64-encoded-content"
}
```

**Response** (201 Created):
```json
{
  "content_id": "uuid",
  "title": "My Document",
  "type": "pdf",
  "language": "en",
  "uploaded_at": "2024-01-01T00:00:00Z",
  "s3_location": "s3://bucket/path",
  "presigned_url": "https://...",
  "metadata": {
    "file_size": 1024,
    "mime_type": "application/pdf"
  },
  "message": "Content uploaded successfully"
}
```

#### Process Text

Process text content and generate summaries.

**Endpoint**: `POST /content/process-text`

**Request**:
```json
{
  "content": "Text to process...",
  "language": "en",
  "summary_type": "brief"
}
```

**Response** (200 OK):
```json
{
  "content_id": "uuid",
  "summary": "Brief summary...",
  "key_points": ["Point 1", "Point 2"],
  "concepts": [
    {
      "name": "Concept Name",
      "description": "Description"
    }
  ],
  "language": "en",
  "processing_time": 2.5
}
```

### Quiz Generation

#### Generate Quiz

Generate a quiz from content.

**Endpoint**: `POST /quiz/generate`

**Request**:
```json
{
  "content": "Content to generate quiz from...",
  "quiz_type": "mixed",
  "question_count": 10
}
```

**Response** (200 OK):
```json
{
  "quiz_id": "uuid",
  "title": "Quiz Title",
  "questions": [
    {
      "id": "uuid",
      "type": "multiple_choice",
      "text": "Question text?",
      "options": ["A", "B", "C", "D"],
      "points": 10
    }
  ],
  "time_limit": 600,
  "passing_score": 70
}
```

#### Submit Quiz

Submit quiz answers for scoring.

**Endpoint**: `POST /quiz/submit`

**Request**:
```json
{
  "quiz_id": "uuid",
  "answers": {
    "question_id_1": "answer_1",
    "question_id_2": "answer_2"
  }
}
```

**Response** (200 OK):
```json
{
  "quiz_id": "uuid",
  "user_id": "uuid",
  "score": 85,
  "total_questions": 10,
  "correct_answers": 8,
  "passed": true,
  "feedback": "Great job! You passed the quiz."
}
```

### Flashcards

#### Generate Flashcards

Generate flashcards from content.

**Endpoint**: `POST /flashcards/generate`

**Request**:
```json
{
  "content": "Content to generate flashcards from...",
  "count": 10
}
```

**Response** (200 OK):
```json
{
  "flashcards": [
    {
      "id": "uuid",
      "question": "Question?",
      "answer": "Answer",
      "difficulty": "medium",
      "tags": ["tag1", "tag2"]
    }
  ],
  "count": 10
}
```

### Code Analysis

#### Analyze Code

Analyze code and provide explanations and improvements.

**Endpoint**: `POST /code/analyze`

**Request**:
```json
{
  "code": "def hello():\n    print('Hello')",
  "language": "python"
}
```

**Response** (200 OK):
```json
{
  "explanation": "Overall explanation...",
  "line_by_line_analysis": [
    {
      "line_number": 1,
      "code": "def hello():",
      "explanation": "Defines a function..."
    }
  ],
  "improvements": [
    {
      "type": "documentation",
      "description": "Add docstring",
      "suggested_code": "def hello():\n    \"\"\"Print hello.\"\"\"",
      "priority": "medium"
    }
  ],
  "issues": [
    {
      "severity": "warning",
      "type": "style",
      "description": "Missing docstring",
      "line_number": 1,
      "suggestion": "Add a docstring"
    }
  ],
  "complexity": {
    "cyclomatic_complexity": 1,
    "cognitive_complexity": 1,
    "lines_of_code": 2
  }
}
```

#### Explain Algorithm

Explain complex algorithms step-by-step.

**Endpoint**: `POST /code/explain-algorithm`

**Request**:
```json
{
  "code": "def quicksort(arr):\n    ...",
  "language": "python"
}
```

**Response** (200 OK):
```json
{
  "overview": "This is a quicksort implementation...",
  "steps": [
    {
      "step_number": 1,
      "description": "Choose pivot element",
      "code_snippet": "pivot = arr[0]"
    }
  ],
  "complexity_analysis": "Time: O(n log n), Space: O(log n)",
  "optimization_suggestions": ["Use random pivot", "Implement tail recursion"]
}
```

### Voice Interface

#### Transcribe Audio

Convert speech to text.

**Endpoint**: `POST /voice/transcribe`

**Request**:
```json
{
  "audio_data": "base64-encoded-audio",
  "language": "en-US"
}
```

**Response** (200 OK):
```json
{
  "text": "Transcribed text...",
  "confidence": 0.95,
  "language": "en-US",
  "timestamps": [
    {
      "start": 0.0,
      "end": 1.5,
      "text": "Hello"
    }
  ]
}
```

#### Synthesize Speech

Convert text to speech.

**Endpoint**: `POST /voice/synthesize`

**Request**:
```json
{
  "text": "Text to synthesize",
  "language": "en-US",
  "voice_id": "Joanna"
}
```

**Response** (200 OK):
```json
{
  "audio_data": "base64-encoded-audio",
  "format": "mp3",
  "language": "en-US",
  "voice_id": "Joanna"
}
```

## Error Responses

All error responses follow a consistent format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional context"
  }
}
```

### Common Error Codes

- `MISSING_PARAMETER`: Required parameter is missing
- `VALIDATION_ERROR`: Input validation failed
- `UNSUPPORTED_FORMAT`: File format not supported
- `CONTENT_PROCESSING_ERROR`: Error processing content
- `INTERNAL_ERROR`: Unexpected server error
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `RATE_LIMIT_EXCEEDED`: Too many requests

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

## Request Throttling

When rate limits are exceeded, the API returns a `429 Too Many Requests` response:

```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Please try again later.",
  "details": {
    "retry_after": 60
  }
}
```

The `Retry-After` header indicates when to retry the request.

## Usage Plans

Different usage plans are available for different user tiers:

### Free Tier
- 1,000 requests per day
- 10 requests per second
- 20 burst capacity

### Standard Tier
- 10,000 requests per day
- 100 requests per second
- 200 burst capacity

### Premium Tier
- 100,000 requests per day
- 1,000 requests per second
- 2,000 burst capacity

## Monitoring and Logging

All API requests are logged to CloudWatch with the following information:

- Request ID
- User ID
- Endpoint
- HTTP method
- Status code
- Response time
- Error details (if applicable)

CloudWatch metrics track:
- Request count
- Error rate
- Latency (p50, p95, p99)
- Throttled requests

## Security

### HTTPS Only
All API endpoints require HTTPS. HTTP requests are automatically redirected.

### Request Signing
Requests can optionally be signed using AWS Signature Version 4 for additional security.

### Input Sanitization
All inputs are sanitized to prevent injection attacks.

### Content Security
- Maximum request body size: 10 MB
- Maximum file upload size: 100 MB
- Supported content types: JSON, multipart/form-data

## Best Practices

### Client Implementation

1. **Handle Rate Limits**: Implement exponential backoff when receiving 429 responses
2. **Use Connection Pooling**: Reuse HTTP connections for better performance
3. **Implement Timeouts**: Set appropriate timeouts for requests
4. **Cache Responses**: Cache responses when appropriate to reduce API calls
5. **Handle Errors Gracefully**: Implement proper error handling for all error codes

### Example Client Code (Python)

```python
import requests
import time

class AILearningAssistantClient:
    def __init__(self, api_url, auth_token):
        self.api_url = api_url
        self.headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
    
    def process_text(self, content, language='en', max_retries=3):
        url = f'{self.api_url}/content/process-text'
        data = {
            'content': content,
            'language': language
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    json=data,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 429:
                    # Rate limited, wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception('Max retries exceeded')
```

## Deployment

The API is deployed using AWS CDK:

```bash
cd infrastructure
npm install
npm run build
cdk deploy --all
```

This creates:
- API Gateway REST API
- Lambda functions for all endpoints
- Cognito User Pool for authentication
- DynamoDB tables for data storage
- S3 bucket for content storage
- CloudWatch log groups for monitoring

## Testing

Test the API using curl:

```bash
# Get authentication token
TOKEN=$(aws cognito-idp initiate-auth ...)

# Process text
curl -X POST https://api.example.com/content/process-text \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Text to process",
    "language": "en"
  }'
```

## Requirement Validation

This implementation satisfies **Requirement 6.4**:

> WHEN handling API requests, THE System SHALL implement rate limiting and load balancing through AWS API Gateway

**Validation**:
- ✅ API Gateway configured with rate limiting (1,000 req/s, 2,000 burst)
- ✅ Usage plans with daily quotas (100,000 requests/day)
- ✅ Request throttling at API Gateway level
- ✅ Load balancing through Lambda auto-scaling
- ✅ CORS support for web clients
- ✅ Request validation at API Gateway level
- ✅ Cognito authentication and authorization
- ✅ Comprehensive error handling
- ✅ CloudWatch monitoring and logging
