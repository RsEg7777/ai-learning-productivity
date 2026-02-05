import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  followUpQuestions?: string[];
}

interface AITutorChatProps {
  apiUrl: string;
  token: string;
  onClose: () => void;
}

const AITutorChat: React.FC<AITutorChatProps> = ({ apiUrl, token, onClose }) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [subject, setSubject] = useState('');
  const [teachingStyle, setTeachingStyle] = useState('socratic');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const startSession = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl}/tutor/start-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_id: 'user123', // Get from auth context
          subject: subject || undefined,
          teaching_style: teachingStyle,
          difficulty_level: 'adaptive',
        }),
      });

      const data = await response.json();
      setSessionId(data.session_id);
      
      // Add welcome message
      setMessages([{
        role: 'assistant',
        content: `Hello! I'm your AI tutor. I'm here to help you learn${subject ? ` about ${subject}` : ''}. What would you like to explore today?`,
        timestamp: new Date().toISOString(),
      }]);
    } catch (error) {
      console.error('Error starting session:', error);
      alert('Failed to start tutor session');
    } finally {
      setLoading(false);
    }
  };

  const askQuestion = async (question: string) => {
    if (!sessionId || !question.trim()) return;

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setLoading(true);

    try {
      const response = await fetch(`${apiUrl}/tutor/ask-question`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          session_id: sessionId,
          question: question,
          include_examples: true,
          use_socratic_method: teachingStyle === 'socratic',
        }),
      });

      const data = await response.json();
      
      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toISOString(),
        followUpQuestions: data.follow_up_questions,
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error asking question:', error);
      alert('Failed to get response');
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
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="ai-tutor-chat"
      style={{
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '90%',
        maxWidth: '800px',
        height: '80vh',
        background: 'rgba(10, 10, 30, 0.95)',
        border: '2px solid #00ffff',
        borderRadius: '20px',
        boxShadow: '0 0 40px rgba(0, 255, 255, 0.3)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 1000,
      }}
    >
      {/* Header */}
      <div style={{
        padding: '20px',
        borderBottom: '1px solid #00ffff',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <h2 style={{ color: '#00ffff', margin: 0 }}>🤖 AI Tutor</h2>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: '1px solid #00ffff',
            color: '#00ffff',
            padding: '8px 16px',
            borderRadius: '8px',
            cursor: 'pointer',
          }}
        >
          Close
        </button>
      </div>

      {/* Setup (if no session) */}
      {!sessionId && (
        <div style={{ padding: '20px' }}>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ color: '#00ffff', display: 'block', marginBottom: '5px' }}>
              Subject (optional):
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g., Python, Mathematics, Physics"
              style={{
                width: '100%',
                padding: '10px',
                background: 'rgba(0, 255, 255, 0.1)',
                border: '1px solid #00ffff',
                borderRadius: '8px',
                color: '#fff',
              }}
            />
          </div>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ color: '#00ffff', display: 'block', marginBottom: '5px' }}>
              Teaching Style:
            </label>
            <select
              value={teachingStyle}
              onChange={(e) => setTeachingStyle(e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                background: 'rgba(0, 255, 255, 0.1)',
                border: '1px solid #00ffff',
                borderRadius: '8px',
                color: '#fff',
              }}
            >
              <option value="socratic">Socratic (Guiding Questions)</option>
              <option value="direct">Direct (Clear Explanations)</option>
              <option value="exploratory">Exploratory (Discovery-Based)</option>
            </select>
          </div>
        </div>
      )}

      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px',
      }}>
        <AnimatePresence>
          {messages.map((msg, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                marginBottom: '15px',
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <div style={{
                maxWidth: '70%',
                padding: '12px 16px',
                borderRadius: '12px',
                background: msg.role === 'user' 
                  ? 'rgba(0, 255, 255, 0.2)' 
                  : 'rgba(100, 100, 255, 0.2)',
                border: `1px solid ${msg.role === 'user' ? '#00ffff' : '#6666ff'}`,
              }}>
                <div style={{ color: '#fff', marginBottom: '5px' }}>
                  {msg.content}
                </div>
                {msg.followUpQuestions && msg.followUpQuestions.length > 0 && (
                  <div style={{ marginTop: '10px' }}>
                    <div style={{ color: '#00ffff', fontSize: '12px', marginBottom: '5px' }}>
                      💡 Think about:
                    </div>
                    {msg.followUpQuestions.map((q, i) => (
                      <div
                        key={i}
                        onClick={() => askQuestion(q)}
                        style={{
                          color: '#aaa',
                          fontSize: '12px',
                          cursor: 'pointer',
                          padding: '4px 8px',
                          marginTop: '4px',
                          background: 'rgba(0, 255, 255, 0.1)',
                          borderRadius: '6px',
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
          <div style={{ color: '#00ffff', textAlign: 'center' }}>
            Thinking...
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} style={{
        padding: '20px',
        borderTop: '1px solid #00ffff',
        display: 'flex',
        gap: '10px',
      }}>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={sessionId ? "Ask a question..." : "Start learning..."}
          disabled={loading}
          style={{
            flex: 1,
            padding: '12px',
            background: 'rgba(0, 255, 255, 0.1)',
            border: '1px solid #00ffff',
            borderRadius: '8px',
            color: '#fff',
          }}
        />
        <button
          type="submit"
          disabled={loading || (!sessionId && !inputText.trim())}
          style={{
            padding: '12px 24px',
            background: '#00ffff',
            color: '#000',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 'bold',
          }}
        >
          {sessionId ? 'Send' : 'Start'}
        </button>
      </form>
    </motion.div>
  );
};

export default AITutorChat;
