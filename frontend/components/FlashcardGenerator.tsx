'use client';
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
const API_URL = () => process.env.NEXT_PUBLIC_API_URL || '';

interface FlashcardGeneratorProps { authToken: string; }
interface Flashcard { id: string; question: string; answer: string; difficulty: string; tags: string[]; }

const FlashcardGenerator: React.FC<FlashcardGeneratorProps> = ({ authToken }) => {
  const [content, setContent] = useState('');
  const [count, setCount] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [cards, setCards] = useState<Flashcard[]>([]);
  const [flipped, setFlipped] = useState<Set<string>>(new Set());
  const [current, setCurrent] = useState(0);
  const [mode, setMode] = useState<'grid' | 'study'>('grid');

  const generate = async () => {
    if (!content.trim()) { setError('Please enter content to generate flashcards from.'); return; }
    if (!API_URL()) { setError('API URL not configured. Set NEXT_PUBLIC_API_URL.'); return; }
    setLoading(true); setError(''); setCards([]); setFlipped(new Set()); setCurrent(0);
    try {
      const res = await fetch(`${API_URL()}/flashcards/generate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` },
        body: JSON.stringify({ content, count }),
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || res.statusText); }
      const data = await res.json();
      if (!data.success) throw new Error('Flashcard generation failed');
      setCards(data.flashcards);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const toggle = (id: string) => setFlipped(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="component-container">
      <h2>🎴 Flashcard Generator</h2>
      <p>AI-powered flashcards with spaced repetition — powered by Amazon Bedrock</p>

      {error && <div className="error">⚠️ {error}</div>}

      <div className="form-group">
        <label>Learning Content</label>
        <textarea value={content} onChange={e => setContent(e.target.value)} placeholder="Paste your study material here…" rows={8} />
      </div>
      <div className="form-group">
        <label>Cards to generate: <strong style={{ color: 'var(--indigo-light)', marginLeft: 6 }}>{count}</strong></label>
        <input type="range" min={5} max={20} value={count} onChange={e => setCount(+e.target.value)} />
      </div>
      <button className="btn-primary" onClick={generate} disabled={loading}>
        {loading ? '🤖 Generating flashcards…' : '✨ Generate Flashcards'}
      </button>

      {loading && <div className="loading"><p>Creating intelligent flashcards with Amazon Bedrock…</p></div>}

      {cards.length > 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flashcard-results">
          <div className="success">✅ {cards.length} flashcards created! Click any card to reveal the answer.</div>

          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <button onClick={() => setMode('grid')} className={mode === 'grid' ? 'btn-primary' : 'btn-secondary'} style={{ width: 'auto', padding: '0.5rem 1.2rem', fontSize: '0.82rem' }}>⊞ Grid</button>
            <button onClick={() => { setMode('study'); setCurrent(0); }} className={mode === 'study' ? 'btn-primary' : 'btn-secondary'} style={{ width: 'auto', padding: '0.5rem 1.2rem', fontSize: '0.82rem' }}>📖 Study Mode</button>
          </div>

          {mode === 'grid' ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px,1fr))', gap: '1rem' }}>
              {cards.map((card, i) => (
                <motion.div key={card.id} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.05 }}
                  className="flashcard" onClick={() => toggle(card.id)}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem', fontWeight: 600 }}>Card {i + 1}</span>
                    <span className={`flashcard-difficulty`} style={{ borderColor: card.difficulty === 'easy' ? 'rgba(16,185,129,0.4)' : card.difficulty === 'hard' ? 'rgba(244,63,94,0.4)' : 'rgba(245,158,11,0.4)', color: card.difficulty === 'easy' ? '#34d399' : card.difficulty === 'hard' ? '#fb7185' : '#fbbf24' }}>{card.difficulty}</span>
                  </div>
                  <AnimatePresence mode="wait">
                    {!flipped.has(card.id) ? (
                      <motion.div key="q" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--indigo-light)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.5rem' }}>Question</div>
                        <p style={{ fontSize: '0.92rem', lineHeight: 1.6 }}>{card.question}</p>
                      </motion.div>
                    ) : (
                      <motion.div key="a" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#34d399', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.5rem' }}>Answer</div>
                        <p style={{ fontSize: '0.92rem', lineHeight: 1.6 }}>{card.answer}</p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                  {card.tags?.length > 0 && <div style={{ marginTop: '0.85rem', display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                    {card.tags.map(t => <span key={t} className="tag tag-indigo" style={{ fontSize: '0.68rem' }}>{t}</span>)}
                  </div>}
                </motion.div>
              ))}
            </div>
          ) : (
            <div style={{ maxWidth: 560, margin: '0 auto' }}>
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '1.5rem' }}>
                Card {current + 1} of {cards.length}
              </div>
              <motion.div key={current} initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }}
                className="flashcard" onClick={() => toggle(cards[current].id)} style={{ minHeight: 200, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.72rem', fontWeight: 700, color: flipped.has(cards[current].id) ? '#34d399' : 'var(--indigo-light)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '1rem' }}>
                    {flipped.has(cards[current].id) ? '✓ Answer' : 'Question — tap to reveal'}
                  </div>
                  <p style={{ fontSize: '1.05rem', lineHeight: 1.7 }}>
                    {flipped.has(cards[current].id) ? cards[current].answer : cards[current].question}
                  </p>
                </div>
              </motion.div>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', justifyContent: 'center' }}>
                <button onClick={() => { setCurrent(c => Math.max(0, c - 1)); setFlipped(new Set()); }} disabled={current === 0} className="btn-secondary">← Prev</button>
                <button onClick={() => { setCurrent(c => Math.min(cards.length - 1, c + 1)); setFlipped(new Set()); }} disabled={current === cards.length - 1} className="btn-primary" style={{ width: 'auto', padding: '0.7rem 1.4rem' }}>Next →</button>
              </div>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
};
export default FlashcardGenerator;
