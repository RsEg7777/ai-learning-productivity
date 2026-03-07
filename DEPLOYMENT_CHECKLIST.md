# Production Deployment Checklist

Use this checklist to deploy your 100% functional AI Learning Assistant to production.

## Pre-Deployment

### ✅ Code Quality
- [ ] All tests passing (`python test_all_features.py`)
- [ ] Health check working (`python check_health.py`)
- [ ] No TODO or FIXME comments in production code
- [ ] Code reviewed and approved
- [ ] Dependencies up to date

### ✅ Configuration
- [ ] AWS credentials configured
- [ ] Environment variables set
- [ ] Region configured correctly
- [ ] Table names configured
- [ ] S3 bucket created (if needed)

### ✅ AWS Services
- [ ] Bedrock access enabled in region
- [ ] DynamoDB tables created
- [ ] S3 bucket created and configured
- [ ] SNS configured for SMS (if using MFA)
- [ ] CloudWatch logging enabled
- [ ] IAM roles and policies configured

### ✅ Security
- [ ] Secrets stored in AWS Secrets Manager
- [ ] CORS origins restricted
- [ ] Rate limiting configured
- [ ] HTTPS/TLS enabled
- [ ] Security headers configured
- [ ] Input validation enabled
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified

### ✅ Monitoring
- [ ] CloudWatch alarms configured
- [ ] Error tracking set up
- [ ] Performance monitoring enabled
- [ ] Cost alerts configured
- [ ] Uptime monitoring configured

## Deployment Steps

### Step 1: Prepare Environment

```bash
# Set production environment variables
export ENVIRONMENT=production
export AWS_REGION=us-east-1
export TABLE_PREFIX=prod-ai-learning-
export STRICT_MODE=true

# Verify configuration
python check_health.py
```

### Step 2: Run Tests

```bash
# Run all tests
python test_all_features.py

# Verify 100% pass rate
# If any tests fail, DO NOT deploy
```

### Step 3: Deploy Application

#### Option A: AWS Lambda

```bash
# Package application
pip install -t package -r requirements.txt
cd package && zip -r ../deployment.zip . && cd ..
zip -g deployment.zip app.py src/

# Create Lambda function
aws lambda create-function \
  --function-name ai-learning-api \
  --runtime python3.9 \
  --handler app.handler \
  --zip-file fileb://deployment.zip \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
  --timeout 300 \
  --memory-size 1024 \
  --environment Variables="{
    AWS_REGION=us-east-1,
    TABLE_PREFIX=prod-ai-learning-,
    STRICT_MODE=true
  }"

# Create API Gateway
aws apigatewayv2 create-api \
  --name ai-learning-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:REGION:ACCOUNT_ID:function:ai-learning-api
```

#### Option B: Docker + ECS

```bash
# Build Docker image
docker build -t ai-learning-assistant:latest .

# Tag for ECR
docker tag ai-learning-assistant:latest \
  ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/ai-learning-assistant:latest

# Push to ECR
aws ecr get-login-password --region REGION | \
  docker login --username AWS --password-stdin \
  ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com

docker push ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/ai-learning-assistant:latest

# Deploy to ECS
aws ecs create-service \
  --cluster production \
  --service-name ai-learning-api \
  --task-definition ai-learning-assistant \
  --desired-count 2 \
  --launch-type FARGATE
```

#### Option C: EC2

```bash
# SSH to EC2 instance
ssh -i key.pem ec2-user@instance-ip

# Clone repository
git clone https://github.com/your-repo/ai-learning-assistant.git
cd ai-learning-assistant

# Install dependencies
pip install -r requirements.txt

# Configure systemd service
sudo cp ai-learning-assistant.service /etc/systemd/system/
sudo systemctl enable ai-learning-assistant
sudo systemctl start ai-learning-assistant

# Configure nginx reverse proxy
sudo cp nginx.conf /etc/nginx/sites-available/ai-learning-assistant
sudo ln -s /etc/nginx/sites-available/ai-learning-assistant \
  /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### Step 4: Verify Deployment

```bash
# Check health endpoint
curl https://your-domain.com/health

# Run smoke tests
python test_api.py --url https://your-domain.com

# Check CloudWatch logs
aws logs tail /aws/lambda/ai-learning-api --follow
```

### Step 5: Configure Monitoring

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name ai-learning-assistant \
  --dashboard-body file://dashboard.json

# Create alarms
aws cloudwatch put-metric-alarm \
  --alarm-name api-error-rate \
  --alarm-description "Alert on high error rate" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold

# Set up SNS notifications
aws sns create-topic --name ai-learning-alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:REGION:ACCOUNT_ID:ai-learning-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

## Post-Deployment

### ✅ Verification
- [ ] Health endpoint returns 200
- [ ] All API endpoints responding
- [ ] Database connections working
- [ ] Bedrock integration working
- [ ] Error handling working
- [ ] Logging working

### ✅ Performance
- [ ] Response times acceptable (<5s for AI features)
- [ ] No memory leaks
- [ ] CPU usage normal
- [ ] Database queries optimized
- [ ] Caching working (if enabled)

### ✅ Monitoring
- [ ] CloudWatch dashboards showing data
- [ ] Alarms configured and working
- [ ] Error tracking capturing errors
- [ ] Cost tracking enabled
- [ ] Uptime monitoring active

### ✅ Security
- [ ] HTTPS working
- [ ] CORS configured correctly
- [ ] Rate limiting active
- [ ] Authentication working
- [ ] Authorization working
- [ ] Audit logging working

### ✅ Documentation
- [ ] API documentation accessible
- [ ] Runbooks created
- [ ] Incident response plan documented
- [ ] Rollback procedure documented
- [ ] Team trained on operations

## Rollback Plan

If deployment fails:

```bash
# Option 1: Revert Lambda function
aws lambda update-function-code \
  --function-name ai-learning-api \
  --zip-file fileb://previous-deployment.zip

# Option 2: Revert ECS service
aws ecs update-service \
  --cluster production \
  --service ai-learning-api \
  --task-definition ai-learning-assistant:PREVIOUS_VERSION

# Option 3: Revert EC2 deployment
ssh -i key.pem ec2-user@instance-ip
cd ai-learning-assistant
git checkout PREVIOUS_COMMIT
sudo systemctl restart ai-learning-assistant
```

## Monitoring Checklist

### Daily
- [ ] Check error rates
- [ ] Review CloudWatch logs
- [ ] Check API response times
- [ ] Verify all services healthy

### Weekly
- [ ] Review cost reports
- [ ] Check for security updates
- [ ] Review performance metrics
- [ ] Update documentation

### Monthly
- [ ] Security audit
- [ ] Performance optimization
- [ ] Cost optimization
- [ ] Dependency updates
- [ ] Backup verification

## Troubleshooting

### High Error Rate
1. Check CloudWatch logs
2. Verify AWS service quotas
3. Check Bedrock throttling
4. Review recent changes
5. Scale up if needed

### Slow Response Times
1. Check Bedrock latency
2. Review DynamoDB performance
3. Check network latency
4. Enable caching
5. Optimize queries

### High Costs
1. Review Bedrock usage
2. Check DynamoDB capacity
3. Review S3 storage
4. Optimize API calls
5. Enable caching

## Success Criteria

Deployment is successful when:

- [x] All health checks passing
- [x] All tests passing
- [x] Response times acceptable
- [x] Error rate <1%
- [x] Monitoring active
- [x] Alerts configured
- [x] Documentation complete
- [x] Team trained

## Emergency Contacts

- **On-Call Engineer:** [Phone/Email]
- **AWS Support:** [Support Plan Details]
- **Team Lead:** [Contact Info]
- **DevOps:** [Contact Info]

## Additional Resources

- API Documentation: https://your-domain.com/docs
- CloudWatch Dashboard: [Link]
- Status Page: [Link]
- Runbooks: [Link]
- Incident Response: [Link]

---

**Remember:** Always test in staging before deploying to production!

**Status:** Ready for Production Deployment ✅
