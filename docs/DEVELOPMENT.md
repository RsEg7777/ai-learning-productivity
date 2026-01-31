# Development Guide

This guide covers development setup, workflows, and best practices for the AI Learning Assistant project.

## Development Environment Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd ai-learning-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure AWS Credentials

```bash
# Configure AWS CLI
aws configure

# Set environment variables
export AWS_REGION=us-east-1
export ENVIRONMENT=dev
```

### 3. Configuration

```bash
# Copy example configuration
cp config/config.example.yaml config/config.yaml

# Edit config.yaml with your settings
```

## Project Structure

```
ai-learning-assistant/
├── src/                          # Source code
│   ├── services/                 # Microservices
│   │   ├── content_processing/   # Content processing
│   │   ├── quiz_generation/      # Quiz generation
│   │   ├── code_analysis/        # Code analysis
│   │   ├── voice_interface/      # Voice processing
│   │   ├── user_management/      # User management
│   │   └── multilingual/         # Translation
│   ├── shared/                   # Shared code
│   │   ├── aws_clients/          # AWS service clients
│   │   ├── models/               # Data models
│   │   └── utils/                # Utilities
│   └── api/                      # API handlers
├── infrastructure/               # CDK infrastructure
├── tests/                        # Test suites
├── config/                       # Configuration
└── docs/                         # Documentation
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_models.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run property-based tests only
pytest tests/property/ -m property

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking with mypy
mypy src/

# Linting with flake8
flake8 src/ tests/

# Run all quality checks
black src/ tests/ && isort src/ tests/ && mypy src/ && flake8 src/ tests/
```

### Local Development

```bash
# Run local API server (using SAM)
sam local start-api

# Invoke specific Lambda function
sam local invoke ContentProcessingFunction --event events/test-event.json

# Test with local DynamoDB
docker run -p 8000:8000 amazon/dynamodb-local
```

## Testing Strategy

### Unit Tests

Unit tests focus on individual components and functions:

```python
# tests/unit/test_example.py
def test_function():
    result = my_function(input_data)
    assert result == expected_output
```

### Property-Based Tests

Property-based tests validate universal properties using Hypothesis:

```python
# tests/property/test_example.py
from hypothesis import given, strategies as st

@given(st.text())
def test_property(text):
    result = process_text(text)
    assert len(result) <= len(text)  # Property: output never longer than input
```

### Integration Tests

Integration tests verify service interactions:

```python
# tests/integration/test_example.py
def test_end_to_end_workflow():
    # Upload content
    content_id = upload_content(file_data)
    
    # Process content
    result = process_content(content_id)
    
    # Verify result
    assert result.status == "completed"
```

## AWS Service Development

### Working with S3

```python
from src.shared.aws_clients import S3Client

s3_client = S3Client(bucket_name="my-bucket")
s3_uri = s3_client.upload_file(file_obj, "path/to/file.txt")
```

### Working with DynamoDB

```python
from src.shared.aws_clients import DynamoDBClient

db_client = DynamoDBClient(table_name="my-table")
db_client.put_item({"id": "123", "data": "value"})
item = db_client.get_item({"id": "123"})
```

### Working with Bedrock

```python
from src.shared.aws_clients import BedrockClient

bedrock = BedrockClient()
response = bedrock.invoke_claude(
    prompt="Explain machine learning",
    max_tokens=1024
)
```

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Use IPython for Interactive Debugging

```python
import ipdb; ipdb.set_trace()  # Set breakpoint
```

### CloudWatch Logs

```bash
# Tail Lambda logs
aws logs tail /aws/lambda/function-name --follow

# Query logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/function-name \
  --filter-pattern "ERROR"
```

## Common Tasks

### Adding a New Service

1. Create service directory: `src/services/new_service/`
2. Implement service logic
3. Add tests in `tests/unit/` and `tests/property/`
4. Update infrastructure in `infrastructure/lib/`
5. Document in `docs/`

### Adding a New Model

1. Define model in `src/shared/models/`
2. Add validation logic
3. Write unit tests
4. Update `__init__.py` exports

### Adding a New AWS Client

1. Create client in `src/shared/aws_clients/`
2. Implement methods with error handling
3. Add IAM permissions in CDK stack
4. Write unit tests with mocks

## Best Practices

### Code Style

- Follow PEP 8 style guide
- Use type hints for all functions
- Write docstrings for public APIs
- Keep functions small and focused

### Error Handling

- Use custom exception classes from `src.shared.utils.errors`
- Log errors with context
- Provide user-friendly error messages
- Never expose sensitive information in errors

### Testing

- Write tests before or alongside code
- Aim for >80% code coverage
- Use property-based tests for algorithms
- Mock external services in unit tests

### Security

- Never commit credentials or secrets
- Use environment variables for configuration
- Validate all user inputs
- Follow least-privilege principle for IAM

### Performance

- Use async/await for I/O operations
- Implement caching where appropriate
- Monitor Lambda cold starts
- Optimize DynamoDB queries

## Troubleshooting

### Import Errors

```bash
# Ensure package is installed in development mode
pip install -e .
```

### AWS Permission Errors

```bash
# Check IAM role permissions
aws iam get-role-policy --role-name role-name --policy-name policy-name
```

### Test Failures

```bash
# Run with verbose output
pytest -vv

# Run specific test
pytest tests/unit/test_file.py::test_function -v
```

## Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
