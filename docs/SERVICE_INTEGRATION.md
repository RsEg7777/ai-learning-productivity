# Service Integration Documentation

## Overview

This document describes how all microservices in the AI Learning Assistant are wired together through API Gateway, service-to-service communication patterns, health checks, and monitoring.

## Architecture

The AI Learning Assistant follows a microservices architecture with the following components:

### Core Services

1. **Content Processing Service** - Handles text, PDF, and video content processing
2. **Quiz Generation Service** - Generates quizzes and flashcards
3. **Code Analysis Service** - Analyzes code and provides explanations
4. **Voice Interface Service** - Handles speech-to-text and text-to-speech
5. **Multilingual Service** - Provides language detection and translation
6. **User Management Service** - Handles authentication and user data

### Integration Layer

- **API Gateway** - Central entry point for all client requests
- **Service Orchestrator** - Coordinates service-to-service communication
- **Health Check System** - Monitors service health and readiness

## API Gateway Integration

All services are exposed through AWS API Gateway with the following endpoints:

### Content Processing Endpoints

- `POST /content/upload` - Upload content files
- `POST /content/process-text` - Process text content

### Quiz Endpoints

- `POST /quiz/generate` - Generate quiz from content
- `POST /quiz/submit` - Submit quiz answers
- `POST /flashcards/generate` - Generate flashcards

### Code Analysis Endpoints

- `POST /code/analyze` - Analyze code
- `POST /code/explain-algorithm` - Explain complex algorithms

### Voice Interface Endpoints

- `POST /voice/transcribe` - Transcribe audio to text
- `POST /voice/synthesize` - Synthesize speech from text

### Health Check Endpoints

- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health status
- `GET /health/ready` - Readiness check
- `GET /health/metrics` - Service metrics

## Service-to-Service Communication

Services communicate through the **ServiceOrchestrator** class, which provides:

### 1. Centralized Service Access

All services are initialized once and shared across workflows:

```python
from src.api.service_orchestrator import get_orchestrator

orchestrator = get_orchestrator()
```

### 2. Complex Workflows

The orchestrator enables multi-service workflows:

#### End-to-End Content Processing

```python
result = orchestrator.process_content_end_to_end(
    content="Learning material text",
    content_type="text",
    language="en",
    generate_quiz=True,
    generate_flashcards=True,
)
```

This workflow:
1. Processes the content (text/PDF/video)
2. Generates quiz questions
3. Generates flashcards
4. Returns comprehensive results

#### Voice-to-Learning Materials

```python
result = orchestrator.process_voice_to_learning_materials(
    audio_data=audio_bytes,
    language_code="en-US",
)
```

This workflow:
1. Transcribes audio to text
2. Processes transcribed text
3. Generates flashcards
4. Returns learning materials

#### Code Analysis with Audio Explanation

```python
result = orchestrator.analyze_code_with_explanation(
    code="def example(): pass",
    language="python",
    generate_audio=True,
    audio_language="en-US",
)
```

This workflow:
1. Analyzes code
2. Generates text explanation
3. Optionally synthesizes audio explanation
4. Returns analysis with audio

### 3. Service Status Monitoring

```python
status = orchestrator.get_service_status()
```

Returns health status of all services.

## Health Checks

The system implements three types of health checks:

### 1. Basic Health Check (`/health`)

- **Purpose**: Quick liveness check for load balancers
- **Response Time**: < 1 second
- **Returns**: Service status and version

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "ai-learning-assistant",
  "version": "1.0.0",
  "environment": "dev"
}
```

### 2. Detailed Health Check (`/health/detailed`)

- **Purpose**: Comprehensive health information
- **Response Time**: < 5 seconds
- **Returns**: Service status, AWS service connectivity, Lambda context

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "text_processor": {"status": "healthy", "initialized": true},
    "quiz_generator": {"status": "healthy", "initialized": true}
  },
  "aws_services": {
    "bedrock": {"status": "healthy"},
    "s3": {"status": "healthy"},
    "dynamodb": {"status": "healthy"}
  },
  "lambda_context": {
    "function_name": "ai-learning-assistant-health",
    "memory_limit": 512,
    "remaining_time": 28500
  }
}
```

### 3. Readiness Check (`/health/ready`)

- **Purpose**: Indicates if service is ready to accept traffic
- **Response Time**: < 2 seconds
- **Returns**: Readiness status and dependency checks

```json
{
  "ready": true,
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "orchestrator": {"ready": true, "message": "Orchestrator initialized"},
    "aws_clients": {"ready": true, "message": "AWS clients initialized"}
  }
}
```

## Monitoring and Observability

### CloudWatch Metrics

The system tracks the following custom metrics:

1. **ContentProcessingTime** - Time to process content
2. **QuizGenerationTime** - Time to generate quizzes
3. **CodeAnalysisTime** - Time to analyze code
4. **VoiceTranscriptionTime** - Time to transcribe audio
5. **ServiceErrors** - Count of service errors
6. **APIRequestCount** - Count of API requests
7. **ServiceCommunicationLatency** - Inter-service communication latency

### CloudWatch Alarms

Configured alarms:

1. **HighErrorRate** - Triggers when error rate exceeds threshold
2. **HighLatency** - Triggers when latency exceeds 30 seconds
3. **LambdaThrottling** - Triggers when Lambda functions are throttled
4. **APIGateway5xxErrors** - Triggers on API Gateway server errors

### CloudWatch Logs

All services log to CloudWatch with structured logging:

```python
logger.info(
    "Processing content",
    extra={
        "user_id": user_id,
        "content_type": content_type,
        "language": language,
    }
)
```

### X-Ray Tracing

AWS X-Ray is enabled for distributed tracing across services:

- Traces service-to-service communication
- Identifies performance bottlenecks
- Provides end-to-end request visualization

## Rate Limiting and Throttling

API Gateway implements rate limiting:

- **Rate Limit**: 1000 requests/second
- **Burst Limit**: 2000 requests
- **Quota**: 100,000 requests/day

## Error Handling

### Service Communication Errors

When service-to-service communication fails:

```python
from src.shared.utils.errors import ServiceCommunicationError

raise ServiceCommunicationError(
    message="Failed to communicate with quiz service",
    service="quiz_generation",
)
```

### Graceful Degradation

Services implement graceful degradation:

1. Retry with exponential backoff
2. Return partial results when possible
3. Provide fallback responses
4. Log detailed error information

## Security

### Authentication

- All endpoints (except health checks) require Cognito authentication
- JWT tokens validated by API Gateway
- User context passed to Lambda functions

### Authorization

- Role-based access control (RBAC)
- Resource-level permissions
- Audit logging for all operations

### Encryption

- Data in transit: TLS 1.2+
- Data at rest: AES-256
- S3 bucket encryption enabled
- DynamoDB encryption enabled

## Deployment

### Infrastructure as Code

All infrastructure is defined in AWS CDK:

```bash
cd infrastructure
npm install
cdk deploy --context environment=dev
```

### Lambda Functions

Lambda functions are deployed with:

- Python 3.11 runtime
- Shared layer for common dependencies
- Environment-specific configuration
- IAM roles with least-privilege permissions

### API Gateway

API Gateway is configured with:

- Request validation
- CORS support
- Rate limiting
- CloudWatch logging

## Testing

### Integration Tests

Run integration tests to verify service wiring:

```bash
pytest tests/integration/test_service_integration.py -v
```

Tests verify:

- Service orchestrator initialization
- End-to-end workflows
- Health check functionality
- Service status reporting

### Load Testing

Use tools like Apache JMeter or Locust to test:

- API Gateway throughput
- Lambda concurrency
- Service-to-service communication under load

## Troubleshooting

### Common Issues

1. **Service Initialization Failures**
   - Check CloudWatch logs for initialization errors
   - Verify IAM permissions
   - Ensure AWS clients are configured correctly

2. **High Latency**
   - Check CloudWatch metrics for bottlenecks
   - Review X-Ray traces
   - Verify Lambda memory allocation

3. **Service Communication Errors**
   - Check orchestrator logs
   - Verify service initialization
   - Review error details in CloudWatch

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

View logs in CloudWatch:

```bash
aws logs tail /aws/lambda/ai-learning-assistant-health --follow
```

## Performance Optimization

### Lambda Optimization

- Use appropriate memory allocation (512MB - 1024MB)
- Implement connection pooling for AWS clients
- Reuse Lambda containers (warm starts)
- Use Lambda layers for shared dependencies

### API Gateway Optimization

- Enable caching for frequently accessed endpoints
- Use request/response compression
- Implement efficient request validation

### Service Communication Optimization

- Minimize service-to-service calls
- Implement caching where appropriate
- Use asynchronous processing for long-running tasks

## Maintenance

### Regular Tasks

1. **Monitor Health Checks** - Review health check status daily
2. **Review Metrics** - Check CloudWatch metrics weekly
3. **Update Dependencies** - Keep Lambda dependencies up to date
4. **Review Logs** - Analyze CloudWatch logs for errors
5. **Test Failover** - Periodically test service failover

### Scaling

The system automatically scales based on:

- Lambda concurrent executions
- API Gateway request rate
- DynamoDB read/write capacity (on-demand)

## Future Enhancements

1. **Service Mesh** - Implement AWS App Mesh for advanced traffic management
2. **Circuit Breakers** - Add circuit breaker pattern for resilience
3. **Caching Layer** - Implement Redis/ElastiCache for response caching
4. **Event-Driven Architecture** - Use EventBridge for asynchronous workflows
5. **GraphQL API** - Add GraphQL endpoint for flexible queries

## References

- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/)
- [CloudWatch Monitoring](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/)
- [AWS X-Ray](https://docs.aws.amazon.com/xray/latest/devguide/)
