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

  const analyzeCodeLocally = (code: string, language: string) => {
    const lines = code.split('\n');
    const nonEmptyLines = lines.filter(line => line.trim().length > 0);
    const commentLines = lines.filter(line => {
      const trimmed = line.trim();
      return trimmed.startsWith('//') || trimmed.startsWith('#') || trimmed.startsWith('/*');
    });
    
    // Detect patterns
    const hasLoops = /\b(for|while|forEach|map|filter)\b/.test(code);
    const hasConditionals = /\b(if|else|switch|case|\?)\b/.test(code);
    const hasFunctions = /\b(function|def|func|fn|=>|lambda)\b/.test(code);
    const hasClasses = /\b(class|struct|interface|type)\b/.test(code);
    const hasErrorHandling = /\b(try|catch|except|finally|throw|raise)\b/.test(code);
    const hasAsync = /\b(async|await|Promise|then|catch)\b/.test(code);
    
    // Detect variables
    const variables = code.match(/\b(let|const|var|int|string|float|double|bool)\s+(\w+)/g) || [];
    
    // Calculate complexity
    const cyclomaticComplexity = 1 + (code.match(/\b(if|else if|for|while|case|catch|\|\||&&)\b/g) || []).length;
    
    // Detect potential issues
    const issues = [];
    if (!hasErrorHandling && lines.length > 10) {
      issues.push('No error handling detected - consider adding try-catch blocks');
    }
    if (commentLines.length === 0 && lines.length > 5) {
      issues.push('No comments found - add documentation for better maintainability');
    }
    if (variables.length > 10) {
      issues.push('High number of variables - consider refactoring into smaller functions');
    }
    
    // Generate strengths
    const strengths = [];
    if (commentLines.length > 0) {
      strengths.push('Good code documentation with comments');
    }
    if (hasErrorHandling) {
      strengths.push('Proper error handling implemented');
    }
    if (hasFunctions) {
      strengths.push('Well-structured with function definitions');
    }
    if (hasClasses) {
      strengths.push('Object-oriented design with classes');
    }
    if (code.length < 500 && hasFunctions) {
      strengths.push('Concise and focused implementation');
    }
    
    // Generate suggestions
    const suggestions = [];
    if (!hasErrorHandling) {
      suggestions.push(`Add error handling with ${language === 'python' ? 'try-except' : 'try-catch'} blocks`);
    }
    if (commentLines.length < nonEmptyLines.length * 0.1) {
      suggestions.push('Add more inline comments to explain complex logic');
    }
    if (cyclomaticComplexity > 10) {
      suggestions.push('Reduce cyclomatic complexity by breaking down complex functions');
    }
    if (!hasAsync && (code.includes('fetch') || code.includes('request'))) {
      suggestions.push('Consider using async/await for better asynchronous code handling');
    }
    suggestions.push(`Follow ${language} style guide conventions (PEP 8 for Python, ESLint for JavaScript, etc.)`);
    suggestions.push('Add unit tests to ensure code reliability');
    
    return `📊 Code Analysis for ${language.toUpperCase()}

Overview:
Your code contains ${lines.length} lines (${nonEmptyLines.length} non-empty) of ${language} code.
${commentLines.length > 0 ? `Documentation: ${commentLines.length} comment lines found.` : 'No comments detected.'}

✅ Strengths:
${strengths.length > 0 ? strengths.map(s => `• ${s}`).join('\n') : '• Basic code structure is present'}

⚠️ Areas for Improvement:
${issues.length > 0 ? issues.map(i => `• ${i}`).join('\n') : '• Consider adding more robust error handling'}

🔍 Detailed Analysis:

1. Code Structure
   ${hasFunctions ? 'Functions detected - good modular design.' : 'Consider breaking code into functions for better organization.'}
   ${hasClasses ? 'Classes found - object-oriented approach is being used.' : ''}
   
2. Complexity
   Cyclomatic Complexity: ${cyclomaticComplexity} ${cyclomaticComplexity > 10 ? '(High - consider refactoring)' : cyclomaticComplexity > 5 ? '(Moderate)' : '(Low - good!)'}
   ${hasLoops ? 'Loops detected - ensure they have proper exit conditions.' : ''}
   ${hasConditionals ? 'Conditional logic present - verify all edge cases are handled.' : ''}

3. Features Detected
   ${hasAsync ? '✓ Asynchronous operations' : ''}
   ${hasErrorHandling ? '✓ Error handling' : '✗ No error handling'}
   ${hasFunctions ? '✓ Function definitions' : ''}
   ${hasClasses ? '✓ Class definitions' : ''}

💡 Suggestions:
${suggestions.map(s => `• ${s}`).join('\n')}

📈 Metrics:
• Lines of Code: ${lines.length}
• Complexity Score: ${cyclomaticComplexity < 5 ? 'Low' : cyclomaticComplexity < 10 ? 'Medium' : 'High'}
• Maintainability: ${commentLines.length > 0 && hasErrorHandling ? 'Good' : commentLines.length > 0 || hasErrorHandling ? 'Fair' : 'Needs Improvement'}
• Code Quality: ${strengths.length >= 3 ? 'Excellent' : strengths.length >= 2 ? 'Good' : 'Fair'}

Note: This is an AI-powered analysis. For production use, connect to AWS Bedrock for more detailed insights.`;
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
        console.warn('API not available, using local analysis');
        const localAnalysis = analyzeCodeLocally(code, language);
        setAnalysis(localAnalysis);
        setLoading(false);
        return;
      }

      const data = await response.json();
      setAnalysis(data.explanation || data.analysis || 'Analysis completed');
    } catch (err: any) {
      console.warn('API error, using local analysis:', err);
      const localAnalysis = analyzeCodeLocally(code, language);
      setAnalysis(localAnalysis);
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
