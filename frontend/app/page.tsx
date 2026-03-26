'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

import AITutorChat from '@/components/AITutorChat';
import AIStudyBuddy from '@/components/AIStudyBuddy';
import CollaborativeLearning from '@/components/CollaborativeLearning';
import StudyTimer from '@/components/StudyTimer';
import ProgressTracker from '@/components/ProgressTracker';
import CodePlayground from '@/components/CodePlayground';
import GamificationDashboard from '@/components/GamificationDashboard';
import MultimodalProcessor from '@/components/MultimodalProcessor';
import NoteTaker from '@/components/NoteTaker';
import QuizGenerator from '@/components/QuizGenerator';
import FlashcardGenerator from '@/components/FlashcardGenerator';
import CodeAnalyzer from '@/components/CodeAnalyzer';
import InterviewPrep from '@/components/InterviewPrep';
import ContentSummarizer from '@/components/ContentSummarizer';
import TranslationTool from '@/components/TranslationTool';
import Login from '@/components/Login';
import CustomCursor from '@/components/CustomCursor';

const pageVariants = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -16 },
};

const TABS = [
  { id: 'tutor',       label: '🤖 AI Tutor' },
  { id: 'study-buddy', label: '🎯 Study Buddy' },
  { id: 'interview',   label: '💼 Interview Prep' },
  { id: 'summarizer',  label: '📄 Summarizer' },
  { id: 'translate',   label: '🌍 Translate' },
  { id: 'quiz',        label: '📝 Quiz' },
  { id: 'flashcards',  label: '🎴 Flashcards' },
  { id: 'code',        label: '🔍 Code Analysis' },
  { id: 'playground',  label: '💻 Playground' },
  { id: 'multimodal',  label: '🖼️ Multimodal' },
  { id: 'collaborative', label: '👥 Collaborate' },
  { id: 'gamification', label: '🎮 Gamification' },
  { id: 'timer',       label: '⏱️ Timer' },
  { id: 'progress',    label: '📊 Progress' },
  { id: 'notes',       label: '📓 Notes' },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState('tutor');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authToken, setAuthToken] = useState('');
  const [username, setUsername] = useState('');

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const hash = window.location.hash;
    if (hash) {
      const params = new URLSearchParams(hash.substring(1));
      const idToken = params.get('id_token');
      if (idToken) {
        localStorage.setItem('authToken', idToken);
        try {
          const payload = JSON.parse(atob(idToken.split('.')[1]));
          const name = (payload.email || payload['cognito:username'] || 'User').split('@')[0];
          localStorage.setItem('username', name);
          setUsername(name);
        } catch { localStorage.setItem('username', 'User'); setUsername('User'); }
        setAuthToken(idToken); setIsAuthenticated(true);
        window.history.replaceState(null, '', window.location.pathname);
        return;
      }
    }
    const t = localStorage.getItem('authToken');
    const u = localStorage.getItem('username');
    if (t) { setAuthToken(t); setIsAuthenticated(true); if (u) setUsername(u); }
  }, []);

  const handleLogin = (token: string) => {
    setAuthToken(token); setIsAuthenticated(true);
    const u = localStorage.getItem('username');
    if (u) setUsername(u);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken'); localStorage.removeItem('username');
    setAuthToken(''); setIsAuthenticated(false); setUsername('');
  };

  if (!isAuthenticated) return <Login onLogin={handleLogin} />;

  return (
    <div className="App">
      <CustomCursor />
      <div className="scan-line" aria-hidden="true" />

      <motion.header className="App-header"
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}>
        <motion.h1
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}>
          🎓 AI Learning Assistant
        </motion.h1>
        <motion.div className="header-user-cluster"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
          {username && <span className="header-username">👋 <strong>{username}</strong></span>}
          <motion.button className="btn-logout" onClick={handleLogout}
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            🚪 Logout
          </motion.button>
        </motion.div>
      </motion.header>

      <nav className="nav-tabs" aria-label="App sections">
        {TABS.map((tab, i) => (
          <motion.button key={tab.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.04, duration: 0.4 }}
            whileHover={{ scale: 1.06, y: -2 }}
            whileTap={{ scale: 0.94 }}
            className={activeTab === tab.id ? 'active' : ''}
            onClick={() => setActiveTab(tab.id)}
            aria-current={activeTab === tab.id ? 'page' : undefined}>
            {tab.label}
          </motion.button>
        ))}
      </nav>

      <main className="main-content">
        <AnimatePresence mode="wait">
          <motion.div key={activeTab}
            variants={pageVariants} initial="initial" animate="animate" exit="exit"
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}>
            {activeTab === 'tutor'         && <AITutorChat authToken={authToken} />}
            {activeTab === 'study-buddy'   && <AIStudyBuddy authToken={authToken} />}
            {activeTab === 'interview'     && <InterviewPrep authToken={authToken} />}
            {activeTab === 'summarizer'    && <ContentSummarizer authToken={authToken} />}
            {activeTab === 'translate'     && <TranslationTool authToken={authToken} />}
            {activeTab === 'quiz'          && <QuizGenerator authToken={authToken} />}
            {activeTab === 'flashcards'    && <FlashcardGenerator authToken={authToken} />}
            {activeTab === 'code'          && <CodeAnalyzer authToken={authToken} />}
            {activeTab === 'playground'    && <CodePlayground authToken={authToken} />}
            {activeTab === 'multimodal'    && <MultimodalProcessor authToken={authToken} />}
            {activeTab === 'collaborative' && <CollaborativeLearning authToken={authToken} />}
            {activeTab === 'gamification'  && <GamificationDashboard authToken={authToken} />}
            {activeTab === 'timer'         && <StudyTimer authToken={authToken} />}
            {activeTab === 'progress'      && <ProgressTracker authToken={authToken} />}
            {activeTab === 'notes'         && <NoteTaker />}
          </motion.div>
        </AnimatePresence>
      </main>

      <motion.footer className="App-footer"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }}>
        <p>AI for Learning &amp; Developer Productivity · AWS AI Bharat Hackathon 2026 · Powered by Amazon Bedrock Nova Pro</p>
      </motion.footer>
    </div>
  );
}
