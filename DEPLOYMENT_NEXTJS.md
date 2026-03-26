# Deployment Guide — Next.js + Elastic Beanstalk

## What changed

| Before | After |
|--------|-------|
| Create React App (`react-scripts`) | Next.js 14 App Router |
| `REACT_APP_API_URL` | `NEXT_PUBLIC_API_URL` |
| `frontend/build/` output | `frontend/.next/` output |
| `vercel.json` → `framework: null` | `vercel.json` → `framework: "nextjs"` |
| `public/index.html` + `_app` | `app/layout.tsx` |
| `src/App.tsx` entry point | `app/page.tsx` entry point |

---

## Local Development

### 1. Start the FastAPI backend
```bash
cd /path/to/ai-learning-productivity
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

### 2. Start the Next.js frontend
```bash
cd frontend
cp .env.example .env.local
# Edit .env.local → set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
# Opens on http://localhost:3000
```

---

## Deploy Backend → AWS Elastic Beanstalk

```bash
# From repo root
pip install awsebcli

eb init ai-learning-app \
  --platform python-3.11 \
  --region ap-south-1

eb create ai-learning-env \
  --instance-type t3.small \
  --single-instance

# Set environment variables
eb setenv \
  AWS_REGION=ap-south-1 \
  TABLE_PREFIX=ai-learning- \
  STRICT_MODE=false

# Deploy
eb deploy

# Get your URL
eb status | grep CNAME
# → ai-learning-env.eba-XXXXXXXX.ap-south-1.elasticbeanstalk.com
```

---

## Deploy Frontend → Vercel

### Step 1 — Rename the env variable in Vercel
In **Vercel Dashboard → Project Settings → Environment Variables**:

| Name | Value |
|------|-------|
| `NEXT_PUBLIC_API_URL` | `http://ai-learning-env.eba-XXXXXXXX.ap-south-1.elasticbeanstalk.com` |

> If you previously had `REACT_APP_API_URL` set, delete it and add `NEXT_PUBLIC_API_URL` instead.

### Step 2 — Push to GitHub
```bash
git add -A
git commit -m "feat: migrate frontend CRA → Next.js 14, add EB deployment"
git push
```
Vercel will auto-detect the framework from `vercel.json` and deploy.

---

## AWS Services Used

| Service | Purpose |
|---------|---------|
| **Amazon Bedrock** (Nova Pro) | AI tutor, quiz generation, code analysis, multilingual, study paths |
| **Amazon DynamoDB** | User sessions, quiz results, gamification data |
| **Amazon S3** | PDF/image uploads for multimodal processing |
| **Amazon Cognito** | Authentication (Google OAuth + username/password) |
| **Amazon Polly** | Text-to-speech |
| **Amazon Transcribe** | Speech-to-text |
| **Amazon Translate** | Multilingual support |
| **Elastic Beanstalk** | Backend hosting (FastAPI + uvicorn) |
| **Vercel** | Frontend hosting (Next.js) |

---

## Required IAM Permissions for EB Role

The Elastic Beanstalk EC2 instance role needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "dynamodb:*",
        "s3:*",
        "cognito-idp:*",
        "polly:SynthesizeSpeech",
        "transcribe:StartTranscriptionJob",
        "transcribe:GetTranscriptionJob",
        "translate:TranslateText",
        "comprehend:DetectDominantLanguage",
        "cloudwatch:PutMetricData",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Project Structure (Post-Migration)

```
ai-learning-productivity/
├── app.py                    ← FastAPI backend (all AI endpoints)
├── application.py            ← EB entry point (wraps app.py)
├── Procfile                  ← EB process: uvicorn application:application
├── requirements.txt
├── .ebextensions/
│   ├── 01_python.config
│   └── 02_packages.config
├── .platform/nginx/conf.d/
│   └── proxy.conf
├── src/
│   ├── api/                  ← FastAPI route handlers
│   ├── services/             ← Business logic + AWS service wrappers
│   └── shared/               ← AWS clients, models, utils
├── frontend/                 ← Next.js 14 App Router
│   ├── app/
│   │   ├── layout.tsx        ← Root layout (metadata, fonts)
│   │   ├── page.tsx          ← Main page (auth gate + tab routing)
│   │   └── globals.css       ← Global styles
│   ├── components/           ← All 19 UI components ('use client')
│   ├── lib/
│   │   └── config.ts         ← NEXT_PUBLIC_ env vars + endpoints
│   ├── next.config.js
│   ├── package.json          ← next, react, framer-motion
│   ├── tsconfig.json
│   ├── speech-recognition.d.ts
│   └── .env.example
└── vercel.json               ← framework: "nextjs"
```
