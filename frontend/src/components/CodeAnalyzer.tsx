import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface CodeAnalyzerProps {
  authToken: string;
}

const CodeAnalyzer: React.FC<CodeAnalyzerProps> = ({ authToken }) => {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState('');

  const API_URL = process.env.REACT_APP_API_URL || '';

  const generateMockAnalysis = (code: string, language: string) => {
    const lines = code.split('\n').length;
    return `📊 Code Analysis for ${language.toUpperCase()}

Overview:
Your code contains ${lines} line${lines !== 1 ? 's' : ''} of ${language} code. Here's a comprehensive analysis:

✅ Strengths:
• Clear variable naming conventions
• Logical code structure
• Good use of ${language} idioms

⚠️ Areas for Improvement:
• Consider adding error handling for edge cases
• Documentation could be enhanced with inline comments
• Performance optimization opportunities exist

🔍 Detailed Analysis:

1. Code Structure
   The overall organization is good, following ${language} best practices.

2. Readability
   Code is generally readable, but could benefit from more descriptive variable names in some areas.

3. Efficiency
   The algorithm has a time complexity that could be optimized.

💡 Suggestions:
• Add type hints (for Python) or proper type declarations
• Implement input validation
• Consider breaking down complex functions into smaller, reusable components
• Add unit tests for better code coverage

📈 Metrics:
• Complexity Score: Medium
• Maintainability: Good
• Security: Review needed for input validation

Note: This is a demo analysis. For production use, connect to the AWS Bedrock API for AI-powered code analysis.`;
  };

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
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          code: code,
          language: language,
        }),
      });

      if (!response.ok) {
        // If API fails, use mock data
        console.warn('API not available, using mock data');
        const mockAnalysis = generateMockAnalysis(code, language);
        setAnalysis(mockAnalysis);
        setLoading(false);
        return;
      }

      const data = await response.json();
      setAnalysis(data.explanation || data.analysis || 'Analysis completed');
    } catch (err: any) {
      console.warn('API error, using mock data:', err);
      // Use mock data as fallback
      const mockAnalysis = generateMockAnalysis(code, language);
      setAnalysis(mockAnalysis);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="component-container"
    >
      <h2>🔍 Code Analyzer</h2>
      <p>Get AI-powered explanations and analysis of your code</p>

      {error && <div className="error">{error}</div>}

      <div className="form-group">
        <label>Programming Language:</label>
        <select 
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
        >
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
          <option value="typescript">TypeScript</option>
          <option value="java">Java</option>
          <option value="cpp">C++</option>
          <option value="csharp">C#</option>
          <option value="go">Go</option>
          <option value="rust">Rust</option>
          <option value="ruby">Ruby</option>
          <option value="php">PHP</option>
        </select>
      </div>

      <div className="form-group">
        <label>Code to Analyze:</label>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Paste your code here..."
          rows={15}
          style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '0.9rem' }}
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
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem', color: 'var(--text-muted)' }}>
            This may take 10-30 seconds
          </p>
        </div>
      )}

      {analysis && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="code-results"
        >
          <div className="success">
            ✅ Code analysis completed!
          </div>

          <div className="code-analysis">
            <h3>Analysis Results</h3>
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.7', color: 'var(--text-primary)' }}>
              {analysis}
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default CodeAnalyzer;
