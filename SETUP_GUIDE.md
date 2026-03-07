# AI Learning Assistant - Setup Guide

## Quick Start

### Prerequisites
- Python 3.9 or higher
- AWS Account with Bedrock access
- AWS credentials configured

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

Option A: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

Option B: AWS CLI Configuration
```bash
aws configure
```

### 3. Start the Backend Server

```bash
# Windows:
.\start-server.ps1

# Linux/Mac:
python -m uvicorn app:app --reload --port 8000
```

The server will:
- Validate AWS credentials
- Create DynamoDB tables if they don't exist
- Initialize Bedrock client
- Start on http://localhost:8000

### 4. Start the Frontend

```bash
cd frontend
npm install
npm start
```

Update `frontend/.env.local`:
```
REACT_APP_API_URL=http://localhost:8000
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| AWS_REGION | us-east-1 | AWS region for services |
| TABLE_PREFIX | ai-learning- | Prefix for DynamoDB tables |
| STRICT_MODE | false | Fail on initialization errors |

### DynamoDB Tables

The following tables will be created automatically:
- `ai-learning-tutor-sessions` - Tutoring session data
- `ai-learning-quiz-results` - Quiz results and scores
- `ai-learning-user-progress` - User learning progress
- `ai-learning-flashcards` - Flashcard data
- `ai-learning-achievements` - User achievements

## API Endpoints

### Health Check
```
GET /health
```

Returns service status and availability.

### AI Tutor
```
POST /tutor/start-session
POST /tutor/ask-question
```

### Quiz Generation
```
POST /quiz/generate
```

### Code Analysis
```
POST /code/analyze
```

## Troubleshooting

### "AWS credentials not configured"
- Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
- Or run `aws configure`

### "Bedrock access denied"
- Ensure your IAM user/role has `bedrock:InvokeModel` permission
- Check that Bedrock is available in your region

### "Table creation failed"
- Ensure IAM permissions for DynamoDB (CreateTable, DescribeTable)
- Check AWS service quotas

### "Empty response from Bedrock"
- Check Bedrock model availability in your region
- Verify model ID is correct
- Check CloudWatch logs for detailed errors

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
# Format code
black src/

# Type checking
mypy src/

# Linting
flake8 src/
```

## Production Deployment

### AWS Lambda
See `docs/DEPLOYMENT.md` for Lambda deployment instructions.

### Docker
```bash
docker build -t ai-learning-assistant .
docker run -p 8000:8000 \
  -e AWS_ACCESS_KEY_ID=xxx \
  -e AWS_SECRET_ACCESS_KEY=xxx \
  ai-learning-assistant
```

## Support

For issues and questions:
1. Check `/health` endpoint for service status
2. Review CloudWatch logs
3. Check AWS service quotas and limits
4. Verify IAM permissions

## Features Status

✅ **Working**
- AI Tutor with Bedrock integration
- Quiz generation (multiple choice, true/false, fill-in-blank)
- Code analysis with suggestions
- Configuration validation
- Automatic table creation
- Proper error handling

⚠️ **Partial**
- User progress tracking (basic implementation)
- Achievements system (needs real queries)

🚧 **Not Implemented**
- Audio processing (placeholder)
- Real-time collaboration (WebSocket)
- MFA (stub implementation)

## Next Steps

1. Test all endpoints with real data
2. Add comprehensive error handling
3. Implement missing features
4. Add integration tests
5. Set up CI/CD pipeline
6. Configure monitoring and alerts
