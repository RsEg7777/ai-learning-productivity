# AI Learning Assistant

A comprehensive cloud-native learning platform built on AWS that provides intelligent content processing, interactive learning tools, and multilingual support for students and developers.

## Features

- **Content Processing**: Upload and process text, PDFs, videos, and audio files with AI-powered summarization
- **Interactive Learning**: Generate flashcards and quizzes with spaced repetition algorithms
- **Code Analysis**: Get detailed code explanations and improvement suggestions
- **Multilingual Support**: Support for Indian languages (Hindi, Tamil, Telugu, Bengali, and more)
- **Voice Interface**: Speech-to-text and text-to-speech capabilities
- **Secure & Scalable**: Built on AWS with enterprise-grade security

## Architecture

The system follows a serverless, event-driven architecture using:
- **AWS Lambda**: Serverless compute for microservices
- **Amazon Bedrock**: Generative AI for content processing and code analysis
- **Amazon Transcribe**: Speech-to-text conversion
- **Amazon Polly**: Text-to-speech synthesis
- **Amazon Translate**: Multilingual translation
- **Amazon Comprehend**: Natural language processing
- **DynamoDB**: NoSQL database for user data and learning progress
- **S3**: Secure content storage
- **API Gateway**: RESTful API management
- **Cognito**: User authentication and authorization

## Project Structure

```
ai-learning-assistant/
├── src/                          # Source code
│   ├── services/                 # Microservices
│   │   ├── content_processing/   # Content processing service
│   │   ├── quiz_generation/      # Quiz and flashcard generation
│   │   ├── code_analysis/        # Code analysis service
│   │   ├── voice_interface/      # Voice processing service
│   │   ├── user_management/      # User management and auth
│   │   └── multilingual/         # Translation and language support
│   ├── shared/                   # Shared utilities
│   │   ├── aws_clients/          # AWS service clients
│   │   ├── models/               # Data models
│   │   └── utils/                # Common utilities
│   └── api/                      # API Gateway handlers
├── infrastructure/               # AWS CDK infrastructure code
├── tests/                        # Test suites
│   ├── unit/                     # Unit tests
│   ├── property/                 # Property-based tests
│   └── integration/              # Integration tests
├── config/                       # Configuration files
└── docs/                         # Documentation
```

## Prerequisites

- Python 3.11 or higher
- Node.js 18+ (for AWS CDK)
- AWS CLI configured with appropriate credentials
- AWS CDK CLI installed (`npm install -g aws-cdk`)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-learning-assistant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Install CDK dependencies:
```bash
cd infrastructure
npm install
cd ..
```

## Configuration

1. Copy the example configuration:
```bash
cp config/config.example.yaml config/config.yaml
```

2. Update `config/config.yaml` with your AWS settings and preferences

3. Set environment variables:
```bash
export AWS_REGION=us-east-1
export ENVIRONMENT=dev
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run property-based tests
pytest tests/property/

# Run with coverage
pytest --cov=src --cov-report=html
```

### Deploying Infrastructure

```bash
# Bootstrap CDK (first time only)
cd infrastructure
cdk bootstrap

# Deploy all stacks
cdk deploy --all

# Deploy specific stack
cdk deploy AILearningAssistantStack
```

### Local Development

```bash
# Run local API server (using SAM)
sam local start-api

# Invoke specific Lambda function
sam local invoke ContentProcessingFunction --event events/test-event.json
```

## Testing Strategy

The project uses a dual testing approach:

1. **Unit Tests**: Test specific examples, edge cases, and integration points
2. **Property-Based Tests**: Validate universal properties across all inputs using Hypothesis (minimum 100 iterations)

Each property test references its corresponding design document property and validates specific requirements.

## Security

- All data encrypted in transit (TLS) and at rest (AES-256)
- Multi-factor authentication via AWS Cognito
- Role-based access controls (RBAC)
- Comprehensive audit logging
- Data privacy controls and consent management

## License

[Your License Here]

## Contributing

[Contributing guidelines]

## Support

For issues and questions, please open a GitHub issue or contact [support email].
