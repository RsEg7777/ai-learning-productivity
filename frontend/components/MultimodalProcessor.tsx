'use client';
import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
const API_URL = () => process.env.NEXT_PUBLIC_API_URL || '';

interface MultimodalProcessorProps { authToken: string; }
type Mode = 'handwriting' | 'diagram' | 'math' | 'screenshot';

const MODES = [
  { id: 'handwriting' as Mode, icon: '✍️', label: 'Handwriting OCR', desc: 'Extract text from handwritten notes' },
  { id: 'diagram' as Mode, icon: '📊', label: 'Diagram Analysis', desc: 'Understand flowcharts, UML, architecture' },
  { id: 'math' as Mode, icon: '🔢', label: 'Math Solver', desc: 'Solve equations step by step' },
  { id: 'screenshot' as Mode, icon: '📸', label: 'Screenshot → Quiz', desc: 'Generate quiz from any screenshot' },
];

const MultimodalProcessor: React.FC<MultimodalProcessorProps> = ({ authToken }) => {
  const [mode, setMode] = useState<Mode>('handwriting');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]; if (!f) return;
    setFile(f); setResult(null); setError('');
    const reader = new FileReader(); reader.onloadend = () => setPreview(reader.result as string); reader.readAsDataURL(f);
  };

  const process = async () => {
    if (!file) return;
    if (!API_URL()) { setError('API URL not configured. Set NEXT_PUBLIC_API_URL.'); return; }
    setProcessing(true); setResult(null); setError('');
    try {
      const ep = { handwriting: '/multimodal/process-handwriting', diagram: '/multimodal/understand-diagram', math: '/multimodal/solve-math', screenshot: '/multimodal/screenshot-to-quiz' }[mode];
      const fd = new FormData(); fd.append('image', file); fd.append('mode', mode);
      const res = await fetch(`${API_URL()}${ep}`, { method: 'POST', headers: { Authorization: `Bearer ${authToken}` }, body: fd });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || res.statusText); }
      const data = await res.json();
      if (!data.success) throw new Error('Processing failed');
      setResult(data);
    } catch (e: any) { setError(e.message); }
    finally { setProcessing(false); }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="component-container">
      <h2>🖼️ Multimodal AI Processor</h2>
      <p>Process images with Claude Vision — OCR, diagram analysis, math solving, screenshot-to-quiz</p>

      {error && <div className="error">⚠️ {error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: '0.75rem', marginBottom: '2rem' }}>
        {MODES.map(m => (
          <button key={m.id} onClick={() => { setMode(m.id); setResult(null); }} style={{ background: mode === m.id ? 'linear-gradient(135deg,rgba(99,102,241,0.2),rgba(139,92,246,0.15))' : 'rgba(255,255,255,0.03)', border: `1px solid ${mode === m.id ? 'rgba(99,102,241,0.5)' : 'rgba(255,255,255,0.08)'}`, borderRadius: 12, padding: '1rem', textAlign: 'left', cursor: 'pointer', transition: 'all 0.18s', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)' }}>
            <div style={{ fontSize: '1.5rem', marginBottom: '0.4rem' }}>{m.icon}</div>
            <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.25rem', color: mode === m.id ? 'var(--indigo-light)' : 'var(--text-primary)' }}>{m.label}</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>{m.desc}</div>
          </button>
        ))}
      </div>

      <div onClick={() => inputRef.current?.click()} onDragOver={e => e.preventDefault()}
        onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) { setFile(f); const r = new FileReader(); r.onloadend = () => setPreview(r.result as string); r.readAsDataURL(f); }}}
        style={{ border: '2px dashed rgba(99,102,241,0.3)', borderRadius: 16, padding: '2rem', textAlign: 'center', cursor: 'pointer', marginBottom: '1.5rem', transition: 'border-color 0.18s', background: 'rgba(99,102,241,0.03)' }}
        onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(99,102,241,0.6)')}
        onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(99,102,241,0.3)')}>
        <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📁</div>
        <p style={{ color: 'var(--indigo-light)', fontWeight: 600 }}>Drop image here or click to browse</p>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.35rem' }}>Supports JPG, PNG, WebP, GIF</p>
        <input ref={inputRef} type="file" accept="image/*" onChange={onFile} style={{ display: 'none' }} />
      </div>

      {preview && (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
          <img src={preview} alt="Preview" style={{ maxWidth: '100%', maxHeight: 400, borderRadius: 12, border: '1px solid rgba(255,255,255,0.08)', display: 'block', margin: '0 auto 1.5rem' }} />
          <button onClick={process} disabled={processing} className="btn-primary" style={{ maxWidth: 320, margin: '0 auto', display: 'block' }}>
            {processing ? '⏳ Processing with AI Vision…' : '🚀 Process Image'}
          </button>
        </motion.div>
      )}

      {processing && <div className="loading"><p>Claude Vision is analysing your image…</p></div>}

      {result && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ marginTop: '2rem', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, padding: '1.75rem' }}>
          <h3 style={{ color: 'var(--indigo-light)', marginBottom: '1.25rem', fontSize: '1.05rem' }}>✨ Results</h3>

          {mode === 'handwriting' && result.text && <>
            <div style={{ background: 'rgba(0,0,0,0.25)', borderRadius: 12, padding: '1.25rem', marginBottom: '1rem' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.5rem' }}>Extracted Text</div>
              <p style={{ color: 'var(--text-primary)', lineHeight: 1.75 }}>{result.text}</p>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              {[{l:'Confidence',v:result.confidence},{l:'Language',v:result.language},{l:'Words',v:result.wordsDetected}].map(m => (
                <div key={m.l} style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 10, padding: '0.65rem 1rem', textAlign: 'center' }}>
                  <div style={{ color: 'var(--indigo-light)', fontWeight: 700 }}>{m.v}</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>{m.l}</div>
                </div>
              ))}
            </div>
          </>}

          {mode === 'diagram' && <>
            <div style={{ color: 'var(--indigo-light)', fontWeight: 700, marginBottom: '0.5rem' }}>Type: {result.type}</div>
            {result.description && <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', lineHeight: 1.7 }}>{result.description}</p>}
            {result.components?.length > 0 && <><div style={{ color: 'var(--text-muted)', fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.5rem' }}>Components</div><div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>{result.components.map((c: string,i: number) => <span key={i} className="tag tag-indigo">{c}</span>)}</div></>}
            {result.insights?.length > 0 && <ul style={{ listStyle: 'none' }}>{result.insights.map((ins: string, i: number) => <li key={i} style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', padding: '0.35rem 0', paddingLeft: '1.2rem', position: 'relative' }}><span style={{ position: 'absolute', left: 0, color: 'var(--cyan)' }}>›</span>{ins}</li>)}</ul>}
          </>}

          {mode === 'math' && <>
            {result.problem && <div style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.25)', borderRadius: 10, padding: '1rem', marginBottom: '1rem' }}><div style={{ color: 'var(--indigo-light)', fontWeight: 700, marginBottom: '0.35rem' }}>Problem</div><p style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{result.problem}</p></div>}
            {result.steps?.map((s: string, i: number) => <div key={i} style={{ padding: '0.75rem 1rem', marginBottom: '0.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: 10, borderLeft: '3px solid var(--indigo)', color: 'var(--text-secondary)', fontSize: '0.88rem' }}><strong style={{ color: 'var(--text-primary)' }}>Step {i+1}:</strong> {s}</div>)}
            {result.answer && <div style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: 10, padding: '1rem' }}><div style={{ color: '#34d399', fontWeight: 700 }}>✓ Answer: {result.answer}</div></div>}
          </>}

          {mode === 'screenshot' && <>
            {result.summary && <p style={{ color: 'var(--text-secondary)', marginBottom: '1.25rem', background: 'rgba(99,102,241,0.08)', borderRadius: 10, padding: '0.85rem', fontSize: '0.88rem' }}>{result.summary}</p>}
            {result.quiz?.map((q: any, i: number) => (
              <div key={i} style={{ background: 'rgba(0,0,0,0.2)', borderRadius: 12, padding: '1rem', marginBottom: '0.85rem' }}>
                <p style={{ color: 'var(--text-primary)', fontWeight: 600, marginBottom: '0.75rem', fontSize: '0.9rem' }}>{i+1}. {q.question}</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {q.options?.map((o: string, j: number) => <div key={j} style={{ padding: '0.55rem 0.85rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, color: 'var(--text-secondary)', fontSize: '0.85rem', cursor: 'pointer' }} onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(99,102,241,0.4)')} onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.07)')}><strong style={{ color: 'var(--indigo-light)' }}>{String.fromCharCode(65+j)}.</strong> {o}</div>)}
                </div>
              </div>
            ))}
          </>}
        </motion.div>
      )}
    </motion.div>
  );
};
export default MultimodalProcessor;
