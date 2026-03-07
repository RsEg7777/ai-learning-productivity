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
        throw new Error('Failed to analyze code');
      }

      const data = await response.json();
      
      if (data.success && data.analysis) {
        const analysisData = data.analysis;
        let analysisText = `📊 Code Analysis for ${language.toUpperCase()}\n\n`;
        
        if (analysisData.explanation) {
          analysisText += `Overview:\n${analysisData.explanation}\n\n`;
        }
        
        if (analysisData.issues && analysisData.issues.length > 0) {
          analysisText += `⚠️ Issues Found:\n`;
          analysisData.issues.forEach((issue: any, i: number) => {
            analysisText += `${i + 1}. [${issue.severity}] Line ${issue.line}: ${issue.message}\n`;
            if (issue.suggestion) {
              analysisText += `   Suggestion: ${issue.suggestion}\n`;
            }
          });
          analysisText += `\n`;
        }
        
        if (analysisData.improvements && analysisData.improvements.length > 0) {
          analysisText += `🔧 Suggested Improvements:\n`;
          analysisData.improvements.forEach((imp: any, i: number) => {
            analysisText += `${i + 1}. ${imp.title}\n`;
            analysisText += `   ${imp.description}\n`;
            if (imp.benefit) {
              analysisText += `   Benefit: ${imp.benefit}\n`;
            }
          });
          analysisText += `\n`;
        }
        
        if (analysisData.complexity) {
          analysisText += `📈 Complexity Metrics:\n`;
          analysisText += `• Cyclomatic Complexity: ${analysisData.complexity.cyclomatic}\n`;
          analysisText += `• Cognitive Complexity: ${analysisData.complexity.cognitive}\n`;
          analysisText += `• Lines of Code: ${analysisData.complexity.lines_of_code}\n`;
          analysisText += `• Maintainability Index: ${analysisData.complexity.maintainability_index}\n\n`;
        }
        
        if (analysisData.best_practices && analysisData.best_practices.length > 0) {
          analysisText += `✨ Best Practices:\n`;
          analysisData.best_practices.forEach((bp: string) => {
            analysisText += `• ${bp}\n`;
          });
        }
        
        setAnalysis(analysisText);
      } else {
        setAnalysis(data.explanation || data.analysis || 'Analysis completed');
      }
    } catch (err: any) {
      console.error('Error analyzing code:', err);
      setError('Failed to analyze code. Please check your connection and try again.');
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
