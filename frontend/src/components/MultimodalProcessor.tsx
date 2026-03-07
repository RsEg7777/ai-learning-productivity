import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface MultimodalProcessorProps {
  authToken: string;
}

const MultimodalProcessor: React.FC<MultimodalProcessorProps> = ({ authToken }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>('');
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [mode, setMode] = useState<'handwriting' | 'diagram' | 'math' | 'screenshot'>('handwriting');

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const processImage = async () => {
    if (!selectedFile) return;

    setProcessing(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('image', selectedFile);
      formData.append('mode', mode);

      const endpoint = {
        handwriting: '/multimodal/process-handwriting',
        diagram: '/multimodal/understand-diagram',
        math: '/multimodal/solve-math',
        screenshot: '/multimodal/screenshot-to-quiz'
      }[mode];

      const apiUrl = process.env.REACT_APP_API_URL || '';
      const response = await fetch(`${apiUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to process image');
      }

      const data = await response.json();
      
      if (data.success) {
        setResult(data);
      } else {
        setResult({ error: 'Processing failed. Please try again.' });
      }
      setProcessing(false);
    } catch (error) {
      console.error('Error processing image:', error);
      setResult({ error: 'Failed to process image. Please check your connection and try again.' });
      setProcessing(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}
    >
      <h2 style={{ color: 'var(--primary-light)', marginBottom: '2rem', fontSize: '2rem', textAlign: 'center' }}>
        🖼️ Multimodal AI Processor
      </h2>

      <div style={{
        background: 'rgba(99, 102, 241, 0.05)',
        border: '1px solid var(--border)',
        borderRadius: '16px',
        padding: '2rem'
      }}>
        {/* Mode Selection */}
        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>Select Processing Mode:</h3>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {[
              { id: 'handwriting', icon: '✍️', label: 'Handwriting OCR' },
              { id: 'diagram', icon: '📊', label: 'Diagram Analysis' },
              { id: 'math', icon: '🔢', label: 'Math Solver' },
              { id: 'screenshot', icon: '📸', label: 'Screenshot to Quiz' }
            ].map(({ id, icon, label }) => (
              <motion.button
                key={id}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setMode(id as any)}
                style={{
                  background: mode === id 
                    ? 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)'
                    : 'var(--bg-card)',
                  border: `1px solid ${mode === id ? 'var(--primary)' : 'var(--border)'}`,
                  color: mode === id ? 'white' : 'var(--text-primary)',
                  padding: '0.8rem 1.5rem',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.95rem',
                  fontWeight: '600'
                }}
              >
                {icon} {label}
              </motion.button>
            ))}
          </div>
        </div>

        {/* File Upload */}
        <div style={{ marginBottom: '2rem' }}>
          <label
            htmlFor="file-upload"
            style={{
              display: 'block',
              background: 'var(--bg-dark)',
              border: '2px dashed var(--border)',
              borderRadius: '12px',
              padding: '2rem',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--primary)'}
            onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border)'}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📁</div>
            <p style={{ color: 'var(--primary-light)', fontSize: '1.1rem', marginBottom: '0.5rem' }}>
              Click to upload image
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Supports: JPG, PNG, PDF
            </p>
            <input
              id="file-upload"
              type="file"
              accept="image/*,.pdf"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </label>
        </div>

        {/* Preview */}
        {preview && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            style={{ marginBottom: '2rem' }}
          >
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>Preview:</h3>
            <img
              src={preview}
              alt="Preview"
              style={{
                maxWidth: '100%',
                maxHeight: '400px',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                display: 'block',
                margin: '0 auto'
              }}
            />
            <motion.button
              whileHover={{ scale: 1.05, boxShadow: '0 0 20px rgba(99, 102, 241, 0.5)' }}
              whileTap={{ scale: 0.95 }}
              onClick={processImage}
              disabled={processing}
              style={{
                background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)',
                border: 'none',
                color: 'white',
                padding: '1rem 2rem',
                borderRadius: '8px',
                cursor: processing ? 'not-allowed' : 'pointer',
                fontSize: '1rem',
                fontWeight: '600',
                marginTop: '1rem',
                opacity: processing ? 0.6 : 1,
                display: 'block',
                margin: '1rem auto 0'
              }}
            >
              {processing ? '⏳ Processing...' : '🚀 Process Image'}
            </motion.button>
          </motion.div>
        )}

        {/* Results */}
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              background: 'var(--bg-dark)',
              border: '1px solid var(--border)',
              borderRadius: '12px',
              padding: '1.5rem'
            }}
          >
            <h3 style={{ color: 'var(--primary-light)', marginBottom: '1.5rem', fontSize: '1.3rem' }}>
              ✨ Results
            </h3>

            {/* Handwriting OCR Results */}
            {mode === 'handwriting' && result.text && (
              <div>
                <div style={{ 
                  marginBottom: '1.5rem',
                  padding: '1.5rem',
                  background: 'var(--bg-card)',
                  borderRadius: '10px',
                  border: '1px solid var(--primary)'
                }}>
                  <h4 style={{ color: 'var(--primary)', marginBottom: '1rem', fontSize: '1.1rem' }}>
                    📝 Extracted Text
                  </h4>
                  <p style={{ fontSize: '1.05rem', lineHeight: '1.8', color: 'var(--text-primary)', marginBottom: '1rem' }}>
                    {result.text}
                  </p>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                    <div style={{ padding: '0.75rem', background: 'var(--bg-dark)', borderRadius: '8px' }}>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Confidence</div>
                      <div style={{ color: 'var(--success)', fontSize: '1.2rem', fontWeight: 'bold' }}>{result.confidence}</div>
                    </div>
                    <div style={{ padding: '0.75rem', background: 'var(--bg-dark)', borderRadius: '8px' }}>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Language</div>
                      <div style={{ color: 'var(--primary)', fontSize: '1.2rem', fontWeight: 'bold' }}>{result.language}</div>
                    </div>
                    <div style={{ padding: '0.75rem', background: 'var(--bg-dark)', borderRadius: '8px' }}>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Words</div>
                      <div style={{ color: 'var(--accent)', fontSize: '1.2rem', fontWeight: 'bold' }}>{result.wordsDetected}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Diagram Analysis Results */}
            {mode === 'diagram' && result.type && (
              <div>
                <div style={{ 
                  marginBottom: '1rem',
                  padding: '1.5rem',
                  background: 'var(--bg-card)',
                  borderRadius: '10px',
                  border: '1px solid var(--primary)'
                }}>
                  <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>📊 Diagram Type</h4>
                  <p style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{result.type}</p>
                </div>
                <div style={{ 
                  marginBottom: '1rem',
                  padding: '1.5rem',
                  background: 'var(--bg-card)',
                  borderRadius: '10px'
                }}>
                  <h4 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>🔍 Components Detected</h4>
                  <ul style={{ listStyle: 'none', padding: 0 }}>
                    {result.components.map((comp: string, i: number) => (
                      <li key={i} style={{ padding: '0.5rem 0', color: 'var(--text-primary)', fontSize: '1rem' }}>
                        • {comp}
                      </li>
                    ))}
                  </ul>
                </div>
                <div style={{ 
                  marginBottom: '1rem',
                  padding: '1.5rem',
                  background: 'var(--bg-card)',
                  borderRadius: '10px'
                }}>
                  <h4 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>💡 Description</h4>
                  <p style={{ lineHeight: '1.8', color: 'var(--text-primary)' }}>{result.description}</p>
                </div>
                <div style={{ 
                  padding: '1.5rem',
                  background: 'var(--bg-card)',
                  borderRadius: '10px'
                }}>
                  <h4 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>✨ Key Insights</h4>
                  <ul style={{ listStyle: 'none', padding: 0 }}>
                    {result.insights.map((insight: string, i: number) => (
                      <li key={i} style={{ padding: '0.5rem 0', color: 'var(--text-primary)' }}>
                        ✓ {insight}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Math Solver Results */}
            {mode === 'math' && result.problem && (
              <div>
                <div style={{ 
                  marginBottom: '1rem',
                  padding: '1.5rem',
                  background: 'var(--bg-card)',
                  borderRadius: '10px',
                  border: '1px solid var(--primary)'
                }}>
                  <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>🔢 Problem</h4>
                  <p style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>{result.problem}</p>
                </div>
                <div style={{ 
                  marginBottom: '1rem',
                  padding: '1.5rem',
                  background: 'var(--bg-card)',
                  borderRadius: '10px'
                }}>
                  <h4 style={{ color: 'var(--primary)', marginBottom: '1rem' }}>📝 Solution Steps</h4>
                  {result.steps.map((step: string, i: number) => (
                    <div key={i} style={{ 
                      padding: '1rem',
                      marginBottom: '0.75rem',
                      background: 'var(--bg-dark)',
                      borderRadius: '8px',
                      borderLeft: '3px solid var(--primary)'
                    }}>
                      <p style={{ color: 'var(--text-primary)', lineHeight: '1.6' }}>{step}</p>
                    </div>
                  ))}
                </div>
                <div style={{ 
                  marginBottom: '1rem',
                  padding: '1.5rem',
                  background: 'var(--bg-card)',
                  borderRadius: '10px',
                  border: '2px solid var(--success)'
                }}>
                  <h4 style={{ color: 'var(--success)', marginBottom: '0.5rem' }}>✅ Answer</h4>
                  <p style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>{result.answer}</p>
                </div>
                <div style={{ 
                  padding: '1rem',
                  background: 'rgba(16, 185, 129, 0.1)',
                  borderRadius: '8px',
                  border: '1px solid var(--success)'
                }}>
                  <p style={{ color: 'var(--success)', fontSize: '0.95rem' }}>
                    ✓ {result.verification}
                  </p>
                </div>
              </div>
            )}

            {/* Screenshot to Quiz Results */}
            {mode === 'screenshot' && result.quiz && (
              <div>
                <div style={{ marginBottom: '1.5rem', padding: '1rem', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '8px' }}>
                  <p style={{ color: 'var(--primary)', fontSize: '1rem' }}>
                    📝 {result.summary}
                  </p>
                </div>
                {result.quiz.map((q: any, i: number) => (
                  <div 
                    key={i} 
                    style={{ 
                      marginBottom: '1.5rem', 
                      padding: '1.5rem',
                      background: 'var(--bg-card)',
                      borderRadius: '10px',
                      border: '1px solid var(--border)'
                    }}
                  >
                    <p style={{ 
                      fontWeight: 'bold', 
                      marginBottom: '1rem',
                      fontSize: '1.05rem',
                      color: 'var(--text-primary)'
                    }}>
                      {i + 1}. {q.question}
                    </p>
                    <div style={{ display: 'grid', gap: '0.75rem' }}>
                      {q.options?.map((opt: string, j: number) => (
                        <div 
                          key={j} 
                          style={{ 
                            padding: '1rem',
                            background: 'var(--bg-dark)',
                            border: '1px solid var(--border)',
                            borderRadius: '8px',
                            color: 'var(--text-primary)',
                            fontSize: '0.95rem',
                            cursor: 'pointer',
                            transition: 'all 0.3s'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.borderColor = 'var(--primary)';
                            e.currentTarget.style.background = 'rgba(99, 102, 241, 0.1)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.borderColor = 'var(--border)';
                            e.currentTarget.style.background = 'var(--bg-dark)';
                          }}
                        >
                          <strong style={{ color: 'var(--primary)' }}>{String.fromCharCode(65 + j)}.</strong> {opt}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default MultimodalProcessor;
