'use client';
import React, { useState } from 'react';
import { motion } from 'framer-motion';
const API_URL = () => process.env.NEXT_PUBLIC_API_URL || '';

interface CodePlaygroundProps { authToken: string; }
const LANGS = ['python','javascript','java','cpp','c','go','rust','ruby','php','typescript'];

const CodePlayground: React.FC<CodePlaygroundProps> = ({ authToken }) => {
  const [code, setCode] = useState('# Write your Python code here\nprint("Hello, World!")');
  const [language, setLanguage] = useState('python');
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState('');
  const [userInput, setUserInput] = useState('');
  const [showInput, setShowInput] = useState(false);
  const [hasError, setHasError] = useState(false);

  const needsInput = (c: string, l: string) => {
    const p: Record<string,RegExp[]> = {
      python:[/input\s*\(/], javascript:[/prompt\s*\(/, /readline\s*\(/],
      java:[/Scanner/, /\.nextLine\(/, /\.nextInt\(/], cpp:[/cin\s*>>/, /scanf\s*\(/],
    };
    return (p[l]||[]).some(r => r.test(c));
  };

  const run = async () => {
    if (!API_URL()) { setOutput('❌ API URL not configured. Set NEXT_PUBLIC_API_URL.'); return; }
    if (needsInput(code, language) && !userInput && !showInput) { setShowInput(true); return; }
    setIsRunning(true); setOutput('Running…'); setAiSuggestion(''); setHasError(false); setShowInput(false);
    try {
      const res = await fetch(`${API_URL()}/playground/execute`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` },
        body: JSON.stringify({ code, language, input: userInput || undefined }),
      });
      const data = await res.json();
      setOutput(data.output || (data.error ? `Error: ${data.error}` : 'No output'));
      setHasError(!data.success);
      if (data.ai_suggestion) setAiSuggestion(data.ai_suggestion);
    } catch (e: any) { setOutput(`❌ ${e.message}`); setHasError(true); }
    finally { setIsRunning(false); }
  };

  const getAiHelp = async () => {
    if (!API_URL() || !code.trim()) return;
    setAiSuggestion('Analysing with AI…');
    try {
      const res = await fetch(`${API_URL()}/code/analyze`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` },
        body: JSON.stringify({ code, language }),
      });
      const data = await res.json();
      if (data.success && data.analysis?.explanation) {
        let text = data.analysis.explanation;
        if (data.analysis.improvements?.length) text += '\n\nKey improvements:\n' + data.analysis.improvements.slice(0,3).map((i: any) => `• ${i.title}: ${i.description}`).join('\n');
        setAiSuggestion(text);
      }
    } catch { setAiSuggestion('AI analysis unavailable.'); }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ maxWidth: 1100, margin: '0 auto' }}>
      <div className="component-container">
        <h2>💻 Interactive Code Playground</h2>
        <p>Write, run, and get AI feedback on your code — Python execution powered by real runtime</p>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <label style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', fontWeight: 600 }}>Language</label>
          <select value={language} onChange={e => { setLanguage(e.target.value); setCode(''); setOutput(''); }} style={{ padding: '0.45rem 2.2rem 0.45rem 0.9rem', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: 'var(--text-primary)', fontSize: '0.85rem', appearance: 'none', backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236366f1' d='M6 8.5L1.5 4h9z'/%3E%3C/svg%3E\")", backgroundRepeat: 'no-repeat', backgroundPosition: 'right 0.75rem center', cursor: 'pointer' }}>
            {LANGS.map(l => <option key={l} value={l}>{l.toUpperCase()}</option>)}
          </select>
        </div>

        <textarea value={code} onChange={e => setCode(e.target.value)} style={{ width: '100%', minHeight: 280, background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: '1.1rem', color: 'var(--text-primary)', fontSize: '0.87rem', fontFamily: 'var(--font-mono)', resize: 'vertical', marginBottom: '1rem', lineHeight: 1.65, outline: 'none' }} />

        {showInput && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.25)', borderRadius: 12, padding: '1rem', marginBottom: '1rem' }}>
            <label style={{ color: 'var(--indigo-light)', fontWeight: 600, display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem' }}>📥 Your code requires input — enter values (one per line):</label>
            <textarea value={userInput} onChange={e => setUserInput(e.target.value)} rows={4} style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, padding: '0.75rem', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: '0.87rem', resize: 'vertical' }} placeholder="Enter input values here…" />
            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.75rem' }}>
              <button onClick={run} className="btn-primary" style={{ width: 'auto', padding: '0.6rem 1.4rem', fontSize: '0.85rem' }}>▶ Run with Input</button>
              <button onClick={() => setShowInput(false)} className="btn-secondary">Cancel</button>
            </div>
          </motion.div>
        )}

        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <button onClick={run} disabled={isRunning} style={{ padding: '0.75rem 2rem', background: 'linear-gradient(135deg,#6366f1,#4338ca)', border: '1px solid rgba(99,102,241,0.4)', borderRadius: 10, color: 'white', fontSize: '0.92rem', fontWeight: 600, cursor: isRunning ? 'not-allowed' : 'pointer', opacity: isRunning ? 0.6 : 1, fontFamily: 'var(--font-sans)' }}>
            {isRunning ? '⏳ Running…' : '▶ Run Code'}
          </button>
          <button onClick={getAiHelp} style={{ padding: '0.75rem 1.75rem', background: 'rgba(139,92,246,0.12)', border: '1px solid rgba(139,92,246,0.35)', borderRadius: 10, color: 'var(--violet)', fontSize: '0.92rem', fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
            🤖 AI Suggestions
          </button>
          {userInput && <button onClick={() => setUserInput('')} style={{ padding: '0.75rem 1.2rem', background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.3)', borderRadius: 10, color: '#fb7185', fontSize: '0.85rem', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>✕ Clear Input</button>}
        </div>

        {output && (
          <div style={{ background: 'rgba(0,0,0,0.4)', border: `1px solid ${hasError ? 'rgba(244,63,94,0.3)' : 'rgba(16,185,129,0.2)'}`, borderRadius: 12, padding: '1rem 1.25rem', marginBottom: '1rem' }}>
            <div style={{ color: hasError ? '#fb7185' : '#34d399', fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.5rem' }}>{hasError ? '❌ Error' : '✓ Output'}</div>
            <pre style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: '0.87rem', whiteSpace: 'pre-wrap', lineHeight: 1.65 }}>{output}</pre>
          </div>
        )}

        {aiSuggestion && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.25)', borderRadius: 12, padding: '1rem 1.25rem' }}>
            <div style={{ color: 'var(--violet)', fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.5rem' }}>🤖 AI Analysis</div>
            <pre style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)', fontSize: '0.87rem', whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{aiSuggestion}</pre>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};
export default CodePlayground;
