import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import VoiceInput from './VoiceInput';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  followUpQuestions?: string[];
}

interface AITutorChatProps {
  authToken: string;
}

const AITutorChat: React.FC<AITutorChatProps> = ({ authToken }) => {
  const apiUrl = process.env.REACT_APP_API_URL || '';
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [subject, setSubject] = useState('');
  const [teachingStyle, setTeachingStyle] = useState('socratic');
  const [language, setLanguage] = useState('english');
  const [error, setError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleVoiceTranscript = useCallback((text: string) => {
    setInputText(prev => {
      const needsSpace = prev.length > 0 && !prev.endsWith(' ');
      return prev + (needsSpace ? ' ' : '') + text;
    });
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const startSession = async () => {
    if (!apiUrl) {
      setError('API URL not configured. Please set REACT_APP_API_URL environment variable.');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${apiUrl}/tutor/start-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          user_id: 'user123',
          subject: subject || undefined,
          teaching_style: teachingStyle,
          difficulty_level: 'adaptive',
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to start session: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success && data.session_id) {
        setSessionId(data.session_id);
        
        setMessages([{
          role: 'assistant',
          content: `Hello! I'm your AI tutor powered by advanced AI. I'm here to help you learn${subject ? ` about ${subject}` : ''}. I'll use a ${teachingStyle} teaching approach to help you understand concepts deeply.\n\nWhat would you like to explore today?`,
          timestamp: new Date().toISOString(),
        }]);
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Error starting session:', error);
      setError('Failed to start tutoring session. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const askQuestion = async (question: string) => {
    if (!sessionId || !question.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${apiUrl}/tutor/ask-question`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          session_id: sessionId,
          question: question,
          include_examples: true,
          use_socratic_method: teachingStyle === 'socratic',
          language: language,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to get response: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success && data.answer) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.answer,
          timestamp: new Date().toISOString(),
          followUpQuestions: data.follow_up_questions || [],
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error('Invalid response from AI tutor');
      }
    } catch (error) {
      console.error('Error asking question:', error);
      setError('Failed to get AI response. Please try again.');
      
      // Add error message to chat
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '❌ Sorry, I encountered an error processing your question. Please try again or rephrase your question.',
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!sessionId) {
      startSession();
    } else {
      askQuestion(inputText);
    }
  };

  return (
    <div className="component-container" style={{ maxWidth: '900px', margin: '0 auto' }}>
      <h2>🤖 AI Tutor Chat</h2>
      <p>Get personalized tutoring with adaptive teaching styles powered by advanced AI</p>

      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid #ef4444',
          borderRadius: '8px',
          padding: '1rem',
          marginBottom: '1rem',
          color: '#ef4444'
        }}>
          ⚠️ {error}
        </div>
      )}

      {!sessionId && (
        <div style={{ marginBottom: '2rem' }}>
          <div className="form-group">
            <label>Subject (optional):</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g., Python, Mathematics, Physics"
            />
          </div>
          <div className="form-group">
            <label>Teaching Style:</label>
            <select
              value={teachingStyle}
              onChange={(e) => setTeachingStyle(e.target.value)}
            >
              <option value="socratic">Socratic (Guiding Questions)</option>
              <option value="direct">Direct (Clear Explanations)</option>
              <option value="exploratory">Exploratory (Discovery-Based)</option>
            </select>
          </div>
          <div className="form-group">
            <label>🌍 Response Language (Bharat Languages):</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="english">English</option>
              <option value="hindi">हिन्दी (Hindi)</option>
              <option value="hinglish">Hinglish (Hindi + English)</option>
              <option value="tamil">தமிழ் (Tamil)</option>
              <option value="tanglish">Tanglish (Tamil + English)</option>
              <option value="telugu">తెలుగు (Telugu)</option>
              <option value="bengali">বাংলা (Bengali)</option>
              <option value="marathi">मराठी (Marathi)</option>
              <option value="gujarati">ગુજરાતી (Gujarati)</option>
              <option value="kannada">ಕನ್ನಡ (Kannada)</option>
              <option value="malayalam">മലയാളം (Malayalam)</option>
              <option value="punjabi">ਪੰਜਾਬੀ (Punjabi)</option>
              <option value="odia">ଓଡ଼ିଆ (Odia)</option>
              <option value="urdu">اردو (Urdu)</option>
              <option value="assamese">অসমীয়া (Assamese)</option>
            </select>
          </div>
        </div>
      )}

      <div style={{
        background: 'var(--bg-dark)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        height: '500px',
        overflowY: 'auto',
        padding: '1.5rem',
        marginBottom: '1rem',
      }}>
        <AnimatePresence>
          {messages.map((msg, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                marginBottom: '1rem',
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <div style={{
                maxWidth: '75%',
                padding: '1rem 1.25rem',
                borderRadius: '12px',
                background: msg.role === 'user' 
                  ? 'linear-gradient(135deg, var(--primary), var(--primary-dark))' 
                  : 'var(--bg-card)',
                border: msg.role === 'user' ? 'none' : '1px solid var(--border)',
                color: 'var(--text-primary)',
              }}>
                <div style={{ marginBottom: msg.followUpQuestions ? '0.75rem' : '0' }}>
                  {msg.content}
                </div>
                {msg.followUpQuestions && msg.followUpQuestions.length > 0 && (
                  <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border)' }}>
                    <div style={{ color: 'var(--primary-light)', fontSize: '0.85rem', marginBottom: '0.5rem', fontWeight: 600 }}>
                      💡 Think about:
                    </div>
                    {msg.followUpQuestions.map((q, i) => (
                      <div
                        key={i}
                        onClick={() => askQuestion(q)}
                        style={{
                          color: 'var(--text-secondary)',
                          fontSize: '0.85rem',
                          cursor: 'pointer',
                          padding: '0.5rem 0.75rem',
                          marginTop: '0.4rem',
                          background: 'var(--bg-dark)',
                          borderRadius: '8px',
                          border: '1px solid var(--border)',
                          transition: 'all 0.3s',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.borderColor = 'var(--primary)';
                          e.currentTarget.style.color = 'var(--primary-light)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.borderColor = 'var(--border)';
                          e.currentTarget.style.color = 'var(--text-secondary)';
                        }}
                      >
                        {q}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {loading && (
          <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
            <div className="loading" style={{ padding: '1rem' }}>
              <p>Thinking...</p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.75rem' }}>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={sessionId ? "Ask a question..." : "Start learning..."}
          disabled={loading}
          style={{
            flex: 1,
            padding: '0.875rem 1rem',
            background: 'var(--bg-dark)',
            border: '1px solid var(--border)',
            borderRadius: '10px',
            color: 'var(--text-primary)',
            fontSize: '0.95rem',
          }}
        />
        <VoiceInput
          onTranscript={handleVoiceTranscript}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || (!sessionId && !inputText.trim())}
          className="btn-primary"
          style={{ width: 'auto', padding: '0.875rem 2rem' }}
        >
          {sessionId ? 'Send' : 'Start'}
        </button>
      </form>
    </div>
  );
};

export default AITutorChat;
