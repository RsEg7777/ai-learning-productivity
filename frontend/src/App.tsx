import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';
import QuizGenerator from './components/QuizGenerator';
import FlashcardGenerator from './components/FlashcardGenerator';
import CodeAnalyzer from './components/CodeAnalyzer';
import AITutorChat from './components/AITutorChat';
import CodePlayground from './components/CodePlayground';
import GamificationDashboard from './components/GamificationDashboard';
import MultimodalProcessor from './components/MultimodalProcessor';
import StudyTimer from './components/StudyTimer';
import ProgressTracker from './components/ProgressTracker';
import NoteTaker from './components/NoteTaker';
import Login from './components/Login';
import CustomCursor from './components/CustomCursor';

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 }
};

const headerVariants = {
  initial: { opacity: 0, y: -50 },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: {
      duration: 0.8,
      ease: [0.6, -0.05, 0.01, 0.99] as any
    }
  }
};

const tabVariants = {
  initial: { scale: 0.8, opacity: 0 },
  animate: (i: number) => ({
    scale: 1,
    opacity: 1,
    transition: {
      delay: i * 0.1,
      duration: 0.5,
      ease: [0.6, -0.05, 0.01, 0.99] as any
    }
  }),
  hover: {
    scale: 1.05,
    transition: { duration: 0.2 }
  },
  tap: { scale: 0.95 }
};

function App() {
  const [activeTab, setActiveTab] = useState('tutor');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authToken, setAuthToken] = useState('');
  const [username, setUsername] = useState('');

  // Check for stored token on mount
  useEffect(() => {
    const hash = window.location.hash;
    if (hash) {
      const params = new URLSearchParams(hash.substring(1));
      const idToken = params.get('id_token');
      
      if (idToken) {
        localStorage.setItem('authToken', idToken);
        try {
          const payload = JSON.parse(atob(idToken.split('.')[1]));
          const email = payload.email || payload['cognito:username'] || 'User';
          const displayName = email.split('@')[0];
          localStorage.setItem('username', displayName);
          setUsername(displayName);
        } catch (e) {
          localStorage.setItem('username', 'User');
          setUsername('User');
        }
        
        setAuthToken(idToken);
        setIsAuthenticated(true);
        window.history.replaceState(null, '', window.location.pathname);
        return;
      }
    }
    
    const storedToken = localStorage.getItem('authToken');
    const storedUsername = localStorage.getItem('username');
    if (storedToken) {
      setAuthToken(storedToken);
      setIsAuthenticated(true);
      if (storedUsername) setUsername(storedUsername);
    }
  }, []);

  const handleLogin = (token: string) => {
    setAuthToken(token);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('username');
    setAuthToken('');
    setIsAuthenticated(false);
    setUsername('');
  };

  if (!isAuthenticated) {
    return (
      <>
        <Login onLogin={handleLogin} />
      </>
    );
  }

  return (
    <div className="App">
      <CustomCursor />
      <motion.header 
        className="App-header"
        variants={headerVariants}
        initial="initial"
        animate="animate"
      >
        <motion.h1
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{
            duration: 0.8,
            ease: [0.6, -0.05, 0.01, 0.99] as any
          }}
        >
          🎓 AI Learning Assistant
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.6 }}
        >
          Powered by AWS Bedrock & Claude AI
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          style={{ 
            position: 'absolute', 
            top: '1.5rem', 
            right: '2rem',
            display: 'flex', 
            alignItems: 'center', 
            gap: '1rem' 
          }}
        >
          {username && (
            <span style={{ color: '#00ffff', fontSize: '0.9rem' }}>
              👋 <strong>{username}</strong>
            </span>
          )}
          <motion.button
            onClick={handleLogout}
            whileHover={{ scale: 1.05, boxShadow: '0 0 20px rgba(255, 107, 107, 0.5)' }}
            whileTap={{ scale: 0.95 }}
            style={{
              background: 'rgba(255, 0, 0, 0.1)',
              border: '1px solid rgba(255, 107, 107, 0.3)',
              color: '#ff6b6b',
              padding: '0.5rem 1.2rem',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: '600',
              transition: 'all 0.3s ease'
            }}
          >
            🚪 Logout
          </motion.button>
        </motion.div>
      </motion.header>

      <nav className="nav-tabs">
        {[
          { id: 'tutor', label: '🤖 AI Tutor', icon: '🤖' },
          { id: 'timer', label: '⏱️ Study Timer', icon: '⏱️' },
          { id: 'progress', label: '📊 Progress', icon: '📊' },
          { id: 'playground', label: '💻 Code Playground', icon: '💻' },
          { id: 'gamification', label: '🎮 Gamification', icon: '🎮' },
          { id: 'multimodal', label: '🖼️ Multimodal AI', icon: '🖼️' },
          { id: 'notes', label: '📓 Notes', icon: '📓' },
          { id: 'quiz', label: '📝 Quiz', icon: '📝' },
          { id: 'flashcards', label: '🎴 Flashcards', icon: '🎴' },
          { id: 'code', label: '🔍 Code Analysis', icon: '🔍' }
        ].map((tab, i) => (
          <motion.button
            key={tab.id}
            custom={i}
            variants={tabVariants}
            initial="initial"
            animate="animate"
            whileHover="hover"
            whileTap="tap"
            className={activeTab === tab.id ? 'active' : ''}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </motion.button>
        ))}
      </nav>

      <main className="main-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.4 }}
          >
            {activeTab === 'tutor' && <AITutorChat authToken={authToken} />}
            {activeTab === 'timer' && <StudyTimer authToken={authToken} />}
            {activeTab === 'progress' && <ProgressTracker authToken={authToken} />}
            {activeTab === 'playground' && <CodePlayground authToken={authToken} />}
            {activeTab === 'gamification' && <GamificationDashboard authToken={authToken} />}
            {activeTab === 'multimodal' && <MultimodalProcessor authToken={authToken} />}
            {activeTab === 'notes' && <NoteTaker />}
            {activeTab === 'quiz' && <QuizGenerator authToken={authToken} />}
            {activeTab === 'flashcards' && <FlashcardGenerator authToken={authToken} />}
            {activeTab === 'code' && <CodeAnalyzer authToken={authToken} />}
          </motion.div>
        </AnimatePresence>
      </main>

      <motion.footer 
        className="App-footer"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 0.6 }}
      >
        <p>AI for Learning & Developer Productivity | Hackathon 2026</p>
      </motion.footer>
    </div>
  );
}

export default App;