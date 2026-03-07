# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Navigation Tabs                                          │  │
│  │  ├─ AI Tutor                                             │  │
│  │  ├─ 🎯 AI Study Buddy (NEW)                             │  │
│  │  ├─ 👥 Collaborative Learning (NEW)                     │  │
│  │  ├─ Code Playground (AI Enhanced)                       │  │
│  │  ├─ Multimodal AI (AI Enhanced)                         │  │
│  │  ├─ Flashcards (AI Enhanced)                            │  │
│  │  └─ Code Analyzer (AI Enhanced)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS/REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Endpoints                                            │  │
│  │  ├─ /code/analyze                                        │  │
│  │  ├─ /flashcards/generate                                 │  │
│  │  ├─ /playground/execute                                  │  │
│  │  ├─ /multimodal/*                                        │  │
│  │  ├─ /study-buddy/* (NEW)                                │  │
│  │  └─ /collaborative/* (NEW)                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ AWS SDK (Boto3)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS Services                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  AWS Bedrock                                              │  │
│  │  ├─ Claude 4 Sonnet (Text Generation)                   │  │
│  │  ├─ Claude Vision (Image Processing)                    │  │
│  │  └─ Adaptive AI (Context-Aware Responses)               │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DynamoDB (Optional)                                      │  │
│  │  ├─ Learning Goals                                       │  │
│  │  ├─ Study Sessions                                       │  │
│  │  ├─ Collaborative Rooms                                  │  │
│  │  └─ User Progress                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature Architecture

### 1. AI Study Buddy Flow

```
User Action                    Backend Processing              AI Processing
─────────────────────────────────────────────────────────────────────────────

Create Goal                    POST /study-buddy/create-goal
  │                                   │
  ├─ Title: "Master React"           │
  ├─ Target Date                     │
  └─ Learning Style: Visual          │
                                     │
                                     ├─ Build AI Prompt
                                     │  ├─ Include goal details
                                     │  ├─ Add learning style
                                     │  └─ Request milestones
                                     │
                                     ▼
                              AWS Bedrock (Claude)
                                     │
                                     ├─ Analyze topic complexity
                                     ├─ Generate 5-7 milestones
                                     ├─ Estimate time per milestone
                                     └─ Recommend techniques
                                     │
                                     ▼
                              JSON Response
                                     │
                                     ├─ Milestones array
                                     ├─ Recommendations
                                     └─ Study techniques
                                     │
                                     ▼
Display Learning Path          Return to Frontend
  │                                   │
  ├─ Progress: 0%                    │
  ├─ Milestone 1: Basics             │
  ├─ Milestone 2: Hooks              │
  └─ Start Session button            │
```

### 2. Collaborative Learning Flow

```
User Action                    Backend Processing              AI Moderation
─────────────────────────────────────────────────────────────────────────────

Join Room                      POST /collaborative/join-room
  │                                   │
  └─ Room ID                         │
                                     │
                                     ├─ Fetch room details
                                     ├─ Get participants
                                     └─ Load recent messages
                                     │
                                     ▼
Display Room                   Return room data
  │                                   │
  ├─ Participants list               │
  ├─ Chat history                    │
  └─ AI Moderator welcome            │
                                     │
Send Message                   POST /collaborative/send-message
  │                                   │
  └─ "How do closures work?"         │
                                     │
                                     ├─ Store message
                                     ├─ Broadcast to participants
                                     └─ Analyze for AI response
                                     │
                                     ▼
                              AWS Bedrock (Claude)
                                     │
                                     ├─ Analyze message context
                                     ├─ Determine if intervention needed
                                     ├─ Generate helpful response
                                     └─ Create follow-up suggestions
                                     │
                                     ▼
AI Moderator Response          Return AI response
  │                                   │
  ├─ Explanation of closures         │
  ├─ Code example                    │
  └─ Suggestions:                    │
      ├─ "Can you elaborate?"        │
      └─ "Try this example"          │
```

### 3. AI-Enhanced Code Playground Flow

```
User Action                    Backend Processing              AI Analysis
─────────────────────────────────────────────────────────────────────────────

Write Code                     
  │
  ├─ Language: Python
  └─ Code: "print('Hello')"
                                     
Click "Run Code"               POST /playground/execute
  │                                   │
  └─ Send code + language            │
                                     │
                                     ├─ Build analysis prompt
                                     │  ├─ Include code
                                     │  ├─ Specify language
                                     │  └─ Request analysis
                                     │
                                     ▼
                              AWS Bedrock (Claude)
                                     │
                                     ├─ Analyze code syntax
                                     ├─ Detect errors
                                     ├─ Simulate execution
                                     └─ Generate suggestions
                                     │
                                     ▼
                              JSON Response
                                     │
                                     ├─ has_errors: false
                                     ├─ output: "Hello"
                                     └─ ai_suggestion: "..."
                                     │
                                     ▼
Display Results                Return to Frontend
  │                                   │
  ├─ Output: "Hello"                 │
  ├─ Execution time                  │
  └─ AI Suggestions                  │
```

### 4. Multimodal AI Processing Flow

```
User Action                    Backend Processing              AI Vision
─────────────────────────────────────────────────────────────────────────────

Upload Image                   
  │
  ├─ Mode: Handwriting OCR
  └─ Image file
                                     
Click "Process"                POST /multimodal/process-handwriting
  │                                   │
  └─ Send image + mode               │
                                     │
                                     ├─ Read image data
                                     ├─ Convert to base64
                                     └─ Build vision prompt
                                     │
                                     ▼
                              AWS Bedrock (Claude Vision)
                                     │
                                     ├─ Analyze image
                                     ├─ Extract text (OCR)
                                     ├─ Detect language
                                     └─ Calculate confidence
                                     │
                                     ▼
                              JSON Response
                                     │
                                     ├─ text: "extracted text"
                                     ├─ confidence: "95%"
                                     ├─ language: "English"
                                     └─ wordsDetected: 42
                                     │
                                     ▼
Display Results                Return to Frontend
  │                                   │
  ├─ Extracted text                  │
  ├─ Confidence score                │
  └─ Metadata                        │
```

---

## Data Flow Diagram

```
┌──────────────┐
│   Browser    │
│  (React UI)  │
└──────┬───────┘
       │
       │ 1. User Interaction
       │
       ▼
┌──────────────┐
│  Component   │
│  (TypeScript)│
└──────┬───────┘
       │
       │ 2. API Call (fetch)
       │
       ▼
┌──────────────┐
│   FastAPI    │
│   Endpoint   │
└──────┬───────┘
       │
       │ 3. Process Request
       │
       ▼
┌──────────────┐
│  Bedrock     │
│   Client     │
└──────┬───────┘
       │
       │ 4. Invoke AI Model
       │
       ▼
┌──────────────┐
│ AWS Bedrock  │
│ Claude 4     │
└──────┬───────┘
       │
       │ 5. AI Response
       │
       ▼
┌──────────────┐
│   FastAPI    │
│   Response   │
└──────┬───────┘
       │
       │ 6. JSON Data
       │
       ▼
┌──────────────┐
│  Component   │
│   Update     │
└──────┬───────┘
       │
       │ 7. Render UI
       │
       ▼
┌──────────────┐
│   Browser    │
│   Display    │
└──────────────┘
```

---

## Component Hierarchy

```
App.tsx
├── Login.tsx
├── CustomCursor.tsx
├── Header
│   ├── Title
│   └── Logout Button
├── Navigation Tabs
│   ├── AI Tutor
│   ├── AI Study Buddy ⭐ NEW
│   ├── Collaborative Learning ⭐ NEW
│   ├── Study Timer
│   ├── Progress Tracker
│   ├── Code Playground
│   ├── Gamification
│   ├── Multimodal AI
│   ├── Notes
│   ├── Quiz Generator
│   ├── Flashcard Generator
│   └── Code Analyzer
└── Footer
```

---

## API Endpoint Structure

```
/api
├── /tutor
│   ├── POST /start-session
│   └── POST /ask-question
│
├── /study-buddy ⭐ NEW
│   ├── GET  /goals
│   ├── POST /create-goal
│   ├── POST /chat
│   └── POST /start-session
│
├── /collaborative ⭐ NEW
│   ├── GET  /rooms
│   ├── POST /create-room
│   ├── POST /join-room
│   └── POST /send-message
│
├── /code
│   └── POST /analyze
│
├── /playground
│   └── POST /execute
│
├── /flashcards
│   └── POST /generate
│
├── /multimodal
│   ├── POST /process-handwriting
│   ├── POST /understand-diagram
│   ├── POST /solve-math
│   └── POST /screenshot-to-quiz
│
├── /quiz
│   └── POST /generate
│
└── /gamification
    ├── POST /award-xp
    ├── GET  /stats/{user_id}
    ├── GET  /leaderboard
    └── GET  /achievements/{user_id}
```

---

## State Management

### Frontend State

```typescript
// App-level State
- isAuthenticated: boolean
- authToken: string
- username: string
- activeTab: string

// AI Study Buddy State
- learningGoals: LearningGoal[]
- currentSession: StudySession | null
- chatMessages: Message[]
- learningStyle: 'visual' | 'auditory' | 'kinesthetic' | 'reading'
- aiInsight: string

// Collaborative Learning State
- rooms: StudyRoom[]
- currentRoom: StudyRoom | null
- participants: Participant[]
- messages: Message[]
- aiSuggestions: string[]
```

### Backend State

```python
# In-Memory (Current)
- services_initialized: bool
- tutor_service: ConversationalTutor
- quiz_service: QuizGenerator
- code_analyzer: CodeAnalyzer
- health_status: dict

# DynamoDB (Future)
- learning_goals: Table
- study_sessions: Table
- collaborative_rooms: Table
- user_progress: Table
- chat_history: Table
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Authentication Layer                                     │
│     ├─ Bearer Token Validation                             │
│     ├─ JWT Token Parsing                                   │
│     └─ Session Management                                  │
│                                                              │
│  2. Authorization Layer (Future)                            │
│     ├─ Role-Based Access Control                           │
│     ├─ Resource Permissions                                │
│     └─ API Rate Limiting                                   │
│                                                              │
│  3. Input Validation                                        │
│     ├─ Pydantic Models                                     │
│     ├─ Type Checking                                       │
│     └─ Sanitization                                        │
│                                                              │
│  4. API Security                                            │
│     ├─ CORS Configuration                                  │
│     ├─ HTTPS Enforcement                                   │
│     └─ Request Size Limits                                 │
│                                                              │
│  5. AWS Security                                            │
│     ├─ IAM Roles & Policies                               │
│     ├─ Bedrock Access Control                             │
│     └─ Credential Management                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Scalability Considerations

### Horizontal Scaling

```
Load Balancer
     │
     ├─── FastAPI Instance 1
     ├─── FastAPI Instance 2
     ├─── FastAPI Instance 3
     └─── FastAPI Instance N
            │
            └─── AWS Bedrock (Shared)
```

### Caching Strategy

```
Request → Cache Check → Cache Hit? → Return Cached
                │
                └─ Cache Miss → AWS Bedrock → Cache Result → Return
```

### Database Scaling

```
Application
     │
     ├─── DynamoDB (Primary)
     │      ├─ Auto-scaling
     │      └─ Global Tables
     │
     └─── ElastiCache (Optional)
            └─ Session Storage
```

---

## Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Application Logs                                           │
│  ├─ FastAPI Logs                                           │
│  ├─ Error Tracking                                         │
│  └─ Request/Response Logs                                  │
│                                                              │
│  AWS CloudWatch                                             │
│  ├─ Bedrock API Metrics                                    │
│  ├─ Lambda Metrics (if used)                               │
│  └─ DynamoDB Metrics                                       │
│                                                              │
│  Custom Metrics                                             │
│  ├─ Feature Usage                                          │
│  ├─ AI Response Times                                      │
│  ├─ User Engagement                                        │
│  └─ Error Rates                                            │
│                                                              │
│  Alerts                                                     │
│  ├─ High Error Rate                                        │
│  ├─ Slow Response Times                                    │
│  └─ Service Unavailability                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Development

```
Local Machine
├── Backend: localhost:8000
├── Frontend: localhost:3000
└── AWS: Development Account
```

### Production

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Setup                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend (Vercel/Netlify)                                  │
│  ├─ CDN Distribution                                        │
│  ├─ HTTPS Certificate                                       │
│  └─ Custom Domain                                           │
│                                                              │
│  Backend (AWS)                                              │
│  ├─ Option 1: Lambda + API Gateway                         │
│  ├─ Option 2: ECS/Fargate                                  │
│  └─ Option 3: EC2 with Auto-scaling                        │
│                                                              │
│  Database (AWS)                                             │
│  ├─ DynamoDB                                                │
│  └─ ElastiCache (Optional)                                  │
│                                                              │
│  AI Services (AWS)                                          │
│  └─ Bedrock (Claude 4)                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React + TypeScript | UI Components |
| Animation | Framer Motion | Smooth transitions |
| Styling | CSS Variables | Theming |
| Backend | FastAPI | REST API |
| Validation | Pydantic | Data models |
| AI/ML | AWS Bedrock | Claude 4 Sonnet |
| Vision AI | Claude Vision | Image processing |
| Database | DynamoDB | Data persistence |
| Auth | JWT | Authentication |
| Deployment | Vercel + AWS | Hosting |

---

This architecture provides a solid foundation for a scalable, maintainable, and feature-rich AI learning platform! 🚀
