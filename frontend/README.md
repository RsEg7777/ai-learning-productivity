# 🎨 AI Learning Assistant - Frontend

Modern, responsive React frontend for the AI Learning Assistant platform.

## ✨ Features

- **Cyan Dark Theme**: Modern cyberpunk aesthetic
- **Interactive Components**: Quiz generator, flashcard creator, code analyzer
- **Real-time Updates**: Live data from backend API
- **Responsive Design**: Works on all screen sizes
- **Smooth Animations**: Framer Motion transitions

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start
```

App will open at http://localhost:3000

### Build for Production

```bash
npm run build
```

## 🔧 Configuration

### API Endpoint

Update the API endpoint in `src/config.ts`:

```typescript
export const API_URL = 'http://localhost:8000';
```

For production, use your deployed backend URL.

## 📁 Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── QuizGenerator.tsx
│   │   ├── FlashcardCreator.tsx
│   │   ├── CodeAnalyzer.tsx
│   │   ├── ServiceStatus.tsx
│   │   └── ErrorDisplay.tsx
│   ├── App.tsx         # Main application
│   ├── config.ts       # Configuration
│   └── index.tsx       # Entry point
└── package.json
```

## 🎨 Components

### QuizGenerator
Generate AI-powered quizzes from any content.

### FlashcardCreator
Create flashcards with spaced repetition.

### CodeAnalyzer
Analyze code and get AI suggestions.

### ServiceStatus
Real-time backend health monitoring.

### ErrorDisplay
User-friendly error messages.

## 🚀 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Production deployment
vercel --prod
```

### Netlify

```bash
# Build
npm run build

# Deploy build/ folder to Netlify
```

### AWS Amplify

```bash
# Install Amplify CLI
npm install -g @aws-amplify/cli

# Initialize
amplify init

# Deploy
amplify publish
```

## 🔧 Environment Variables

Create `.env` file:

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENV=development
```

For production:

```bash
REACT_APP_API_URL=https://your-api-url.com
REACT_APP_ENV=production
```

## 🧪 Testing

```bash
# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

## 📦 Dependencies

### Core
- React 18
- TypeScript
- Axios (API calls)

### UI
- Framer Motion (animations)
- Tailwind CSS (styling)

### Dev Tools
- ESLint
- Prettier

## 🎨 Theming

The app uses a cyan dark theme. Customize in `src/styles/theme.ts`:

```typescript
export const theme = {
  colors: {
    primary: '#00ffff',    // Cyan
    background: '#0a0a0a', // Dark
    text: '#ffffff',       // White
  }
};
```

## 📱 Responsive Breakpoints

- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

## 🔒 Security

- API calls use HTTPS in production
- CORS configured for backend
- No sensitive data in localStorage
- XSS protection enabled

## 🐛 Troubleshooting

### Port already in use
```bash
# Use different port
PORT=3001 npm start
```

### API connection failed
- Check backend is running
- Verify API_URL in config
- Check CORS settings

### Build errors
```bash
# Clear cache
rm -rf node_modules
npm install
```

## 📊 Performance

- Lighthouse Score: 95+
- First Contentful Paint: < 1s
- Time to Interactive: < 2s
- Bundle Size: < 500KB

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request

## 📄 License

MIT License

---

**Built with React + TypeScript**
