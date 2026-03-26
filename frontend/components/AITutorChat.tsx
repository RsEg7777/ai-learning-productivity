'use client';
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import VoiceInput from './VoiceInput';
const API_URL = () => process.env.NEXT_PUBLIC_API_URL || '';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  followUpQuestions?: string[];
}
interface AITutorChatProps { authToken: string; }

const LANGUAGES = [
  { value: 'english', label: 'English' },
  { value: 'hindi', label: 'हिन्दी (Hindi)' },
  { value: 'hinglish', label: 'Hinglish' },
  { value: 'tamil', label: 'தமிழ் (Tamil)' },
  { value: 'tanglish', label: 'Tanglish' },
  { value: 'telugu', label: 'తెలుగు (Telugu)' },
  { value: 'bengali', label: 'বাংলা (Bengali)' },
  { value: 'marathi', label: 'मराठी (Marathi)' },
  { value: 'gujarati', label: 'ગુજરાતી (Gujarati)' },
  { value: 'kannada', label: 'ಕನ್ನಡ (Kannada)' },
  { value: 'malayalam', label: 'മലയാളം (Malayalam)' },
  { value: 'punjabi', label: 'ਪੰਜਾਬੀ (Punjabi)' },
  { value: 'odia', label: 'ଓଡ଼ିଆ (Odia)' },
  { value: 'urdu', label: 'اردو (Urdu)' },
];

const AITutorChat: React.FC<AITutorChatProps> = ({ authToken }) => {
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
    setInputText(prev => prev + (prev && !prev.endsWith(' ') ? ' ' : '') + text);
  }, []);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const startSession = async () => {
    if (!API_URL()) { setError('API URL not configured. Set NEXT_PUBLIC_API_URL.'); return; }
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API_URL()}/tutor/start-session`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` },
        body: JSON.stringify({ user_id: 'user123', subject: subject || undefined, teaching_style: teachingStyle, difficulty_level: 'adaptive' }),
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || res.statusText); }
      const data = await res.json();
      setSessionId(data.session_id);
      setMessages([{ role: 'assistant', content: `Hello! I'm your AI tutor${subject ? ` for ${subject}` : ''}. I'll use the ${teachingStyle} method. What would you like to explore?`, timestamp: new Date().toISOString() }]);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const askQuestion = async (question: string) => {
    if (!sessionId || !question.trim()) return;
    setMessages(prev => [...prev, { role: 'user', content: question, timestamp: new Date().toISOString() }]);
    setInputText(''); setLoading(true); setError('');
    try {
      const res = await fetch(`${API_URL()}/tutor/ask-question`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` },
        body: JSON.stringify({ session_id: sessionId, question, include_examples: true, use_socratic_method: teachingStyle === 'socratic', language }),
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || res.statusText); }
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer, timestamp: new Date().toISOString(), followUpQuestions: data.follow_up_questions }]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: `❌ Error: ${e.message}`, timestamp: new Date().toISOString() }]);
    } finally { setLoading(false); }
  };

  const handleSubmit = (e: React.FormEvent) => { e.preventDefault(); sessionId ? askQuestion(inputText) : startSession(); };

  return (
    <div className="component-container" style={{ maxWidth: 900, margin: '0 auto' }}>
      <h2>🤖 AI Tutor</h2>
      <p>Personalised tutoring with Socratic method, powered by Amazon Bedrock Nova Pro</p>

      {error && <div className="error">⚠️ {error}</div>}

      {!sessionId && (
        <div style={{ marginBottom: '2rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Subject (optional)</label>
            <input type="text" value={subject} onChange={e => setSubject(e.target.value)} placeholder="e.g., Python, Mathematics…" />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Teaching Style</label>
            <select value={teachingStyle} onChange={e => setTeachingStyle(e.target.value)}>
              <option value="socratic">Socratic (Guiding Questions)</option>
              <option value="direct">Direct (Clear Explanations)</option>
              <option value="exploratory">Exploratory (Discovery)</option>
            </select>
          </div>
          <div className="form-group" style={{ marginBottom: 0, gridColumn: '1/-1' }}>
            <label>🌍 Response Language (Indian Languages Supported)</label>
            <select value={language} onChange={e => setLanguage(e.target.value)}>
              {LANGUAGES.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
          </div>
        </div>
      )}

      <div style={{ background: 'rgba(0,0,0,0.25)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 14, height: 480, overflowY: 'auto', padding: '1.5rem', marginBottom: '1rem' }}>
        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: '1rem' }}>
              <div style={{ maxWidth: '78%', padding: '1rem 1.2rem', borderRadius: 14, background: msg.role === 'user' ? 'linear-gradient(135deg,#6366f1,#4338ca)' : 'rgba(255,255,255,0.05)', border: msg.role === 'user' ? 'none' : '1px solid rgba(255,255,255,0.08)', whiteSpace: 'pre-wrap', lineHeight: 1.65, fontSize: '0.9rem' }}>
                {msg.content}
                {msg.followUpQuestions && msg.followUpQuestions.length > 0 && (
                  <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                    <div style={{ color: '#818cf8', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.5rem' }}>💡 Think about:</div>
                    {msg.followUpQuestions.map((q, qi) => (
                      <div key={qi} onClick={() => askQuestion(q)} style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', padding: '0.45rem 0.75rem', marginTop: '0.35rem', background: 'rgba(99,102,241,0.08)', borderRadius: 8, border: '1px solid rgba(99,102,241,0.18)', cursor: 'pointer', transition: 'all 0.15s' }}
                        onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = 'rgba(99,102,241,0.5)'; }}
                        onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'rgba(99,102,241,0.18)'; }}>
                        {q}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {loading && <div style={{ display: 'flex', gap: 6, padding: '0.5rem 0' }}>
          {[0,0.2,0.4].map((d,i) => <motion.div key={i} animate={{ scale:[1,1.4,1] }} transition={{ repeat:Infinity, duration:0.7, delay:d }} style={{ width:8, height:8, borderRadius:'50%', background:'var(--indigo)' }} />)}
        </div>}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.75rem' }}>
        <input type="text" value={inputText} onChange={e => setInputText(e.target.value)} placeholder={sessionId ? 'Ask a question…' : 'Press Start to begin'} disabled={loading} style={{ flex: 1, padding: '0.85rem 1rem', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, color: 'var(--text-primary)', fontSize: '0.9rem' }} />
        <VoiceInput onTranscript={handleVoiceTranscript} disabled={loading} />
        <button type="submit" disabled={loading || (!sessionId && !inputText.trim())} className="btn-primary" style={{ width: 'auto', padding: '0.85rem 2rem' }}>
          {loading ? '…' : sessionId ? 'Send' : 'Start'}
        </button>
      </form>
    </div>
  );
};
export default AITutorChat;
