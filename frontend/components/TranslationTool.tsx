'use client';
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import VoiceInput from './VoiceInput';

interface TranslationToolProps { authToken: string; }

const LANGUAGES = [
  { id: 'hindi',     label: 'हिन्दी',    name: 'Hindi',     flag: '🇮🇳' },
  { id: 'hinglish',  label: 'Hinglish', name: 'Hinglish',  flag: '🇮🇳' },
  { id: 'tamil',     label: 'தமிழ்',    name: 'Tamil',     flag: '🇮🇳' },
  { id: 'tanglish',  label: 'Tanglish', name: 'Tanglish',  flag: '🇮🇳' },
  { id: 'telugu',    label: 'తెలుగు',   name: 'Telugu',    flag: '🇮🇳' },
  { id: 'bengali',   label: 'বাংলা',    name: 'Bengali',   flag: '🇮🇳' },
  { id: 'marathi',   label: 'मराठी',    name: 'Marathi',   flag: '🇮🇳' },
  { id: 'gujarati',  label: 'ગુજરાતી',  name: 'Gujarati',  flag: '🇮🇳' },
  { id: 'kannada',   label: 'ಕನ್ನಡ',    name: 'Kannada',   flag: '🇮🇳' },
  { id: 'malayalam', label: 'മലയാളം',   name: 'Malayalam', flag: '🇮🇳' },
  { id: 'punjabi',   label: 'ਪੰਜਾਬੀ',   name: 'Punjabi',   flag: '🇮🇳' },
  { id: 'odia',      label: 'ଓଡ଼ିଆ',    name: 'Odia',      flag: '🇮🇳' },
  { id: 'urdu',      label: 'اردو',     name: 'Urdu',      flag: '🇵🇰' },
  { id: 'assamese',  label: 'অসমীয়া',  name: 'Assamese',  flag: '🇮🇳' },
  { id: 'sanskrit',  label: 'संस्कृत',  name: 'Sanskrit',  flag: '🇮🇳' },
];

const TranslationTool: React.FC<TranslationToolProps> = ({ authToken }) => {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || '';
  const [text, setText] = useState('');
  const [targetLang, setTargetLang] = useState('hindi');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);

  const handleVoice = (t: string) => setText(p => p + (p.endsWith(' ') || !p ? '' : ' ') + t);

  const translate = async () => {
    if (!text.trim()) { setError('Please enter text to translate'); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await fetch(`${API_URL}/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` },
        body: JSON.stringify({ text, target_language: targetLang, source_language: 'english' }),
      });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Translation failed'); }
      const data = await res.json();
      setResult(data);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const selectedLang = LANGUAGES.find(l => l.id === targetLang);

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="component-container">
      <h2>🌍 Multilingual Translation</h2>
      <p>Translate educational content into 15 Indian languages — including code-mixed variants like Hinglish and Tanglish — powered by Amazon Bedrock Nova Pro</p>

      {error && <div className="error">⚠️ {error}</div>}

      {/* Language grid */}
      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', color: 'var(--text-secondary)', fontWeight: 600, fontSize: '.78rem', textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: '.75rem' }}>
          Target Language
        </label>
        <div style={{ display: 'flex', gap: '.5rem', flexWrap: 'wrap' }}>
          {LANGUAGES.map(lang => (
            <motion.button key={lang.id} whileHover={{ scale: 1.05 }} whileTap={{ scale: .95 }}
              onClick={() => setTargetLang(lang.id)}
              style={{
                padding: '.45rem .9rem', borderRadius: 'var(--r-full)', cursor: 'pointer',
                background: targetLang === lang.id ? 'linear-gradient(135deg,var(--indigo),var(--violet))' : 'var(--bg-glass)',
                border: `1px solid ${targetLang === lang.id ? 'transparent' : 'var(--border-subtle)'}`,
                color: targetLang === lang.id ? '#fff' : 'var(--text-secondary)',
                fontSize: '.82rem', fontWeight: 600, backdropFilter: 'blur(8px)',
                boxShadow: targetLang === lang.id ? '0 0 16px var(--glow-primary)' : 'none',
                transition: 'all .15s ease',
              }}>
              {lang.flag} {lang.name}
              <span style={{ opacity: .7, marginLeft: '.3rem', fontFamily: 'var(--font-sans)' }}>({lang.label})</span>
            </motion.button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
        {/* Input */}
        <div>
          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '.5rem' }}>
              🇬🇧 English Source
              <VoiceInput onTranscript={handleVoice} disabled={loading} />
            </label>
            <textarea value={text} onChange={e => setText(e.target.value)} rows={10}
              placeholder="Type or dictate English text to translate..." />
          </div>
        </div>

        {/* Output */}
        <div>
          <label style={{ display: 'block', color: 'var(--text-secondary)', fontWeight: 600, fontSize: '.78rem', textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: '.45rem' }}>
            {selectedLang?.flag} {selectedLang?.name} Translation
          </label>
          <div style={{
            minHeight: '220px', padding: '.75rem 1rem',
            background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.2)',
            borderRadius: 'var(--r-md)', position: 'relative',
          }}>
            {loading && (
              <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '.75rem' }}>
                <div style={{ width: 32, height: 32, border: '2px solid rgba(99,102,241,0.2)', borderTopColor: 'var(--indigo)', borderRadius: '50%', animation: 'spin .7s linear infinite' }} />
                <p style={{ color: 'var(--text-muted)', fontSize: '.82rem' }}>Translating...</p>
              </div>
            )}
            {result?.translated ? (
              <p style={{ color: 'var(--text-primary)', lineHeight: 1.9, fontSize: '.95rem', direction: targetLang === 'urdu' ? 'rtl' : 'ltr' }}>
                {result.translated}
              </p>
            ) : !loading && (
              <p style={{ color: 'var(--text-muted)', fontSize: '.875rem' }}>Translation will appear here...</p>
            )}
          </div>
          {result?.translated && (
            <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: .97 }}
              onClick={() => navigator.clipboard.writeText(result.translated)}
              style={{ marginTop: '.5rem', padding: '.4rem .9rem', background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 'var(--r-sm)', color: 'var(--indigo-light)', fontSize: '.78rem', fontWeight: 600, cursor: 'pointer' }}>
              📋 Copy Translation
            </motion.button>
          )}
        </div>
      </div>

      <button className="btn-primary" onClick={translate} disabled={loading} style={{ marginTop: '1rem' }}>
        {loading ? `🤖 Translating to ${selectedLang?.name}...` : `✨ Translate to ${selectedLang?.name}`}
      </button>

      {/* Info cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: '.75rem', marginTop: '1.5rem' }}>
        {[
          { icon: '🎓', title: 'Educational Focus', desc: 'Preserves technical terms in English while explaining in the target language' },
          { icon: '🔀', title: 'Code-Mixed Support', desc: 'Hinglish and Tanglish — natural, conversational mixed-language output' },
          { icon: '⚡', title: 'Real-time AI', desc: 'Powered by Amazon Bedrock Nova Pro with contextual understanding' },
        ].map((c, i) => (
          <div key={i} style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--r-md)' }}>
            <span style={{ fontSize: '1.5rem' }}>{c.icon}</span>
            <p style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '.85rem', marginTop: '.4rem' }}>{c.title}</p>
            <p style={{ color: 'var(--text-muted)', fontSize: '.78rem', marginTop: '.25rem', lineHeight: 1.5 }}>{c.desc}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
};
export default TranslationTool;
