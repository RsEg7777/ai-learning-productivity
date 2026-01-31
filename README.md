# AI Learning & Developer Productivity Assistant

**Hackathon Submission for AWS AI Bharat 2026**

A comprehensive cloud-native learning platform built on AWS that provides intelligent content processing, interactive learning tools, and multilingual support for students and developers. This project showcases an AI-powered assistant that enhances student learning and developer workflows.

## 🎯 Features

- **Content Processing**: Upload and process text, PDFs, videos, and audio files with AI-powered summarization
- **Interactive Learning**: Generate flashcards and quizzes with spaced repetition algorithms
- **Code Analysis**: Get detailed code explanations and improvement suggestions
- **Multilingual Support**: Support for Indian languages (Hindi, Tamil, Telugu, Bengali, and more)
- **Voice Interface**: Speech-to-text and text-to-speech capabilities
- **Secure & Scalable**: Built on AWS with enterprise-grade security
- **Modern UI**: Award-winning cyan dark theme with Framer Motion animations

## 🏗️ Architecture

The system follows a serverless, event-driven architecture using:
- **AWS Lambda**: Serverless compute for microservices
- **Amazon Bedrock**: Generative AI (Claude 3.5 Sonnet) for content processing and code analysis
- **Amazon Transcribe**: Speech-to-text conversion
- **Amazon Polly**: Text-to-speech synthesis
- **Amazon Translate**: Multilingual translation
- **Amazon Comprehend**: Natural language processing
- **DynamoDB**: NoSQL database for user data and learning progress
- **S3**: Secure content storage
- **API Gateway**: RESTful API management
- **Cognito**: User authentication and authorization

## 📁 Project Structure

```
ai-learning-productivity/
├── src/                          # Backend source code
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
├── frontend/                     # React + TypeScript frontend
│   ├── src/                      # Frontend source
│   │   ├── components/           # React components
│   │   └── App.tsx               # Main application
│   └── public/                   # Static assets
├── infrastructure/               # AWS CDK infrastructure code
├── tests/                        # Test suites
│   ├── unit/                     # Unit tests
│   ├── property/                 # Property-based tests
│   └── integration/              # Integration tests
├── config/                       # Configuration files
└── docs/                         # Documentation
```

## 🚀 Live Deployment

- **Backend API**: `https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev/`
- **Frontend**: Ready for Vercel deployment
- **Region**: AWS Mumbai (ap-south-1)

## 📋 Prerequisites

- Python 3.11 or higher
- Node.js 18+ (for AWS CDK and React)
- AWS CLI configured with appropriate credentials
- AWS CDK CLI installed (`npm install -g aws-cdk`)

## 🔧 Installation

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/RsEg7777/ai-learning-productivity.git
cd ai-learning-productivity
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

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm start
```

The app will open at `http://localhost:3000`

## ⚙️ Configuration

1. Copy the example configuration:
```bash
cp config/config.example.yaml config/config.yaml
```

2. Update `config/config.yaml` with your AWS settings and preferences

3. Set environment variables:
```bash
export AWS_REGION=ap-south-1
export ENVIRONMENT=dev
```

## 🧪 Development

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

### Deploying Frontend to Vercel

```bash
cd frontend

# Using Vercel CLI
vercel

# Or for production
vercel --prod
```

See `frontend/README_DEPLOYMENT.md` for detailed deployment instructions.

## 🎨 Frontend Features

- **Cyan Dark Theme**: Modern cyberpunk aesthetic with pure cyan (#00ffff) accents
- **Custom Cursor**: Glowing cyan cursor with follower trail
- **Animations**: Smooth transitions using Framer Motion
- **Particle System**: Floating particles with connection lines
- **Responsive Design**: Works on all screen sizes
- **Interactive Components**: Quiz generator, flashcard creator, code analyzer

## 🧪 Testing Strategy

The project uses a dual testing approach:

1. **Unit Tests**: Test specific examples, edge cases, and integration points
2. **Property-Based Tests**: Validate universal properties across all inputs using Hypothesis (minimum 100 iterations)

Each property test references its corresponding design document property and validates specific requirements.

## 🔒 Security

- All data encrypted in transit (TLS) and at rest (AES-256)
- Multi-factor authentication via AWS Cognito
- Role-based access controls (RBAC)
- Comprehensive audit logging
- Data privacy controls and consent management

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:
- API Gateway Implementation
- Service Integration Guide
- Error Handling Strategy
- Multilingual Support
- And more...

## 🏆 Hackathon 2026

This project was developed for the AWS AI Bharat 2026 Hackathon, showcasing:
- Modern serverless architecture on AWS
- AI-powered learning and productivity tools
- Beautiful, award-winning UI design
- Comprehensive testing and documentation
- Production-ready deployment

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open a GitHub issue.
