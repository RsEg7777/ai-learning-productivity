# Production Deployment Guide

## Pre-Deployment Checklist

- [x] All demo mode code removed
- [x] All features tested and working
- [x] AI integration verified
- [x] Error handling implemented
- [x] Documentation updated
- [x] Unnecessary markdown files deleted

## Quick Start

### 1. Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
aws configure
# Enter: Access Key, Secret Key, Region (us-east-1)
```

### 2. Start Server

```bash
# Development
python -m uvicorn app:app --reload --port 8000

# Production
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Verify Deployment

```bash
# Run production tests
python test_production_features.py

# Check health
curl http://localhost:8000/health
```

## Frontend Deployment

### 1. Configure API URL

```bash
cd frontend
echo "REACT_APP_API_URL=http://your-api-url.com" > .env.production
```

### 2. Build and Deploy

```bash
# Build
npm run build

# Deploy to Vercel
vercel --prod

# Or deploy to AWS Amplify, Netlify, etc.
```

## AWS Configuration

### Required Services

1. **Amazon Bedrock** (Nova Pro model)
   - Enable model access in AWS Console
   - Ensure IAM permissions for `bedrock:InvokeModel`

2. **DynamoDB**
   - Tables created automatically on first run
   - Ensure IAM permissions for DynamoDB operations

3. **S3** (Optional for file uploads)
   - Create bucket for content storage
   - Configure CORS if needed

### IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "dynamodb:*",
        "s3:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## Environment Variables

```bash
# Optional - defaults work for most cases
export AWS_REGION=us-east-1
export TABLE_PREFIX=ai-learning-
export STRICT_MODE=false
```

## Monitoring

### Health Check

```bash
# Check service health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "bedrock": "operational",
    "dynamodb": "operational"
  }
}
```

### Logs

```bash
# View application logs
tail -f app.log

# Check for errors
grep ERROR app.log
```

## Troubleshooting

### Issue: Bedrock Access Denied

**Solution:**
1. Verify payment method added in AWS Console
2. Check IAM permissions include `bedrock:InvokeModel`
3. Wait 2-5 minutes for permissions to propagate

### Issue: DynamoDB Table Errors

**Solution:**
1. Tables are created automatically on first run
2. Check IAM permissions for DynamoDB
3. Verify table prefix matches configuration

### Issue: Frontend Can't Connect

**Solution:**
1. Check CORS configuration in `app.py`
2. Verify API URL in frontend `.env` file
3. Ensure server is running and accessible

## Performance Optimization

### 1. Enable Caching

```python
# Add Redis caching for frequently accessed data
# See docs/PERFORMANCE.md for details
```

### 2. Scale with Load Balancer

```bash
# Deploy multiple instances behind ALB
# Configure auto-scaling based on CPU/memory
```

### 3. Use CloudFront CDN

```bash
# Cache static assets and API responses
# Reduce latency for global users
```

## Security Best Practices

1. **API Keys**: Use AWS Secrets Manager for sensitive data
2. **HTTPS**: Always use TLS in production
3. **Rate Limiting**: Implement API rate limiting
4. **Input Validation**: All inputs are validated
5. **Error Messages**: Don't expose internal details

## Cost Optimization

### Amazon Nova Pro Pricing

- **Free Tier**: First 2 months free
- **After Free Tier**: ~$0.0008 per 1K tokens
- **Estimated**: $1-5/month for development
- **Production**: $50-200/month depending on usage

### Tips to Reduce Costs

1. Cache AI responses for common queries
2. Use shorter prompts when possible
3. Implement request throttling
4. Monitor usage with CloudWatch

## Support

- **Issues**: Open a GitHub issue
- **Documentation**: Check `docs/` folder
- **Status**: See [PRODUCTION_FIXES.md](PRODUCTION_FIXES.md)

---

**Last Updated**: 2026-03-09
**Status**: Production Ready ✅
