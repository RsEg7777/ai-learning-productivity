# AI Learning Assistant - Frontend

Modern React + TypeScript frontend for the AI Learning Assistant.

## Features

- 📝 **Quiz Generator**: Generate AI-powered quizzes with multiple question types
- 🎴 **Flashcard Generator**: Create flashcards for spaced repetition learning
- 💻 **Code Analyzer**: Get AI explanations of your code
- 🔐 **Authentication**: Secure login with Cognito tokens

## Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm start
```

The app will open at `http://localhost:3000`

### 3. Login

You'll need your Cognito ID token. Get it from the PowerShell test script:

```powershell
# In the root directory
.\test_live_api.ps1
```

Copy the token value and paste it into the login screen.

## Build for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` folder.

## Deploy to Vercel (Free)

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Deploy:
```bash
cd frontend
vercel
```

Follow the prompts and your app will be live!

## Deploy to Netlify (Free)

1. Build the app:
```bash
npm run build
```

2. Drag and drop the `build/` folder to [Netlify Drop](https://app.netlify.com/drop)

## API Configuration

The API endpoint is hardcoded in each component:
```typescript
const API_URL = 'https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev';
```

To change it, update the `API_URL` constant in:
- `src/components/QuizGenerator.tsx`
- `src/components/FlashcardGenerator.tsx`
- `src/components/CodeAnalyzer.tsx`

## Tech Stack

- React 19
- TypeScript
- CSS3 (Custom styling, no frameworks)
- Fetch API for HTTP requests

## Project Structure

```
frontend/
├── public/           # Static files
├── src/
│   ├── components/   # React components
│   │   ├── Login.tsx
│   │   ├── QuizGenerator.tsx
│   │   ├── FlashcardGenerator.tsx
│   │   └── CodeAnalyzer.tsx
│   ├── App.tsx       # Main app component
│   ├── App.css       # Global styles
│   └── index.tsx     # Entry point
└── package.json
```

## Notes

- The app requires a valid Cognito ID token to work
- Token expires after 1 hour (default Cognito setting)
- All API calls go directly to AWS API Gateway
- No backend proxy needed
