'use client';
import React, { useState } from 'react';
import { motion } from 'framer-motion';
const API_URL = () => process.env.NEXT_PUBLIC_API_URL || '';

interface CodeAnalyzerProps { authToken: string; }

const LANGS = ['python','javascript','typescript','java','cpp','csharp','go','rust','ruby','php'];

const CodeAnalyzer: React.FC<CodeAnalyzerProps> = ({ authToken }) => {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState<any>(null);

  const analyze = async () => {
    if (!code.trim()) { setError('Please enter code to analyse.'); return; }
    if (!API_URL()) { setError('API URL not configured. Set NEXT_PUBLIC_API_URL.'); return; }
    setLoading(true); setError(''); setAnalysis(null);
    try {
      const res = await fetch(`${API_URL()}/code/analyze`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` },
        body: JSON.stringify({ code, language }),
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || res.statusText); }
      const data = await res.json();
      setAnalysis(data.analysis);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const severityColor = (s: string) => ({ critical: '#fb7185', high: '#f97316', medium: '#fbbf24', low: '#34d399' }[s] || '#94a3b8');

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="component-container">
      <h2>🔍 AI Code Analyser</h2>
      <p>Deep code analysis — issues, improvements, complexity metrics, powered by Amazon Bedrock</p>

      {error && <div className="error">⚠️ {error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1rem', marginBottom: '1.25rem', alignItems: 'end' }}>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label>Language</label>
          <select value={language} onChange={e => setLanguage(e.target.value)}>
            {LANGS.map(l => <option key={l} value={l}>{l.toUpperCase()}</option>)}
          </select>
        </div>
        <div />
      </div>

      <div className="form-group">
        <label>Code</label>
        <textarea value={code} onChange={e => setCode(e.target.value)} placeholder="Paste your code here…" rows={16} style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }} />
      </div>

      <button className="btn-primary" onClick={analyze} disabled={loading}>
        {loading ? '🤖 Analysing with AI…' : '✨ Analyse Code'}
      </button>

      {loading && <div className="loading"><p>Amazon Bedrock is analysing your code…</p><p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>This may take 15–30 seconds</p></div>}

      {analysis && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="success">✅ Analysis complete</div>

          {analysis.explanation && (
            <div className="glass-panel">
              <h3 style={{ color: 'var(--indigo-light)', marginBottom: '0.75rem', fontSize: '0.95rem' }}>📖 Overview</h3>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '0.88rem' }}>{analysis.explanation}</p>
            </div>
          )}

          {analysis.issues?.length > 0 && (
            <div className="glass-panel">
              <h3 style={{ color: '#fb7185', marginBottom: '0.85rem', fontSize: '0.95rem' }}>⚠️ Issues ({analysis.issues.length})</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {analysis.issues.map((issue: any, i: number) => (
                  <div key={i} style={{ padding: '0.75rem 1rem', background: 'rgba(0,0,0,0.2)', borderRadius: 10, borderLeft: `3px solid ${severityColor(issue.severity)}` }}>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.35rem' }}>
                      <span style={{ color: severityColor(issue.severity), fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase' }}>{issue.severity}</span>
                      {issue.line && <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>Line {issue.line}</span>}
                    </div>
                    <p style={{ color: 'var(--text-primary)', fontSize: '0.85rem', marginBottom: '0.25rem' }}>{issue.message}</p>
                    {issue.suggestion && <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>💡 {issue.suggestion}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {analysis.improvements?.length > 0 && (
            <div className="glass-panel">
              <h3 style={{ color: '#34d399', marginBottom: '0.85rem', fontSize: '0.95rem' }}>🔧 Improvements ({analysis.improvements.length})</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                {analysis.improvements.map((imp: any, i: number) => (
                  <div key={i} style={{ padding: '0.75rem 1rem', background: 'rgba(0,0,0,0.2)', borderRadius: 10, borderLeft: '3px solid rgba(16,185,129,0.5)' }}>
                    <p style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.88rem', marginBottom: '0.3rem' }}>{imp.title}</p>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', marginBottom: imp.benefit ? '0.3rem' : 0 }}>{imp.description}</p>
                    {imp.benefit && <p style={{ color: '#34d399', fontSize: '0.78rem' }}>✓ {imp.benefit}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {analysis.complexity && (
            <div className="glass-panel">
              <h3 style={{ color: 'var(--indigo-light)', marginBottom: '0.85rem', fontSize: '0.95rem' }}>📊 Complexity Metrics</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px,1fr))', gap: '0.75rem' }}>
                {[
                  { label: 'Cyclomatic', value: analysis.complexity.cyclomatic },
                  { label: 'Cognitive', value: analysis.complexity.cognitive },
                  { label: 'Lines of Code', value: analysis.complexity.lines_of_code },
                  { label: 'Maintainability', value: analysis.complexity.maintainability_index ? `${analysis.complexity.maintainability_index}/100` : 'N/A' },
                ].map(m => (
                  <div key={m.label} style={{ background: 'rgba(0,0,0,0.25)', borderRadius: 10, padding: '0.85rem', textAlign: 'center' }}>
                    <div style={{ color: 'var(--indigo-light)', fontSize: '1.4rem', fontWeight: 700 }}>{m.value ?? '—'}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: 4 }}>{m.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {analysis.best_practices?.length > 0 && (
            <div className="glass-panel">
              <h3 style={{ color: 'var(--cyan)', marginBottom: '0.75rem', fontSize: '0.95rem' }}>✨ Best Practices</h3>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {analysis.best_practices.map((bp: string, i: number) => (
                  <li key={i} style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', paddingLeft: '1.2rem', position: 'relative' }}>
                    <span style={{ position: 'absolute', left: 0, color: 'var(--cyan)' }}>›</span>{bp}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
};
export default CodeAnalyzer;
