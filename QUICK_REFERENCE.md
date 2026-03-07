# Quick Reference Card

## 🚀 Start Server

### Windows
```powershell
.\start-server.ps1
```

### Linux/Mac
```bash
python -m uvicorn app:app --reload --port 8000
```

## ✅ Check Status

```bash
# Quick health check
python check_health.py

# Full API test
python test_api.py

# Manual check
curl http://localhost:8000/health
```

## 📚 API Endpoints

### Base URL
```
http://localhost:8000
```

### Health & Docs
```
GET  /              # Root
GET  /health        # Health check
GET  /docs          # API documentation
```

### AI Tutor
```
POST /tutor/start-session
{
  "user_id": "test",
  "subject": "Python",
  "teaching_style": "socratic"
}

POST /tutor/ask-question
{
  "session_id": "...",
  "question": "What is a decorator?"
}
```

### Quiz
```
POST /quiz/generate
{
  "topic": "Python basics",
  "num_questions": 5,
  "difficulty": "medium"
}
```

### Code Analysis
```
POST /code/analyze
{
  "code": "def hello():\n    print('Hello')",
  "language": "python"
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Optional
export AWS_REGION=us-east-1
export TABLE_PREFIX=ai-learning-
export STRICT_MODE=false
```

### AWS Credentials
```bash
# Option 1: Environment variables (above)

# Option 2: AWS CLI
aws configure

# Option 3: Credentials file
# ~/.aws/credentials
[default]
aws_access_key_id = your_key
aws_secret_access_key = your_secret
```

## 🐛 Troubleshooting

### Server won't start
```bash
# Check Python version (need 3.9+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check port 8000 is free
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac
```

### AWS errors
```bash
# Check credentials
aws sts get-caller-identity

# Check Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Check DynamoDB access
aws dynamodb list-tables --region us-east-1
```

### Empty Bedrock responses
- Verify region supports Bedrock
- Check model ID is correct
- Review CloudWatch logs
- Verify IAM permissions

## 📁 Key Files

### Must Know
- `app.py` - Main API server
- `start-server.ps1` - Startup script
- `test_api.py` - API tests
- `check_health.py` - Health check

### Configuration
- `src/api/app_init.py` - Initialization
- `src/shared/config/config_validator.py` - Validation
- `src/shared/config/table_setup.py` - Table setup

### Services
- `src/services/ai_tutor/conversational_tutor.py` - Tutor
- `src/services/quiz_generation/quiz_generator.py` - Quiz
- `src/services/code_analysis/code_analyzer.py` - Code

### Documentation
- `README_FIXED.md` - Main README
- `SETUP_GUIDE.md` - Setup guide
- `TRANSFORMATION_SUMMARY.md` - What changed

## 🎯 Common Tasks

### Test a feature
```bash
# Start server
.\start-server.ps1

# In another terminal
python test_api.py
```

### Check logs
```bash
# Application logs (if configured)
tail -f logs/app.log

# AWS CloudWatch
aws logs tail /aws/lambda/ai-learning-api --follow
```

### Update dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Reset database
```bash
# Delete tables (careful!)
aws dynamodb delete-table --table-name ai-learning-tutor-sessions
aws dynamodb delete-table --table-name ai-learning-quiz-results
# etc.

# Restart server (will recreate tables)
.\start-server.ps1
```

## 💡 Tips

### Development
- Use `/docs` for interactive API testing
- Check `/health` for service status
- Run `test_api.py` after changes
- Use `check_health.py` for quick checks

### Production
- Set `STRICT_MODE=true`
- Use AWS Secrets Manager
- Enable CloudWatch logging
- Set up budget alerts
- Restrict CORS origins

### Performance
- Use caching for sessions
- Enable response compression
- Use async/await
- Monitor Bedrock costs
- Use DynamoDB on-demand billing

## 🆘 Getting Help

1. Check `/health` endpoint
2. Review error messages
3. Check CloudWatch logs
4. Verify IAM permissions
5. Read `SETUP_GUIDE.md`
6. Check `TRANSFORMATION_SUMMARY.md`

## 📊 Status Indicators

### Health Status
- 🟢 `healthy` - All systems operational
- 🟡 `degraded` - Some warnings present
- 🔴 `unhealthy` - Errors present
- ⚪ `unknown` - Not initialized

### Service Status
- ✓ Available
- ✗ Unavailable

## 🔗 URLs

### Local Development
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Frontend: http://localhost:3000

### AWS Console
- Bedrock: https://console.aws.amazon.com/bedrock
- DynamoDB: https://console.aws.amazon.com/dynamodb
- CloudWatch: https://console.aws.amazon.com/cloudwatch
- IAM: https://console.aws.amazon.com/iam

## 📝 Quick Commands

```bash
# Setup
pip install -r requirements.txt
aws configure

# Start
.\start-server.ps1

# Test
python check_health.py
python test_api.py
curl http://localhost:8000/health

# Frontend
cd frontend
npm install
npm start

# Deploy
# See SETUP_GUIDE.md for deployment instructions
```

---

**Keep this file handy for quick reference!** 📌
