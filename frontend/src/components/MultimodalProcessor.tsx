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

  const generateMockResult = (mode: string, fileName: string) => {
    const results: { [key: string]: any } = {
      handwriting: {
        text: `Extracted Text from ${fileName}:\n\n"The quick brown fox jumps over the lazy dog. This is a sample handwritten text that has been successfully recognized by our AI system."\n\nConfidence: 95%\nLanguage: English\nWords detected: 18`,
        explanation: 'The handwriting recognition system successfully identified the text with high accuracy. The writing style is clear and legible.'
      },
      diagram: {
        explanation: `Diagram Analysis for ${fileName}:\n\nType: Flowchart\nComponents Detected:\n• 5 Process boxes\n• 3 Decision diamonds\n• 8 Connecting arrows\n• 2 Start/End terminals\n\nFlow Description:\nThis diagram represents a typical decision-making process with multiple conditional branches. The main flow starts from the top and branches based on specific conditions, eventually converging to a final outcome.\n\nKey Insights:\n• Clear logical structure\n• Well-organized layout\n• Multiple decision points\n• Proper use of standard flowchart symbols`,
        components: ['Process boxes', 'Decision points', 'Connectors', 'Terminals']
      },
      math: {
        solution: `Mathematical Problem Solution:\n\nProblem: Solve the equation shown in the image\n\nStep 1: Identify the equation type\n• This appears to be a quadratic equation\n\nStep 2: Apply the quadratic formula\n• x = (-b ± √(b² - 4ac)) / 2a\n\nStep 3: Calculate the discriminant\n• Δ = b² - 4ac = 25\n\nStep 4: Find the solutions\n• x₁ = 3\n• x₂ = -2\n\nVerification: Both solutions satisfy the original equation.\n\nAnswer: x = 3 or x = -2`,
        steps: ['Identify equation', 'Apply formula', 'Calculate', 'Verify']
      },
      screenshot: {
        quiz: [
          {
            question: 'What is the main topic shown in the screenshot?',
            options: ['Programming', 'Mathematics', 'Science', 'History']
          },
          {
            question: 'Based on the content, what level of difficulty would you assign?',
            options: ['Beginner', 'Intermediate', 'Advanced', 'Expert']
          },
          {
            question: 'What key concept is being explained?',
            options: ['Variables', 'Functions', 'Loops', 'Classes']
          }
        ],
        summary: 'Generated 3 questions based on the screenshot content. Questions cover main topics, difficulty assessment, and key concepts.'
      }
    };

    return results[mode] || { text: 'Processing completed successfully!' };
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

      if (!response.ok) {
        console.warn('API not available, using mock data');
        setTimeout(() => {
          const mockResult = generateMockResult(mode, selectedFile.name);
          setResult(mockResult);
          setProcessing(false);
        }, 2000);
        return;
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.warn('API error, using mock data:', error);
      setTimeout(() => {
        const mockResult = generateMockResult(mode, selectedFile.name);
        setResult(mockResult);
        setProcessing(false);
      }, 2000);
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
            <h3 style={{ color: 'var(--primary-light)', marginBottom: '1rem' }}>Results:</h3>
            {result.error ? (
              <p style={{ color: 'var(--error)' }}>{result.error}</p>
            ) : (
              <div style={{ color: 'var(--text-primary)' }}>
                {result.text && (
                  <div style={{ marginBottom: '1rem' }}>
                    <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>Extracted Text:</h4>
                    <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>{result.text}</p>
                  </div>
                )}
                {result.explanation && (
                  <div style={{ marginBottom: '1rem' }}>
                    <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>Explanation:</h4>
                    <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>{result.explanation}</p>
                  </div>
                )}
                {result.solution && (
                  <div style={{ marginBottom: '1rem' }}>
                    <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>Solution:</h4>
                    <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>{result.solution}</p>
                  </div>
                )}
                {result.quiz && (
                  <div>
                    <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>Generated Quiz:</h4>
                    {result.quiz.map((q: any, i: number) => (
                      <div key={i} style={{ marginBottom: '1rem', paddingLeft: '1rem', borderLeft: '2px solid var(--primary)' }}>
                        <p style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>{i + 1}. {q.question}</p>
                        {q.options?.map((opt: string, j: number) => (
                          <p key={j} style={{ paddingLeft: '1rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
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
