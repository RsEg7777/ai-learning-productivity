'use client';
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import VoiceInput from './VoiceInput';

interface ContentSummarizerProps { authToken: string; }

const ContentSummarizer: React.FC<ContentSummarizerProps> = ({ authToken }) => {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || '';
  const [content, setContent] = useState('');
  const [summaryType, setSummaryType] = useState('detailed');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);

  const handleVoice = (text: string) => {
    setContent(p => p + (p.endsWith(' ') || !p ? '' : ' ') + text);
  };

  const summarize = async () => {
    if (!content.trim()) { setError('Please enter content to summarize'); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await fetch(`${API_URL}/content/summarize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` },
        body: JSON.stringify({ content, summary_type: summaryType }),
      });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Summarization failed'); }
      const data = await res.json();
      setResult(data);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const TYPES = [
    { id: 'brief', label: '⚡ Brief', desc: '3-5 sentences' },
    { id: 'detailed', label: '📋 Detailed', desc: 'Comprehensive' },
    { id: 'bullet_points', label: '• Bullet Points', desc: 'Key points list' },
    { id: 'hierarchical', label: '🗂️ Hierarchical', desc: 'Outline structure' },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="component-container">
      <h2>📄 Content Summarizer</h2>
      <p>Paste any text — lecture notes, articles, documentation — and get an AI-powered summary in seconds using Amazon Bedrock Nova Pro</p>

      {error && <div className="error">⚠️ {error}</div>}

      <div style={{ display: 'flex', gap: '.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {TYPES.map(t => (
          <motion.button key={t.id} whileHover={{ scale: 1.04 }} whileTap={{ scale: .96 }}
            onClick={() => setSummaryType(t.id)}
            style={{
              padding: '.55rem 1.1rem', borderRadius: 'var(--r-full)', cursor: 'pointer',
              background: summaryType === t.id ? 'linear-gradient(135deg,var(--indigo),var(--violet))' : 'var(--bg-glass)',
              border: `1px solid ${summaryType === t.id ? 'transparent' : 'var(--border-default)'}`,
              color: summaryType === t.id ? '#fff' : 'var(--text-secondary)',
              fontSize: '.82rem', fontWeight: 600, backdropFilter: 'blur(8px)',
              boxShadow: summaryType === t.id ? '0 0 20px var(--glow-primary)' : 'none',
            }}>
            {t.label} <span style={{ opacity: .7, fontSize: '.72rem' }}>({t.desc})</span>
          </motion.button>
        ))}
      </div>

      <div className="form-group">
        <label style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
          Content to Summarize
          <VoiceInput onTranscript={handleVoice} disabled={loading} />
        </label>
        <textarea value={content} onChange={e => setContent(e.target.value)} rows={12}
          placeholder="Paste your text here, or use the 🎤 mic to dictate. Supports lecture notes, articles, documentation, textbooks..." />
      </div>

      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '.5rem' }}>
        <span style={{ color: 'var(--text-muted)', fontSize: '.8rem' }}>
          {content.split(/\s+/).filter(Boolean).length} words · {content.length} chars
        </span>
      </div>

      <button className="btn-primary" onClick={summarize} disabled={loading}>
        {loading ? '🤖 Summarizing...' : '✨ Summarize with AI'}
      </button>
      {loading && <div className="loading"><p>Amazon Bedrock Nova Pro is reading and summarizing...</p></div>}

      {result && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="success">✅ Summary generated ({result.type?.replace('_', ' ')})</div>

          <div style={{ padding: '1.5rem', background: 'rgba(13,13,36,0.7)', backdropFilter: 'blur(16px)', border: '1px solid var(--border-default)', borderRadius: 'var(--r-lg)' }}>
            <h3 style={{ color: 'var(--indigo-light)', fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '.5rem' }}>
              📝 Summary
              <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: .95 }}
                onClick={() => navigator.clipboard.writeText(result.summary)}
                style={{ padding: '.25rem .65rem', background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 'var(--r-sm)', color: 'var(--indigo-light)', fontSize: '.72rem', fontWeight: 600, cursor: 'pointer' }}>
                📋 Copy
              </motion.button>
            </h3>
            <p style={{ color: 'var(--text-primary)', lineHeight: 1.8, whiteSpace: 'pre-wrap', fontSize: '.92rem' }}>{result.summary}</p>
          </div>

          {result.key_points?.length > 0 && (
            <div style={{ padding: '1.5rem', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: 'var(--r-lg)' }}>
              <h3 style={{ color: '#34d399', fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>🎯 Key Takeaways</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '.6rem' }}>
                {result.key_points.map((pt: string, i: number) => (
                  <motion.div key={i} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * .08 }}
                    style={{ display: 'flex', gap: '.75rem', alignItems: 'flex-start' }}>
                    <span style={{ width: '22px', height: '22px', borderRadius: '50%', background: 'linear-gradient(135deg,var(--indigo),var(--violet))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '.72rem', fontWeight: 700, color: '#fff', flexShrink: 0, marginTop: '.1rem' }}>{i + 1}</span>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '.875rem', lineHeight: 1.6 }}>{pt}</p>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: '.75rem', flexWrap: 'wrap' }}>
            <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: .97 }}
              onClick={() => { setResult(null); setContent(''); }}
              style={{ padding: '.55rem 1.1rem', background: 'var(--bg-glass)', border: '1px solid var(--border-default)', borderRadius: 'var(--r-md)', color: 'var(--text-secondary)', fontSize: '.85rem', fontWeight: 600, cursor: 'pointer' }}>
              🔄 New Summary
            </motion.button>
            {TYPES.filter(t => t.id !== summaryType).slice(0, 2).map(t => (
              <motion.button key={t.id} whileHover={{ scale: 1.03 }} whileTap={{ scale: .97 }}
                onClick={() => { setSummaryType(t.id); summarize(); }}
                style={{ padding: '.55rem 1.1rem', background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.25)', borderRadius: 'var(--r-md)', color: 'var(--indigo-light)', fontSize: '.85rem', fontWeight: 600, cursor: 'pointer' }}>
                Try {t.label}
              </motion.button>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};
export default ContentSummarizer;
