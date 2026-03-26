'use client';
import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import VoiceInput from './VoiceInput';
const API_URL = () => process.env.NEXT_PUBLIC_API_URL || '';

interface QuizGeneratorProps { authToken: string; }
interface Question { id: string; type: string; text: string; options?: string[]; points: number; difficulty: string; }
interface Quiz { quiz_id: string; title: string; questions: Question[]; time_limit?: number; passing_score: number; }

const QuizGenerator: React.FC<QuizGeneratorProps> = ({ authToken }) => {
  const [content, setContent] = useState('');
  const [count, setCount] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [submitted, setSubmitted] = useState(false);

  const handleVoice = useCallback((text: string) => {
    setContent(prev => prev + (prev && !prev.endsWith(' ') ? ' ' : '') + text);
  }, []);

  const generate = async () => {
    if (!content.trim()) { setError('Please enter content to generate a quiz from.'); return; }
    if (!API_URL()) { setError('API URL not configured. Set NEXT_PUBLIC_API_URL in your environment.'); return; }
    setLoading(true); setError(''); setQuiz(null); setAnswers({}); setSubmitted(false);
    try {
      const res = await fetch(`${API_URL()}/quiz/generate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` },
        body: JSON.stringify({ content, question_count: count }),
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || res.statusText); }
      const data = await res.json();
      if (!data.success) throw new Error(data.detail || 'Quiz generation failed');
      setQuiz(data);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const score = quiz ? quiz.questions.filter((q, i) => q.options && answers[q.id] === 0).length : 0;

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="component-container">
      <h2>📝 AI Quiz Generator</h2>
      <p>Generate intelligent quizzes with multiple question types using Amazon Bedrock</p>

      {error && <div className="error">⚠️ {error}</div>}

      <div className="form-group">
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          Learning Content <VoiceInput onTranscript={handleVoice} disabled={loading} />
        </label>
        <textarea value={content} onChange={e => setContent(e.target.value)} placeholder="Paste lecture notes, documentation, or any learning material here…" rows={10} />
      </div>

      <div className="form-group">
        <label>Number of Questions: <strong style={{ color: 'var(--indigo-light)', marginLeft: 6 }}>{count}</strong></label>
        <input type="range" min={3} max={15} value={count} onChange={e => setCount(+e.target.value)} />
        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.78rem', marginTop: 4 }}><span>3</span><span>15</span></div>
      </div>

      <button className="btn-primary" onClick={generate} disabled={loading}>
        {loading ? '🤖 Generating with AI…' : '✨ Generate Quiz'}
      </button>

      {loading && <div className="loading"><p>Amazon Bedrock is analysing your content…</p></div>}

      {quiz && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="quiz-results">
          <div className="success">✅ {quiz.questions.length} questions generated — Passing: {quiz.passing_score}%{quiz.time_limit ? ` · Time: ${quiz.time_limit}s` : ''}</div>
          <div style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 14, padding: '1.25rem', marginBottom: '1rem' }}>
            <h3 style={{ color: 'var(--indigo-light)', fontSize: '1.2rem', marginBottom: 0 }}>{quiz.title}</h3>
          </div>

          {quiz.questions.map((q, i) => (
            <motion.div key={q.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }} className="question-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                <span className="question-type">{q.type.replace('_', ' ')}</span>
                <span className={`tag tag-${q.difficulty === 'easy' ? 'emerald' : q.difficulty === 'hard' ? 'rose' : 'amber'}`}>{q.difficulty}</span>
                <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: '0.8rem' }}>{q.points} pt{q.points !== 1 ? 's' : ''}</span>
              </div>
              <p style={{ color: 'var(--text-primary)', fontSize: '0.95rem', fontWeight: 500, marginBottom: '1rem' }}>Q{i + 1}. {q.text}</p>
              {q.options ? (
                <ul className="options">
                  {q.options.map((opt, oi) => (
                    <li key={oi} onClick={() => !submitted && setAnswers(prev => ({ ...prev, [q.id]: oi }))}
                      style={{ cursor: submitted ? 'default' : 'pointer', borderColor: answers[q.id] === oi ? 'rgba(99,102,241,0.6)' : undefined, background: answers[q.id] === oi ? 'rgba(99,102,241,0.12)' : undefined, color: answers[q.id] === oi ? 'var(--indigo-light)' : undefined }}>
                      <span style={{ color: 'var(--indigo-light)', fontWeight: 700, marginRight: '0.5rem' }}>{String.fromCharCode(65 + oi)}.</span>{opt}
                    </li>
                  ))}
                </ul>
              ) : (
                <textarea placeholder="Your answer…" rows={3} style={{ width: '100%', padding: '0.75rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', resize: 'vertical' }} />
              )}
            </motion.div>
          ))}
        </motion.div>
      )}
    </motion.div>
  );
};
export default QuizGenerator;
