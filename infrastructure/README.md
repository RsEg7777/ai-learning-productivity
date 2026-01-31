# AI Learning Assistant Infrastructure

This directory contains AWS CDK infrastructure code for deploying the AI Learning Assistant.

## Prerequisites

- Node.js 18+ installed
- AWS CLI configured with appropriate credentials
- AWS CDK CLI installed: `npm install -g aws-cdk`

## Setup

1. Install dependencies:
```bash
npm install
```

2. Bootstrap CDK (first time only):
```bash
cdk bootstrap
```

## Deployment

### Deploy to Development Environment

```bash
cdk deploy --context environment=dev
```

### Deploy to Production Environment

```bash
cdk deploy --context environment=prod
```

### Deploy All Stacks

```bash
cdk deploy --all
```

## Infrastructure Components

### Storage
- **S3 Bucket**: Encrypted storage for user content (text, PDFs, videos, audio)
  - AES-256 encryption at rest
  - Versioning enabled
  - Block public access
  - Lifecycle rules for old versions

### Database
- **DynamoDB Tables**:
  - User Progress Table: Track learning progress and statistics
  - Quiz Results Table: Store quiz attempts and scores
  - Flashcards Table: Store generated flashcards
  - Content Metadata Table: Store content metadata and processing status
  - All tables use on-demand billing and AWS-managed encryption

### Authentication
- **Cognito User Pool**: User authentication and authorization
  - Email and username sign-in
  - Multi-factor authentication (optional)
  - Password policy enforcement
  - Email verification

### Compute
- **Lambda Functions**: Serverless compute for microservices
  - Python 3.11 runtime
  - Shared layer for common dependencies
  - IAM roles with least-privilege permissions

### API
- **API Gateway**: RESTful API with Cognito authorization
  - Rate limiting (1000 req/s)
  - Burst limiting (2000 req/s)
  - CORS enabled
  - CloudWatch logging

### AI/ML Services (IAM Permissions)
- Amazon Bedrock: Generative AI for content processing
- Amazon Transcribe: Speech-to-text conversion
- Amazon Polly: Text-to-speech synthesis
- Amazon Translate: Multilingual translation
- Amazon Comprehend: Natural language processing

## Useful Commands

- `npm run build`: Compile TypeScript to JavaScript
- `npm run watch`: Watch for changes and compile
- `cdk synth`: Synthesize CloudFormation template
- `cdk diff`: Compare deployed stack with current state
- `cdk deploy`: Deploy stack to AWS
- `cdk destroy`: Remove stack from AWS

## Stack Outputs

After deployment, the following outputs are available:

- `ContentBucketName`: S3 bucket name for content storage
- `UserPoolId`: Cognito User Pool ID
- `UserPoolClientId`: Cognito User Pool Client ID
- `APIEndpoint`: API Gateway endpoint URL
- `UserProgressTableName`: DynamoDB User Progress table name
- `QuizResultsTableName`: DynamoDB Quiz Results table name
- `FlashcardsTableName`: DynamoDB Flashcards table name
- `ContentMetadataTableName`: DynamoDB Content Metadata table name

## Security

- All data encrypted in transit (TLS) and at rest (AES-256)
- IAM roles follow least-privilege principle
- Cognito provides secure authentication with MFA support
- API Gateway enforces rate limiting
- CloudWatch logs enabled for audit trail

## Cost Optimization

- DynamoDB uses on-demand billing (pay per request)
- Lambda functions use ARM64 architecture where possible
- S3 lifecycle rules delete old versions after 90 days
- CloudWatch logs retention set to 1 week for non-production

## Cleanup

To remove all infrastructure:

```bash
cdk destroy --all
```

**Warning**: This will delete all resources including data in DynamoDB tables and S3 buckets (except in production environment where retention is enabled).
