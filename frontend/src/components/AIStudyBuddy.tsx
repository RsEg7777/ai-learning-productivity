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

interface StudyPathModule {
  id: number;
  title: string;
  description: string;
  difficulty: string;
  estimatedHours: number;
  prerequisites: number[];
  topics: string[];
  learningObjectives: string[];
  resources: Array<{type: string; title: string; description: string}>;
  assessment: string;
}

interface SmartStudyPath {
  skillGapAnalysis: {
    currentSkills: string[];
    targetSkills: string[];
    gaps: string[];
  };
  modules: StudyPathModule[];
  weeklySchedule: Array<{week: number; focus: string; modules: number[]; hoursPlanned: number; milestone: string}>;
  totalEstimatedWeeks: number;
  dailyRecommendation: string;
  motivationalTip: string;
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
  const [activeTab, setActiveTab] = useState<'chat' | 'studypath'>('chat');
  const [studyPath, setStudyPath] = useState<SmartStudyPath | null>(null);
  const [pathLoading, setPathLoading] = useState(false);
  const [pathForm, setPathForm] = useState({ topic: '', currentLevel: 'beginner', targetLevel: 'advanced', hoursPerWeek: 10, knownTopics: '' });
  const [showPathForm, setShowPathForm] = useState(false);
  const [expandedModule, setExpandedModule] = useState<number | null>(null);

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
    const currentInput = userInput;
    setUserInput('');
    setLoading(true);

    try {
      // Try API first, fallback to demo mode
      let responseData = null;
      
      if (API_URL) {
        try {
          const response = await fetch(`${API_URL}/study-buddy/chat`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
              message: currentInput,
              context: {
                learningGoals: learningGoals,
                learningStyle: learningStyle,
                currentSession: currentSession
              }
            })
          });

          if (response.ok) {
            responseData = await response.json();
          }
        } catch (apiError) {
          console.log('API unavailable, using demo mode');
        }
      }
      
      // Demo mode fallback
      if (!responseData) {
        responseData = {
          response: generateStudyBuddyResponse(currentInput, learningGoals, learningStyle),
          recommendation: `💡 Tip: Focus on ${learningStyle} learning methods for better retention!`
        };
      }

      setChatMessages([...newMessages, {
        role: 'assistant',
        content: responseData.response
      }]);

      if (responseData.recommendation) {
        setAiInsight(responseData.recommendation);
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

  const generateStudyBuddyResponse = (message: string, goals: LearningGoal[], style: string): string => {
    const lowerMsg = message.toLowerCase();
    
    if (lowerMsg.includes('help') || lowerMsg.includes('stuck')) {
      return `I'm here to help! Let's break this down together. Based on your ${style} learning style, I recommend:\n\n• Take it step by step\n• Use ${style === 'visual' ? 'diagrams and charts' : style === 'auditory' ? 'discussions and explanations' : 'hands-on practice'}\n• Review your progress regularly\n\nWhat specific area would you like to focus on?`;
    } else if (lowerMsg.includes('goal') || lowerMsg.includes('plan')) {
      return `Great thinking! Setting clear goals is key to success. ${goals.length > 0 ? `I see you have ${goals.length} goal(s) already.` : 'Let\'s create your first learning goal!'}\n\nFor effective learning:\n1. Set specific, measurable goals\n2. Break them into smaller milestones\n3. Track your progress regularly\n\nWould you like to add a new goal or work on existing ones?`;
    } else if (lowerMsg.includes('study') || lowerMsg.includes('learn')) {
      return `Excellent! Let's optimize your study approach. For ${style} learners, I recommend:\n\n• ${style === 'visual' ? 'Use mind maps, flashcards, and color coding' : style === 'auditory' ? 'Record lectures, discuss topics, use mnemonics' : 'Practice problems, build projects, hands-on exercises'}\n• Take regular breaks (Pomodoro technique)\n• Review material within 24 hours\n\nWhat topic are you studying today?`;
    } else {
      return `That's interesting! I'm ${buddyName}, your AI study companion. I'm here to help you learn effectively using your ${style} learning style.\n\nI can help you:\n• Create and track learning goals\n• Suggest study strategies\n• Generate personalized study paths\n• Keep you motivated\n\nWhat would you like to work on?`;
    }
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

  const generateSmartPath = async () => {
    if (!pathForm.topic) return;
    setPathLoading(true);
    try {
      // Try API first, fallback to demo mode
      let pathData = null;
      
      if (API_URL) {
        try {
          const response = await fetch(`${API_URL}/study-buddy/generate-smart-path`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
              topic: pathForm.topic,
              currentLevel: pathForm.currentLevel,
              targetLevel: pathForm.targetLevel,
              availableHoursPerWeek: pathForm.hoursPerWeek,
              learningStyle: learningStyle,
              knownTopics: pathForm.knownTopics ? pathForm.knownTopics.split(',').map((t: string) => t.trim()).filter(Boolean) : []
            })
          });
          if (response.ok) {
            pathData = await response.json();
          }
        } catch (apiError) {
          console.log('API unavailable, using demo study path');
        }
      }
      
      // Demo mode fallback
      if (!pathData) {
        pathData = {
          studyPath: generateDemoStudyPath(pathForm.topic, pathForm.currentLevel, pathForm.targetLevel, pathForm.hoursPerWeek)
        };
      }
      
      setStudyPath(pathData.studyPath);
      setShowPathForm(false);
    } catch (error) {
      console.error('Error generating study path:', error);
    }
    setPathLoading(false);
  };

  const generateDemoStudyPath = (topic: string, currentLevel: string, targetLevel: string, hoursPerWeek: number): SmartStudyPath => {
    const weeks = Math.ceil(12 * (targetLevel === 'advanced' ? 1.5 : 1));
    return {
      skillGapAnalysis: {
        currentSkills: [`Basic ${topic} knowledge`, 'Fundamental concepts'],
        targetSkills: [`Advanced ${topic} mastery`, 'Real-world application', 'Best practices'],
        gaps: ['Intermediate concepts', 'Practical experience', 'Advanced techniques']
      },
      modules: [
        {
          id: 1,
          title: `Introduction to ${topic}`,
          description: `Learn the fundamentals of ${topic} and build a strong foundation`,
          difficulty: 'beginner',
          estimatedHours: 10,
          prerequisites: [],
          topics: ['Basics', 'Core concepts', 'Getting started'],
          learningObjectives: [`Understand ${topic} fundamentals`, 'Set up development environment', 'Write first programs'],
          resources: [
            { type: 'video', title: 'Introduction Course', description: 'Comprehensive video tutorial' },
            { type: 'article', title: 'Getting Started Guide', description: 'Step-by-step written guide' }
          ],
          assessment: 'Quiz and hands-on project'
        },
        {
          id: 2,
          title: `Intermediate ${topic}`,
          description: `Dive deeper into ${topic} concepts and patterns`,
          difficulty: 'intermediate',
          estimatedHours: 15,
          prerequisites: [1],
          topics: ['Advanced concepts', 'Design patterns', 'Best practices'],
          learningObjectives: ['Master intermediate concepts', 'Apply design patterns', 'Build complex projects'],
          resources: [
            { type: 'video', title: 'Advanced Techniques', description: 'In-depth video series' },
            { type: 'project', title: 'Real-world Project', description: 'Build a complete application' }
          ],
          assessment: 'Capstone project'
        },
        {
          id: 3,
          title: `Advanced ${topic} & Real-world Applications`,
          description: `Master advanced techniques and build production-ready applications`,
          difficulty: 'advanced',
          estimatedHours: 20,
          prerequisites: [1, 2],
          topics: ['Performance optimization', 'Architecture', 'Production deployment'],
          learningObjectives: ['Optimize for production', 'Design scalable systems', 'Deploy applications'],
          resources: [
            { type: 'video', title: 'Expert Masterclass', description: 'Advanced techniques from experts' },
            { type: 'project', title: 'Portfolio Project', description: 'Build a showcase project' }
          ],
          assessment: 'Final portfolio project'
        }
      ],
      weeklySchedule: [
        { week: 1, focus: 'Fundamentals', modules: [1], hoursPlanned: hoursPerWeek, milestone: 'Complete basics' },
        { week: 2, focus: 'Core Concepts', modules: [1], hoursPlanned: hoursPerWeek, milestone: 'First project' },
        { week: 3, focus: 'Intermediate Topics', modules: [2], hoursPlanned: hoursPerWeek, milestone: 'Advanced concepts' },
        { week: 4, focus: 'Advanced Techniques', modules: [2, 3], hoursPlanned: hoursPerWeek, milestone: 'Capstone project' }
      ],
      totalEstimatedWeeks: weeks,
      dailyRecommendation: `Study for ${Math.floor(hoursPerWeek / 5)} hours daily, focusing on ${learningStyle} learning methods`,
      motivationalTip: `You're on track to master ${topic}! Stay consistent and practice daily.`
    };
  };

  const getDifficultyColor = (diff: string) => {
    switch (diff?.toLowerCase()) {
      case 'beginner': return '#10b981';
      case 'intermediate': return '#f59e0b';
      case 'advanced': return '#ef4444';
      default: return '#6366f1';
    }
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

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '2px solid var(--border)', paddingBottom: '0.5rem' }}>
          {[
            { id: 'chat' as const, icon: '💬', label: 'Chat & Goals' },
            { id: 'studypath' as const, icon: '🗺️', label: 'Smart Study Path' }
          ].map(tab => (
            <motion.button
              key={tab.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: activeTab === tab.id
                  ? 'linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%)'
                  : 'transparent',
                border: activeTab === tab.id ? 'none' : '1px solid var(--border)',
                color: activeTab === tab.id ? 'white' : 'var(--text-secondary)',
                padding: '0.75rem 1.5rem',
                borderRadius: '10px 10px 0 0',
                cursor: 'pointer',
                fontSize: '1rem',
                fontWeight: '600',
                flex: 1
              }}
            >
              {tab.icon} {tab.label}
            </motion.button>
          ))}
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

        {activeTab === 'chat' && (<>
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
        </>)}

        {activeTab === 'studypath' && (
          <div>
            {/* Study Path Generator Form */}
            {!studyPath && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: '12px',
                  padding: '2rem'
                }}
              >
                <h3 style={{ color: 'var(--primary-light)', margin: '0 0 0.5rem 0', fontSize: '1.3rem' }}>
                  🗺️ AI Smart Study Path Generator
                </h3>
                <p style={{ color: 'var(--text-secondary)', margin: '0 0 1.5rem 0', fontSize: '0.9rem' }}>
                  Get a personalized learning roadmap with skill gap analysis, modules, and weekly schedule — powered by Amazon Nova Pro AI.
                </p>

                <div style={{ display: 'grid', gap: '1rem' }}>
                  <input
                    type="text"
                    placeholder="What do you want to learn? (e.g., Machine Learning, React, Data Structures)"
                    value={pathForm.topic}
                    onChange={(e) => setPathForm({ ...pathForm, topic: e.target.value })}
                    style={{ width: '100%', background: 'var(--bg-dark)', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '0.75rem', borderRadius: '8px', fontSize: '1rem' }}
                  />

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                      <label style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', display: 'block', marginBottom: '0.5rem' }}>Current Level</label>
                      <select
                        value={pathForm.currentLevel}
                        onChange={(e) => setPathForm({ ...pathForm, currentLevel: e.target.value })}
                        style={{ width: '100%', background: 'var(--bg-dark)', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '0.75rem', borderRadius: '8px', fontSize: '1rem' }}
                      >
                        <option value="beginner">Beginner</option>
                        <option value="intermediate">Intermediate</option>
                        <option value="advanced">Advanced</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', display: 'block', marginBottom: '0.5rem' }}>Target Level</label>
                      <select
                        value={pathForm.targetLevel}
                        onChange={(e) => setPathForm({ ...pathForm, targetLevel: e.target.value })}
                        style={{ width: '100%', background: 'var(--bg-dark)', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '0.75rem', borderRadius: '8px', fontSize: '1rem' }}
                      >
                        <option value="intermediate">Intermediate</option>
                        <option value="advanced">Advanced</option>
                        <option value="expert">Expert</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', display: 'block', marginBottom: '0.5rem' }}>Hours Available Per Week</label>
                    <input
                      type="number"
                      min={1}
                      max={40}
                      value={pathForm.hoursPerWeek}
                      onChange={(e) => setPathForm({ ...pathForm, hoursPerWeek: parseInt(e.target.value) || 10 })}
                      style={{ width: '100%', background: 'var(--bg-dark)', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '0.75rem', borderRadius: '8px', fontSize: '1rem' }}
                    />
                  </div>

                  <div>
                    <label style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', display: 'block', marginBottom: '0.5rem' }}>Topics You Already Know (comma-separated, optional)</label>
                    <input
                      type="text"
                      placeholder="e.g., Python basics, HTML, CSS"
                      value={pathForm.knownTopics}
                      onChange={(e) => setPathForm({ ...pathForm, knownTopics: e.target.value })}
                      style={{ width: '100%', background: 'var(--bg-dark)', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '0.75rem', borderRadius: '8px', fontSize: '1rem' }}
                    />
                  </div>

                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={generateSmartPath}
                    disabled={pathLoading || !pathForm.topic}
                    style={{
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      border: 'none',
                      color: 'white',
                      padding: '1rem',
                      borderRadius: '10px',
                      cursor: pathLoading || !pathForm.topic ? 'not-allowed' : 'pointer',
                      fontSize: '1.1rem',
                      fontWeight: '700',
                      opacity: pathLoading || !pathForm.topic ? 0.6 : 1
                    }}
                  >
                    {pathLoading ? '🧠 AI is generating your personalized study path...' : '🚀 Generate My Smart Study Path'}
                  </motion.button>
                </div>
              </motion.div>
            )}

            {/* Study Path Results */}
            {studyPath && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                  <h3 style={{ color: 'var(--primary-light)', margin: 0, fontSize: '1.3rem' }}>
                    🗺️ Your Personalized Study Path
                  </h3>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => { setStudyPath(null); setShowPathForm(true); }}
                    style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '0.5rem 1rem', borderRadius: '8px', cursor: 'pointer', fontSize: '0.85rem' }}
                  >
                    🔄 Generate New Path
                  </motion.button>
                </div>

                {/* Skill Gap Analysis */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.5rem', marginBottom: '1.5rem' }}>
                  <h4 style={{ color: '#f59e0b', margin: '0 0 1rem 0' }}>🔍 Skill Gap Analysis</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
                    <div>
                      <p style={{ color: '#10b981', fontWeight: 600, margin: '0 0 0.5rem 0', fontSize: '0.85rem' }}>✅ Current Skills</p>
                      {studyPath.skillGapAnalysis?.currentSkills?.map((skill, i) => (
                        <div key={i} style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', padding: '0.25rem 0' }}>• {skill}</div>
                      ))}
                    </div>
                    <div>
                      <p style={{ color: '#6366f1', fontWeight: 600, margin: '0 0 0.5rem 0', fontSize: '0.85rem' }}>🎯 Target Skills</p>
                      {studyPath.skillGapAnalysis?.targetSkills?.map((skill, i) => (
                        <div key={i} style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', padding: '0.25rem 0' }}>• {skill}</div>
                      ))}
                    </div>
                    <div>
                      <p style={{ color: '#ef4444', fontWeight: 600, margin: '0 0 0.5rem 0', fontSize: '0.85rem' }}>⚠️ Gaps to Fill</p>
                      {studyPath.skillGapAnalysis?.gaps?.map((gap, i) => (
                        <div key={i} style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', padding: '0.25rem 0' }}>• {gap}</div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Visual Module Path */}
                <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.5rem', marginBottom: '1.5rem' }}>
                  <h4 style={{ color: 'var(--primary-light)', margin: '0 0 1rem 0' }}>📚 Learning Modules ({studyPath.modules?.length || 0} modules • ~{studyPath.totalEstimatedWeeks} weeks)</h4>
                  <div style={{ position: 'relative' }}>
                    {/* Vertical connecting line */}
                    <div style={{ position: 'absolute', left: '20px', top: '20px', bottom: '20px', width: '3px', background: 'linear-gradient(180deg, #10b981, #6366f1, #ef4444)', borderRadius: '2px' }} />
                    
                    {studyPath.modules?.map((mod, index) => (
                      <motion.div
                        key={mod.id || index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', position: 'relative', paddingLeft: '50px' }}
                      >
                        {/* Module number circle */}
                        <div style={{
                          position: 'absolute',
                          left: '8px',
                          top: '50%',
                          transform: 'translateY(-50%)',
                          width: '28px',
                          height: '28px',
                          borderRadius: '50%',
                          background: getDifficultyColor(mod.difficulty),
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontWeight: '700',
                          fontSize: '0.8rem',
                          zIndex: 1
                        }}>
                          {index + 1}
                        </div>

                        <div
                          onClick={() => setExpandedModule(expandedModule === index ? null : index)}
                          style={{
                            flex: 1,
                            background: expandedModule === index ? 'rgba(99, 102, 241, 0.1)' : 'var(--bg-dark)',
                            border: `1px solid ${expandedModule === index ? 'var(--primary)' : 'var(--border)'}`,
                            borderRadius: '10px',
                            padding: '1rem',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ flex: 1 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{mod.title}</span>
                                <span style={{ background: getDifficultyColor(mod.difficulty), color: 'white', padding: '0.1rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600 }}>
                                  {mod.difficulty}
                                </span>
                              </div>
                              <p style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '0.85rem' }}>{mod.description}</p>
                            </div>
                            <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem', whiteSpace: 'nowrap', marginLeft: '1rem' }}>
                              ⏱ {mod.estimatedHours}h
                            </span>
                          </div>

                          {/* Expanded details */}
                          {expandedModule === index && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              style={{ marginTop: '1rem', borderTop: '1px solid var(--border)', paddingTop: '1rem' }}
                            >
                              {mod.learningObjectives?.length > 0 && (
                                <div style={{ marginBottom: '0.75rem' }}>
                                  <p style={{ color: '#10b981', fontWeight: 600, margin: '0 0 0.25rem 0', fontSize: '0.85rem' }}>🎯 Learning Objectives:</p>
                                  {mod.learningObjectives.map((obj, i) => (
                                    <div key={i} style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', padding: '0.15rem 0' }}>• {obj}</div>
                                  ))}
                                </div>
                              )}
                              {mod.topics?.length > 0 && (
                                <div style={{ marginBottom: '0.75rem' }}>
                                  <p style={{ color: '#6366f1', fontWeight: 600, margin: '0 0 0.25rem 0', fontSize: '0.85rem' }}>📝 Topics:</p>
                                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    {mod.topics.map((topic, i) => (
                                      <span key={i} style={{ background: 'rgba(99, 102, 241, 0.15)', color: 'var(--primary)', padding: '0.2rem 0.6rem', borderRadius: '6px', fontSize: '0.8rem' }}>{topic}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              {mod.resources?.length > 0 && (
                                <div style={{ marginBottom: '0.75rem' }}>
                                  <p style={{ color: '#f59e0b', fontWeight: 600, margin: '0 0 0.25rem 0', fontSize: '0.85rem' }}>📚 Resources:</p>
                                  {mod.resources.map((res, i) => (
                                    <div key={i} style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', padding: '0.15rem 0' }}>
                                      [{res.type}] <strong>{res.title}</strong> — {res.description}
                                    </div>
                                  ))}
                                </div>
                              )}
                              {mod.assessment && (
                                <div>
                                  <p style={{ color: '#ef4444', fontWeight: 600, margin: '0 0 0.25rem 0', fontSize: '0.85rem' }}>🏆 Assessment:</p>
                                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', margin: 0 }}>{mod.assessment}</p>
                                </div>
                              )}
                            </motion.div>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* Weekly Schedule */}
                {studyPath.weeklySchedule && studyPath.weeklySchedule.length > 0 && (
                  <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '1.5rem', marginBottom: '1.5rem' }}>
                    <h4 style={{ color: 'var(--primary-light)', margin: '0 0 1rem 0' }}>📅 Weekly Schedule</h4>
                    <div style={{ display: 'grid', gap: '0.75rem' }}>
                      {studyPath.weeklySchedule.map((week, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem', background: 'var(--bg-dark)', borderRadius: '8px' }}>
                          <div style={{ minWidth: '65px', fontWeight: 700, color: 'var(--primary)', fontSize: '0.9rem' }}>Week {week.week}</div>
                          <div style={{ flex: 1 }}>
                            <div style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.9rem' }}>{week.focus}</div>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{week.milestone}</div>
                          </div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', whiteSpace: 'nowrap' }}>{week.hoursPlanned}h</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Daily Recommendation & Motivation */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  {studyPath.dailyRecommendation && (
                    <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10b981', borderRadius: '12px', padding: '1.25rem' }}>
                      <p style={{ color: '#10b981', fontWeight: 600, margin: '0 0 0.5rem 0' }}>📆 Daily Routine</p>
                      <p style={{ color: 'var(--text-primary)', margin: 0, fontSize: '0.9rem', lineHeight: 1.6 }}>{studyPath.dailyRecommendation}</p>
                    </div>
                  )}
                  {studyPath.motivationalTip && (
                    <div style={{ background: 'rgba(139, 92, 246, 0.1)', border: '1px solid var(--secondary)', borderRadius: '12px', padding: '1.25rem' }}>
                      <p style={{ color: 'var(--secondary)', fontWeight: 600, margin: '0 0 0.5rem 0' }}>💪 Motivation</p>
                      <p style={{ color: 'var(--text-primary)', margin: 0, fontSize: '0.9rem', lineHeight: 1.6 }}>{studyPath.motivationalTip}</p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default AIStudyBuddy;
