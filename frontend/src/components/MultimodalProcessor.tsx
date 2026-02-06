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

      const response = await fetch(`${process.env.REACT_APP_API_URL || ''}${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        body: formData
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: error instanceof Error ? error.message : 'Processing failed' });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}
    >
      <h2 style={{ color: '#00ffff', marginBottom: '2rem', fontSize: '2rem', textAlign: 'center' }}>
        🖼️ Multimodal AI Processor
      </h2>

      <div style={{
        background: 'rgba(0, 255, 255, 0.05)',
        border: '1px solid rgba(0, 255, 255, 0.2)',
        borderRadius: '16px',
        padding: '2rem'
      }}>
        {/* Mode Selection */}
        <div style={{ marginBottom: '2rem' }}>
          <h3 style={{ color: '#00ffff', marginBottom: '1rem' }}>Select Processing Mode:</h3>
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
                    ? 'linear-gradient(135deg, #00ffff 0%, #00cccc 100%)'
                    : 'rgba(0, 255, 255, 0.1)',
                  border: `1px solid ${mode === id ? '#00ffff' : 'rgba(0, 255, 255, 0.3)'}`,
                  color: mode === id ? '#000' : '#00ffff',
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
              display: 'inline-block',
              background: 'rgba(0, 255, 255, 0.2)',
              border: '2px dashed rgba(0, 255, 255, 0.5)',
              borderRadius: '12px',
              padding: '2rem',
              textAlign: 'center',
              cursor: 'pointer',
              width: '100%',
              transition: 'all 0.3s ease'
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📁</div>
            <p style={{ color: '#00ffff', fontSize: '1.1rem', marginBottom: '0.5rem' }}>
              Click to upload image
            </p>
            <p style={{ color: '#888', fontSize: '0.9rem' }}>
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
            <h3 style={{ color: '#00ffff', marginBottom: '1rem' }}>Preview:</h3>
            <img
              src={preview}
              alt="Preview"
              style={{
                maxWidth: '100%',
                maxHeight: '400px',
                borderRadius: '8px',
                border: '1px solid rgba(0, 255, 255, 0.3)'
              }}
            />
            <motion.button
              whileHover={{ scale: 1.05, boxShadow: '0 0 20px rgba(0, 255, 255, 0.5)' }}
              whileTap={{ scale: 0.95 }}
              onClick={processImage}
              disabled={processing}
              style={{
                background: 'linear-gradient(135deg, #00ffff 0%, #00cccc 100%)',
                border: 'none',
                color: '#000',
                padding: '1rem 2rem',
                borderRadius: '8px',
                cursor: processing ? 'not-allowed' : 'pointer',
                fontSize: '1rem',
                fontWeight: '600',
                marginTop: '1rem',
                opacity: processing ? 0.6 : 1
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
              background: 'rgba(0, 0, 0, 0.5)',
              border: '1px solid rgba(0, 255, 255, 0.3)',
              borderRadius: '12px',
              padding: '1.5rem'
            }}
          >
            <h3 style={{ color: '#00ffff', marginBottom: '1rem' }}>Results:</h3>
            {result.error ? (
              <p style={{ color: '#ff6b6b' }}>{result.error}</p>
            ) : (
              <div style={{ color: '#fff' }}>
                {result.text && (
                  <div style={{ marginBottom: '1rem' }}>
                    <h4 style={{ color: '#00ffff', marginBottom: '0.5rem' }}>Extracted Text:</h4>
                    <p style={{ whiteSpace: 'pre-wrap' }}>{result.text}</p>
                  </div>
                )}
                {result.explanation && (
                  <div style={{ marginBottom: '1rem' }}>
                    <h4 style={{ color: '#00ffff', marginBottom: '0.5rem' }}>Explanation:</h4>
                    <p style={{ whiteSpace: 'pre-wrap' }}>{result.explanation}</p>
                  </div>
                )}
                {result.solution && (
                  <div style={{ marginBottom: '1rem' }}>
                    <h4 style={{ color: '#00ffff', marginBottom: '0.5rem' }}>Solution:</h4>
                    <p style={{ whiteSpace: 'pre-wrap' }}>{result.solution}</p>
                  </div>
                )}
                {result.quiz && (
                  <div>
                    <h4 style={{ color: '#00ffff', marginBottom: '0.5rem' }}>Generated Quiz:</h4>
                    {result.quiz.map((q: any, i: number) => (
                      <div key={i} style={{ marginBottom: '1rem', paddingLeft: '1rem' }}>
                        <p style={{ fontWeight: 'bold' }}>{i + 1}. {q.question}</p>
                        {q.options?.map((opt: string, j: number) => (
                          <p key={j} style={{ paddingLeft: '1rem', color: '#888' }}>
                            {String.fromCharCode(65 + j)}. {opt}
                          </p>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default MultimodalProcessor;
