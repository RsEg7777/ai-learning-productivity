# AWS Resources & Required Environment Variables

Purpose
-------
This document lists the AWS resources the project expects in production, the minimum environment
variables the application needs to run, and quick example commands to provision resources for
development and deployment. Use this as a checklist when deploying backend services.

High-level services required
---------------------------
- S3: content and media storage (uploads, audio files, processed artifacts)
- DynamoDB: tables for content metadata, sessions, user data, caches
- Amazon Bedrock: primary LLM provider (or SageMaker fallback)
- Cognito: user pool + app client for authentication (optional if using external auth)
- Amazon Polly, Transcribe, Translate: TTS/STT/translation services used by voice features
- SNS: notifications (optional)
- CloudWatch: logging & metrics
- IAM: roles for Lambda/EC2/Elastic Beanstalk with appropriate policies

Minimal environment variables (example keys used by the codebase)
---------------------------------------------------------------
Set these for any deployed environment (Elastic Beanstalk, Lambda, or container).

- `AWS_REGION` — AWS region (e.g., `us-east-1`)
- `AWS_ACCESS_KEY_ID` — AWS credentials (use IAM roles in prod instead)
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN` (optional, for temporary creds)
- `S3_BUCKET_NAME` — bucket for uploaded assets
- `DYNAMODB_TABLE_PREFIX` or `DYNAMODB_TABLE_NAME` — prefix or name used by services
- `COGNITO_USER_POOL_ID` — if using Cognito
- `COGNITO_CLIENT_ID`
- `BEDROCK_MODEL_ID` — Bedrock model identifier to invoke
- `OUTPUT_PROVIDER` or `ONLY_AWS_OUTPUTS` — set to `aws_only`/`true` to enforce AWS-only outputs
- `USE_LOCAL_MODELS` — `true` in CI/test to avoid live AWS calls
- `ALLOW_SAGEMAKER_FALLBACK` — `true|false` if SageMaker fallback allowed
- `SAGEMAKER_ENDPOINT_NAME` — for SageMaker fallback
- `AUTOML_ENDPOINT_NAME` — for AutoML fallback (if used)
- `POLLY_VOICE` — default voice name (e.g., `Joanna`)
- `TRANSCRIBE_ROLE_ARN` — role ARN that gives Transcribe access to S3
- `SNS_TOPIC_ARN` (optional)
- `LOG_LEVEL` — `INFO`, `DEBUG`, etc.

Local/dev notes
---------------
- Run tests and local dev with a mock mode:

```powershell
$env:USE_LOCAL_MODELS = 'true'
pytest -q
```

- For local testing you can set fake values for AWS keys, but rely on `USE_LOCAL_MODELS=true`.

Quick provisioning examples (CLI)
--------------------------------
S3 (create bucket):

```bash
aws s3api create-bucket --bucket my-app-content-bucket --create-bucket-configuration LocationConstraint=us-east-1
```

DynamoDB (basic table for content metadata):

```bash
aws dynamodb create-table \
  --table-name content-table \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

IAM (create a role for Transcribe to access S3):

1. Create trust policy allowing Transcribe service to assume the role.
2. Attach an inline policy that permits `s3:GetObject`/`s3:PutObject` on your bucket.

Bedrock and LLMs
-----------------
- Ensure the executing IAM principal has Bedrock permissions (Bedrock:InvokeModel).
- Configure `BEDROCK_MODEL_ID` to the model you want (e.g., Anthropic / Claude or your Bedrock model id).
- If you prefer SageMaker fallbacks, create a SageMaker endpoint and set `SAGEMAKER_ENDPOINT_NAME`.

Deployment options
------------------
- Lambda: package application (or use the `deployed-lambda/` folder), create a Lambda with runtime Python 3.12,
  set environment variables in the function configuration, and attach an IAM role that grants access to S3/DynamoDB/Bedrock.
- Elastic Beanstalk: create an EB application/environment with Python 3.12 platform; set environment variables via
  `eb setenv VAR1=val VAR2=val` or AWS Console.
- Containers/ECS: provide the env vars in the task definition or secrets via SSM/Secrets Manager.

Secrets & best practices
------------------------
- Do NOT commit AWS credentials to source. Use IAM instance/profile roles or store sensitive values in AWS Secrets Manager
  or Parameter Store and reference them from your runtime environment.
- Prefer IAM roles (Lambda execution role / EB instance role) over static credentials in production.

Suggested automation
--------------------
- Use CloudFormation or Terraform to declare S3 buckets, DynamoDB tables, IAM roles, and policy attachments.
- Include a small CloudFormation template that creates the expected DynamoDB table names and IAM roles for Transcribe and Bedrock access.

What to check after provisioning
--------------------------------
- Confirm `S3_BUCKET_NAME` exists and the runtime principal can read/write objects.
- Confirm DynamoDB tables exist and have expected partition keys.
- Verify Bedrock access by running a small `invoke_model` call with the configured `BEDROCK_MODEL_ID`.
- For voice features: confirm `TRANSCRIBE_ROLE_ARN` is set and that the role can access the bucket.

References
----------
- Use the AWS Console or CLI docs for creating S3, DynamoDB, Cognito, and IAM policies.
- Prefer deploying infra via Terraform/CloudFormation for reproducibility.

If you'd like, I can:

- Generate a minimal CloudFormation template for the S3 bucket + DynamoDB table + IAM role needed for Transcribe, or
- Add a `.env.example` file at the repo root with the variable keys shown above.

Remediation checklist (quick)
-----------------------------
Use this checklist after provisioning cloud resources and before deploying the app.

- [ ] Create S3 bucket and set `S3_BUCKET_NAME`.
- [ ] Create DynamoDB table(s) and set `DYNAMODB_TABLE_NAME` (or prefix).
- [ ] Deploy or confirm Bedrock access and set `BEDROCK_MODEL_ID`.
- [ ] Create/assign IAM roles (Lambda/EB/ECS task) that allow access to S3, DynamoDB, and Bedrock.
- [ ] Create Transcribe IAM role and set `TRANSCRIBE_ROLE_ARN`.
- [ ] Set any Cognito variables (`COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`) if using Cognito.
- [ ] Review `OUTPUT_PROVIDER` / `ONLY_AWS_OUTPUTS` and set to enforce AWS-only outputs.
- [ ] Store secrets in Secrets Manager / Parameter Store; do not hardcode creds.
- [ ] Run `pytest` with `USE_LOCAL_MODELS=true` locally and in CI to validate behavior without live AWS.

CI enforcement
--------------
We recommend enabling the included GitHub Actions workflow (`.github/workflows/ci.yml`) which runs tests with `USE_LOCAL_MODELS=true` and will fail if any non-AWS model provider strings are referenced under `src/`.

