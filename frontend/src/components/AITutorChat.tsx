import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  followUpQuestions?: string[];
}

interface AITutorChatProps {
  authToken: string;
}

const getDemoResponse = (question: string): { answer: string; follow_up_questions: string[] } => {
  const q = question.toLowerCase();
  if (q.includes('python') || q.includes('code') || q.includes('program')) {
    return {
      answer: `Great question about programming! Here's what you should know:\n\n**Key Concepts:**\n1. Python uses indentation to define code blocks\n2. Variables are dynamically typed\n3. Functions are defined with the \`def\` keyword\n\n**Example:**\n\`\`\`python\ndef greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("World"))\n\`\`\`\n\nThis is a demo response — connect to the API for real AI-powered tutoring!`,
      follow_up_questions: [
        'What are Python data types?',
        'How do loops work in Python?',
        'What is object-oriented programming?',
      ],
    };
  }
  if (q.includes('math') || q.includes('calculus') || q.includes('algebra')) {
    return {
      answer: `Let me help you with mathematics!\n\n**Approach:**\n1. Identify what type of problem this is\n2. Recall the relevant formulas\n3. Work step by step\n\nMathematics is all about practice and understanding the fundamentals. This is a demo response — connect to the API for full AI tutoring.`,
      follow_up_questions: [
        'Can you explain derivatives?',
        'What is the quadratic formula?',
        'How do matrices work?',
      ],
    };
  }
  return {
    answer: `That's an interesting topic! Here's a structured way to think about it:\n\n1. **Break it down** into smaller concepts\n2. **Find connections** to things you already know\n3. **Practice** with examples\n4. **Test yourself** with quizzes\n\nThis is a demo response. Connect the API backend for real AI-powered answers!`,
    follow_up_questions: [
      'Can you explain this in simpler terms?',
      'What are some practical examples?',
      'How does this relate to other topics?',
    ],
  };
};

const AITutorChat: React.FC<AITutorChatProps> = ({ authToken }) => {
  const apiUrl = process.env.REACT_APP_API_URL || '';
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [subject, setSubject] = useState('');
  const [teachingStyle, setTeachingStyle] = useState('socratic');
  const [isDemo, setIsDemo] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const startSession = async () => {
    setLoading(true);
    // If no API URL, go straight to demo mode
    if (!apiUrl) {
      setSessionId('demo_' + Date.now());
      setIsDemo(true);
      setMessages([{
        role: 'assistant',
        content: `Hello! I'm your AI tutor (demo mode). I'm here to help you learn${subject ? ` about ${subject}` : ''}. Ask me anything and I'll do my best to help!`,
        timestamp: new Date().toISOString(),
      }]);
      setLoading(false);
      return;
    }
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

      const data = await response.json();
      setSessionId(data.session_id);
      
      setMessages([{
        role: 'assistant',
        content: `Hello! I'm your AI tutor. I'm here to help you learn${subject ? ` about ${subject}` : ''}. What would you like to explore today?`,
        timestamp: new Date().toISOString(),
      }]);
    } catch (error) {
      console.error('Error starting session, falling back to demo:', error);
      setSessionId('demo_' + Date.now());
      setIsDemo(true);
      setMessages([{
        role: 'assistant',
        content: `Hello! I'm your AI tutor (demo mode — API unavailable). Ask me anything!`,
        timestamp: new Date().toISOString(),
      }]);
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

    // Demo mode — simulate a response
    if (isDemo || !apiUrl) {
      await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 700));
      const demo = getDemoResponse(question);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: demo.answer,
        timestamp: new Date().toISOString(),
        followUpQuestions: demo.follow_up_questions,
      }]);
      setLoading(false);
      return;
    }

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
        }),
      });

      const data = await response.json();
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toISOString(),
        followUpQuestions: data.follow_up_questions,
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error asking question:', error);
      const demo = getDemoResponse(question);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: demo.answer + '\n\n_(Offline mode — API unavailable)_',
        timestamp: new Date().toISOString(),
        followUpQuestions: demo.follow_up_questions,
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
      <p>Get personalized tutoring with adaptive teaching styles</p>

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
