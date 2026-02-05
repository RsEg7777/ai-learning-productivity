import React, { useState } from 'react';

interface CodeAnalyzerProps {
  authToken: string;
}

const CodeAnalyzer: React.FC<CodeAnalyzerProps> = ({ authToken }) => {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState('');

  const API_URL = 'https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev';

  const handleAnalyze = async () => {
    if (!code.trim()) {
      setError('Please enter some code to analyze');
      return;
    }

    setLoading(true);
    setError('');
    setAnalysis('');

    try {
      const response = await fetch(`${API_URL}/code/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authToken,
        },
        body: JSON.stringify({
          code: code,
          language: language,
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      setAnalysis(data.explanation || data.analysis || 'Analysis completed');
    } catch (err: any) {
      setError(err.message || 'Failed to analyze code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="component-container">
      <h2>💻 Code Analyzer</h2>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Get AI-powered explanations and analysis of your code.
      </p>

      {error && <div className="error">{error}</div>}

      <div className="form-group">
        <label>Programming Language:</label>
        <select 
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          style={{ 
            width: '100%', 
            padding: '1rem', 
            border: '2px solid #e0e0e0', 
            borderRadius: '8px',
            fontSize: '1rem'
          }}
        >
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
          <option value="typescript">TypeScript</option>
          <option value="java">Java</option>
          <option value="cpp">C++</option>
          <option value="csharp">C#</option>
          <option value="go">Go</option>
          <option value="rust">Rust</option>
        </select>
      </div>

      <div className="form-group">
        <label>Code to Analyze:</label>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Paste your code here..."
          rows={12}
          style={{ fontFamily: 'monospace', fontSize: '0.95rem' }}
        />
      </div>

      <button 
        className="btn-primary" 
        onClick={handleAnalyze}
        disabled={loading}
      >
        {loading ? '🤖 Analyzing Code...' : '✨ Analyze Code'}
      </button>

      {loading && (
        <div className="loading">
          <p>AI is analyzing your code...</p>
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>This may take 10-30 seconds</p>
        </div>
      )}

      {analysis && (
        <div className="code-results">
          <div className="success">
            ✅ Code analysis completed!
          </div>

          <div className="code-analysis">
            <h3 style={{ color: '#667eea', marginBottom: '1rem' }}>Analysis Results</h3>
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', color: '#333' }}>
              {analysis}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CodeAnalyzer;
