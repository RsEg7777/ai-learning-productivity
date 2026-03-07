/**
 * Frontend Configuration
 */

// API Configuration
export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Environment
export const ENV = process.env.REACT_APP_ENV || 'development';

// API Endpoints
export const ENDPOINTS = {
  health: `${API_URL}/health`,
  tutor: {
    startSession: `${API_URL}/tutor/start-session`,
    askQuestion: `${API_URL}/tutor/ask-question`,
    getSession: (sessionId: string) => `${API_URL}/tutor/session/${sessionId}`,
  },
  quiz: {
    generate: `${API_URL}/quiz/generate`,
  },
  code: {
    analyze: `${API_URL}/code/analyze`,
  },
  flashcards: {
    generate: `${API_URL}/flashcards/generate`,
  },
};

// Theme Configuration
export const THEME = {
  colors: {
    primary: '#00ffff',      // Cyan
    secondary: '#00cccc',    // Darker cyan
    background: '#0a0a0a',   // Dark background
    surface: '#1a1a1a',      // Surface color
    text: '#ffffff',         // White text
    textSecondary: '#cccccc', // Gray text
    error: '#ff4444',        // Error red
    success: '#00ff88',      // Success green
    warning: '#ffaa00',      // Warning orange
  },
  fonts: {
    primary: "'Inter', sans-serif",
    mono: "'Fira Code', monospace",
  },
  borderRadius: {
    small: '4px',
    medium: '8px',
    large: '16px',
  },
  shadows: {
    small: '0 2px 4px rgba(0, 255, 255, 0.1)',
    medium: '0 4px 8px rgba(0, 255, 255, 0.2)',
    large: '0 8px 16px rgba(0, 255, 255, 0.3)',
    glow: '0 0 20px rgba(0, 255, 255, 0.5)',
  },
};

// Feature Flags
export const FEATURES = {
  gamification: true,
  voiceInterface: false, // Coming soon
  collaboration: false,  // Coming soon
  multimodal: false,     // Coming soon
};

// App Configuration
export const APP_CONFIG = {
  name: 'AI Learning Assistant',
  version: '1.0.0',
  description: 'AI-powered learning platform',
  maxSessionDuration: 3600000, // 1 hour in ms
  autoSaveInterval: 30000,     // 30 seconds
};

export default {
  API_URL,
  ENV,
  ENDPOINTS,
  THEME,
  FEATURES,
  APP_CONFIG,
};
