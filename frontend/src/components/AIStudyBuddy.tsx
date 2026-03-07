import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface AIStudyBuddyProps {
  authToken: string;
}

interface LearningGoal {
  id: string;
  title: string;
  description: string;
  targetDate: string;
  progress: number;
  milestones: Milestone[];
}

interface Milestone {
  id: string;
  title: string;
  completed: boolean;
  aiRecommendation: string;
}

interface StudySession {
  topic: string;
  duration: number;
  difficulty: string;
  focusAreas: string[];
}

const AIStudyBuddy: React.FC<AIStudyBuddyProps> = ({ authToken }) => {
  const [buddyName, setBuddyName] = useState('Nova');
  const [learningGoals, setLearningGoals] = useState<LearningGoal[]>([]);
  const [currentSession, setCurrentSession] = useState<StudySession | null>(null);
  const [chatMessages, setChatMessages] = useState<Array<{role: string, content: string}>>([]);
  const [userInput, setUserInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showGoalForm, setShowGoalForm] = useState(false);
  const [newGoal, setNewGoal] = useState({ title: '', description: '', targetDate: '' });
  const [learningStyle, setLearningStyle] = useState<'visual' | 'auditory' | 'kinesthetic' | 'reading'>('visual');
  const [aiInsight, setAiInsight] = useState('');

  const API_URL = process.env.REACT_APP_API_URL || '';

  useEffect(() => {
    // Initial greeting from AI buddy
    setChatMessages([{
      role: 'assistant',
      content: `Hi! I'm ${buddyName}, your AI Study Buddy! 🤖✨\n\nI'm here to help you achieve your learning goals with personalized study plans, adaptive recommendations, and real-time support.\n\nWhat would you like to learn today?`
    }]);
    loadLearningGoals();
  }, []);

  const loadLearningGoals = async () => {
    try {
      const response = await fetch(`${API_URL}/study-buddy/goals`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (response.ok) {
        const data = await response.json();
        setLearningGoals(data.goals || []);
      }
    } catch (error) {
      console.error('Error loading goals:', error);
    }
  };

  const createLearningGoal = async () => {
    if (!newGoal.title || !newGoal.targetDate) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/study-buddy/create-goal`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          title: newGoal.title,
          description: newGoal.description,
          targetDate: newGoal.targetDate,
          learningStyle: learningStyle
        })
      });

      if (response.ok) {
        const data = await response.json();
        setLearningGoals([...learningGoals, data.goal]);
        setShowGoalForm(false);
        setNewGoal({ title: '', description: '', targetDate: '' });
        
        setChatMessages([...chatMessages, {
          role: 'assistant',
          content: `🎯 Great! I've created a personalized learning path for "${newGoal.title}"!\n\n${data.aiRecommendation}\n\nLet's break this down into manageable milestones. Ready to start?`
        }]);
      }
    } catch (error) {
      console.error('Error creating goal:', error);
    }
    setLoading(false);
  };

  const sendMessage = async () => {
    if (!userInput.trim()) return;

    const newMessages = [...chatMessages, { role: 'user', content: userInput }];
    setChatMessages(newMessages);
    setUserInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/study-buddy/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          message: userInput,
          context: {
            learningGoals: learningGoals,
            learningStyle: learningStyle,
            currentSession: currentSession
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        setChatMessages([...newMessages, {
          role: 'assistant',
          content: data.response
        }]);

        if (data.recommendation) {
          setAiInsight(data.recommendation);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setChatMessages([...newMessages, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }]);
    }
    setLoading(false);
  };

  const startAdaptiveSession = async (goalId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/study-buddy/start-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          goalId: goalId,
          learningStyle: learningStyle
        })
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentSession(data.session);
        
        setChatMessages([...chatMessages, {
          role: 'assistant',
          content: `🚀 Let's start your ${data.session.duration}-minute study session on "${data.session.topic}"!\n\n${data.aiGuidance}\n\nI'll adapt the difficulty based on your performance. Ready?`
        }]);
      }
    } catch (error) {
      console.error('Error starting session:', error);
    }
    setLoading(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ width: '100%', maxWidth: '1400px', margin: '0 auto' }}
    >
      <div style={{
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
        border: '1px solid var(--border)',
        borderRadius: '20px',
        padding: '2rem',
        marginBottom: '2rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{
            width: '60px',
            height: '60px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '2rem',
            boxShadow: '0 0 30px rgba(99, 102, 241, 0.5)'
          }}>
            🤖
          </div>
          <div>
            <h2 style={{ color: 'var(--primary-light)', margin: 0, fontSize: '2rem' }}>
              AI Study Buddy - {buddyName}
            </h2>
            <p style={{ color: 'var(--text-secondary)', margin: '0.25rem 0 0 0' }}>
              Your personalized AI learning companion with adaptive intelligence
            </p>
          </div>
        </div>

        {/* Learning Style Selector */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ color: 'var(--text-primary)', fontWeight: 600, marginBottom: '0.5rem', display: 'block' }}>
            🎨 Your Learning Style:
          </label>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            {[
              { id: 'visual', icon: '👁️', label: 'Visual' },
              { id: 'auditory', icon: '👂', label: 'Auditory' },
              { id: 'kinesthetic', icon: '✋', label: 'Kinesthetic' },
              { id: 'reading', icon: '📖', label: 'Reading/Writing' }
            ].map(style => (
              <motion.button
                key={style.id}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setLearningStyle(style.id as any)}
                style={{
                  background: learningStyle === style.id
                    ? 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)'
                    : 'var(--bg-card)',
                  border: `1px solid ${learningStyle === style.id ? 'var(--primary)' : 'var(--border)'}`,
                  color: learningStyle === style.id ? 'white' : 'var(--text-primary)',
                  padding: '0.6rem 1.2rem',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: '600'
                }}
              >
                {style.icon} {style.label}
              </motion.button>
            ))}
          </div>
        </div>

        {/* AI Insight Banner */}
        <AnimatePresence>
          {aiInsight && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              style={{
                background: 'rgba(139, 92, 246, 0.15)',
                border: '1px solid var(--secondary)',
                borderRadius: '12px',
                padding: '1rem',
                marginBottom: '1.5rem'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'start', gap: '0.75rem' }}>
                <span style={{ fontSize: '1.5rem' }}>💡</span>
                <div style={{ flex: 1 }}>
                  <strong style={{ color: 'var(--secondary)' }}>AI Insight:</strong>
                  <p style={{ color: 'var(--text-primary)', margin: '0.5rem 0 0 0', lineHeight: '1.6' }}>
                    {aiInsight}
                  </p>
                </div>
                <button
                  onClick={() => setAiInsight('')}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    fontSize: '1.2rem'
                  }}
                >
                  ×
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Learning Goals */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ color: 'var(--primary-light)', margin: 0 }}>🎯 Your Learning Goals</h3>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowGoalForm(!showGoalForm)}
              style={{
                background: 'var(--primary)',
                border: 'none',
                color: 'white',
                padding: '0.6rem 1.2rem',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: '600'
              }}
            >
              + New Goal
            </motion.button>
          </div>

          {showGoalForm && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: '12px',
                padding: '1.5rem',
                marginBottom: '1rem'
              }}
            >
              <input
                type="text"
                placeholder="Goal title (e.g., Master React Hooks)"
                value={newGoal.title}
                onChange={(e) => setNewGoal({ ...newGoal, title: e.target.value })}
                style={{
                  width: '100%',
                  background: 'var(--bg-dark)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  marginBottom: '1rem',
                  fontSize: '1rem'
                }}
              />
              <textarea
                placeholder="Description (optional)"
                value={newGoal.description}
                onChange={(e) => setNewGoal({ ...newGoal, description: e.target.value })}
                rows={3}
                style={{
                  width: '100%',
                  background: 'var(--bg-dark)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  marginBottom: '1rem',
                  fontSize: '1rem',
                  resize: 'vertical'
                }}
              />
              <input
                type="date"
                value={newGoal.targetDate}
                onChange={(e) => setNewGoal({ ...newGoal, targetDate: e.target.value })}
                style={{
                  width: '100%',
                  background: 'var(--bg-dark)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  marginBottom: '1rem',
                  fontSize: '1rem'
                }}
              />
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={createLearningGoal}
                  disabled={loading}
                  style={{
                    background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)',
                    border: 'none',
                    color: 'white',
                    padding: '0.75rem 1.5rem',
                    borderRadius: '8px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    fontSize: '1rem',
                    fontWeight: '600',
                    opacity: loading ? 0.6 : 1
                  }}
                >
                  {loading ? '🤖 Creating AI Plan...' : '✨ Create with AI'}
                </motion.button>
                <button
                  onClick={() => setShowGoalForm(false)}
                  style={{
                    background: 'var(--bg-dark)',
                    border: '1px solid var(--border)',
                    color: 'var(--text-primary)',
                    padding: '0.75rem 1.5rem',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '1rem'
                  }}
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          )}

          <div style={{ display: 'grid', gap: '1rem' }}>
            {learningGoals.map((goal, index) => (
              <motion.div
                key={goal.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: '12px',
                  padding: '1.5rem'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                  <div style={{ flex: 1 }}>
                    <h4 style={{ color: 'var(--text-primary)', margin: '0 0 0.5rem 0' }}>{goal.title}</h4>
                    <p style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '0.9rem' }}>{goal.description}</p>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => startAdaptiveSession(goal.id)}
                    style={{
                      background: 'rgba(99, 102, 241, 0.2)',
                      border: '1px solid var(--primary)',
                      color: 'var(--primary)',
                      padding: '0.5rem 1rem',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                      fontWeight: '600',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    🚀 Start Session
                  </motion.button>
                </div>
                
                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Progress</span>
                    <span style={{ color: 'var(--primary)', fontSize: '0.85rem', fontWeight: '600' }}>{goal.progress}%</span>
                  </div>
                  <div style={{
                    width: '100%',
                    height: '8px',
                    background: 'var(--bg-dark)',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${goal.progress}%` }}
                      transition={{ duration: 1, ease: 'easeOut' }}
                      style={{
                        height: '100%',
                        background: 'linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%)',
                        borderRadius: '4px'
                      }}
                    />
                  </div>
                </div>

                {goal.milestones && goal.milestones.length > 0 && (
                  <div style={{ marginTop: '1rem' }}>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                      Milestones:
                    </p>
                    {goal.milestones.slice(0, 3).map(milestone => (
                      <div
                        key={milestone.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          padding: '0.5rem',
                          background: milestone.completed ? 'rgba(16, 185, 129, 0.1)' : 'var(--bg-dark)',
                          borderRadius: '6px',
                          marginBottom: '0.5rem'
                        }}
                      >
                        <span style={{ fontSize: '1.2rem' }}>
                          {milestone.completed ? '✅' : '⭕'}
                        </span>
                        <span style={{
                          color: milestone.completed ? 'var(--success)' : 'var(--text-primary)',
                          fontSize: '0.9rem',
                          flex: 1
                        }}>
                          {milestone.title}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>

        {/* Chat Interface */}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '12px',
          overflow: 'hidden'
        }}>
          <div style={{
            background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)',
            padding: '1rem',
            color: 'white',
            fontWeight: '600'
          }}>
            💬 Chat with {buddyName}
          </div>
          
          <div style={{
            height: '400px',
            overflowY: 'auto',
            padding: '1rem'
          }}>
            {chatMessages.map((msg, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  marginBottom: '1rem'
                }}
              >
                <div style={{
                  maxWidth: '70%',
                  padding: '1rem',
                  borderRadius: '12px',
                  background: msg.role === 'user'
                    ? 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)'
                    : 'var(--bg-dark)',
                  color: msg.role === 'user' ? 'white' : 'var(--text-primary)',
                  whiteSpace: 'pre-wrap',
                  lineHeight: '1.6'
                }}>
                  {msg.content}
                </div>
              </motion.div>
            ))}
            {loading && (
              <div style={{ display: 'flex', gap: '0.5rem', padding: '1rem' }}>
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ repeat: Infinity, duration: 0.6 }}
                  style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--primary)' }}
                />
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ repeat: Infinity, duration: 0.6, delay: 0.2 }}
                  style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--primary)' }}
                />
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ repeat: Infinity, duration: 0.6, delay: 0.4 }}
                  style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--primary)' }}
                />
              </div>
            )}
          </div>

          <div style={{
            padding: '1rem',
            borderTop: '1px solid var(--border)',
            display: 'flex',
            gap: '0.75rem'
          }}>
            <input
              type="text"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask me anything about your learning..."
              style={{
                flex: 1,
                background: 'var(--bg-dark)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
                padding: '0.75rem',
                borderRadius: '8px',
                fontSize: '1rem'
              }}
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={sendMessage}
              disabled={loading || !userInput.trim()}
              style={{
                background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)',
                border: 'none',
                color: 'white',
                padding: '0.75rem 1.5rem',
                borderRadius: '8px',
                cursor: loading || !userInput.trim() ? 'not-allowed' : 'pointer',
                fontSize: '1rem',
                fontWeight: '600',
                opacity: loading || !userInput.trim() ? 0.6 : 1
              }}
            >
              Send
            </motion.button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default AIStudyBuddy;
