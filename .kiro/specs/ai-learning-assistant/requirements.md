# Requirements Document — AI Learning Assistant
## AWS AI Bharat Hackathon 2026

## System Overview

A production-grade, cloud-native AI learning platform serving students and developers in India.
All AI features are backed by Amazon Bedrock (Nova Pro + Claude Vision). No demo modes.

## Non-Functional Requirements

- **Response time:** AI endpoints complete within 30s (Nova Pro). Python code execution within 5s.
- **Availability:** 99.5% SLA via Elastic Beanstalk auto-scaling.
- **Security:** AWS Cognito auth (JWT), CORS locked in production, IAM least-privilege.
- **Scalability:** Stateless FastAPI backend, DynamoDB on-demand capacity.
- **Zero fallbacks:** Every feature calls real AWS services. No hardcoded or static responses.

---

## Requirement 1: AI Tutor with Socratic Method

**Story:** As a student, I want an AI tutor that teaches using the Socratic method so I develop deep understanding.

### Criteria
1. WHEN a user starts a session, the system SHALL create a DynamoDB-persisted session with user ID, subject, and teaching style.
2. WHEN a user asks a question, Nova Pro SHALL respond with Socratic guiding questions and/or explanations.
3. WHEN a non-English language is requested, the system SHALL translate the response into 14 Indian languages via a second Bedrock call.
4. WHEN a session is active, full conversation context SHALL be maintained across turns.

---

## Requirement 2: Interactive Code Playground

**Story:** As a developer, I want to run code and get AI feedback.

### Criteria
1. WHEN Python code is submitted, the server SHALL execute it in a restricted sandbox (no file I/O, no subprocess) and return real stdout/stderr.
2. WHEN execution succeeds, Nova Pro SHALL provide a brief code quality review.
3. WHEN an error occurs, Nova Pro SHALL explain the error and provide a corrected version.
4. WHEN a non-Python language is submitted, Nova Pro SHALL simulate the expected output and explain the code.
5. WHEN code requires stdin input, the user SHALL be able to provide it.

---

## Requirement 3: Quiz Generation

**Story:** As a learner, I want AI-generated quizzes from my notes.

### Criteria
1. WHEN content is submitted, Nova Pro SHALL generate 3–15 questions (multiple choice, true/false, fill-in-blank).
2. WHEN a quiz is submitted, the result SHALL be stored in DynamoDB and XP SHALL be awarded.
3. WHEN quiz questions are generated, each SHALL have a difficulty level and point value.

---

## Requirement 4: Flashcard Generator

**Story:** As a student, I want flashcards with spaced repetition.

### Criteria
1. WHEN content is submitted, Nova Pro SHALL generate at least 5 question/answer pairs.
2. Each flashcard SHALL have a difficulty level (easy/medium/hard) and relevant tags.
3. Cards SHALL be interactive (flip animation) in the frontend.

---

## Requirement 5: Code Analyzer

**Story:** As a developer, I want deep AI analysis of my code.

### Criteria
1. WHEN code is submitted, the system SHALL return: explanation, line-by-line analysis, issues with severity, improvement suggestions with before/after code, complexity metrics.
2. WHEN issues are found, each SHALL have a severity (info/warning/error/critical) and fix suggestion.
3. WHEN best practices apply, the system SHALL list them with documentation links.

---

## Requirement 6: Multimodal AI Processor

**Story:** As a student, I want to upload handwritten notes, diagrams, and math problems.

### Criteria
1. WHEN a handwriting image is uploaded, Claude 3.5 Sonnet v2 SHALL extract all text with confidence score.
2. WHEN a diagram image is uploaded, the model SHALL identify type, components, description, and insights.
3. WHEN a math problem image is uploaded, the model SHALL solve it step-by-step and verify.
4. WHEN a screenshot is uploaded, the model SHALL generate 3 quiz questions from the content.

---

## Requirement 7: Interview Prep *(New)*

**Story:** As a job seeker, I want AI-generated interview questions and answer evaluation.

### Criteria
1. WHEN a role/company/difficulty/topic is submitted, Nova Pro SHALL generate 8 typed questions (technical/behavioral/system design) with hints and model answers.
2. WHEN a candidate submits an answer, Nova Pro SHALL evaluate it: score (0–100), strengths, improvements, model answer highlights, follow-up questions, verdict (strong/adequate/needs_improvement).

---

## Requirement 8: Content Summarizer *(New)*

**Story:** As a student, I want to summarize long texts into digestible formats.

### Criteria
1. WHEN text is submitted with a summary type, Nova Pro SHALL generate: Brief (3–5 sentences), Detailed (comprehensive), Bullet Points (8–12 key points), or Hierarchical (outline).
2. The response SHALL also include 5 key takeaways extracted by a second AI call.
3. Content up to 6,000 characters SHALL be accepted per request.

---

## Requirement 9: Multilingual Translation *(New)*

**Story:** As an Indian student, I want educational content in my native language.

### Criteria
1. WHEN text and a target language are submitted, Nova Pro SHALL translate into the selected language.
2. WHEN translating, the system SHALL preserve technical terms in English and explain them in the target language.
3. The system SHALL support: Hindi, Hinglish, Tamil, Tanglish, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia, Urdu, Assamese, Sanskrit.

---

## Requirement 10: AI Study Buddy

**Story:** As a learner, I want a conversational AI companion for personalised guidance.

### Criteria
1. WHEN a user chats, Nova Pro SHALL respond with advice adapted to their declared learning style.
2. WHEN a goal is created, Nova Pro SHALL generate a milestone breakdown and study recommendation.
3. WHEN a session is started, Nova Pro SHALL design a 30-minute adaptive study plan tailored to the learning style.
4. WHEN a smart study path is requested, Nova Pro SHALL produce: skill gap analysis, 5–8 modules with resources, weekly schedule, daily routine, motivational tip — all as structured JSON.

---

## Requirement 11: Gamification System

**Story:** As a user, I want XP, achievements, and leaderboards to stay motivated.

### Criteria
1. WHEN activities are completed, the system SHALL award XP and persist it to DynamoDB.
2. WHEN XP thresholds are reached, the system SHALL unlock achievements and publish SNS notifications.
3. WHEN leaderboards are requested, the system SHALL return ranked user scores from DynamoDB.
4. The system SHALL support 50+ achievement types across 10 categories and 5 badge tiers.

---

## Requirement 12: Collaborative Learning Rooms

**Story:** As a student, I want to study in AI-moderated group rooms.

### Criteria
1. WHEN a room is created, Nova Pro SHALL generate relevant tags and the room SHALL be persisted to DynamoDB.
2. WHEN a user joins, Nova Pro SHALL generate a personalised welcome message with a discussion-starter.
3. WHEN a message is sent, the AI moderator SHALL decide whether to inject an educational insight.
4. WHEN a message is sent, Nova Pro SHALL generate 3 follow-up discussion prompts.

---

## Requirement 13: Authentication

### Criteria
1. WHEN a user logs in with Google, AWS Cognito Hosted UI SHALL handle the OAuth flow and return a JWT.
2. WHEN a user logs in with username/password, Cognito USER_PASSWORD_AUTH SHALL authenticate and return a JWT.
3. WHEN a guest token is issued, the user SHALL access all features with a guest_* token.
4. ALL API endpoints SHALL accept a Bearer token in the Authorization header.

---

## DynamoDB Tables

| Table | Partition Key | Sort Key | Purpose |
|---|---|---|---|
| `ai-learning-tutor-sessions` | `session_id` | — | Tutor conversation state |
| `ai-learning-quiz-results` | `result_id` | — | Quiz submission results |
| `ai-learning-user-progress` | `user_id` | — | User XP, level, streak |
| `ai-learning-flashcards` | `card_id` | — | Flashcard store |
| `ai-learning-achievements` | `user_id` | `achievement_id` | Achievement unlock state |
| `ai-learning-learning-goals` | `id` (GSI: user_id) | — | AI-generated learning goals |
| `ai-learning-study-rooms` | `id` | — | Collaborative room state |
