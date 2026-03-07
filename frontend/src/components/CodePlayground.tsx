import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface CodePlaygroundProps {
  authToken: string;
}

const CodePlayground: React.FC<CodePlaygroundProps> = ({ authToken }) => {
  const [code, setCode] = useState('# Write your code here\nprint("Hello, World!")');
  const [language, setLanguage] = useState('python');
  const [output, setOutput] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [aiSuggestion, setAiSuggestion] = useState('');
  const [userInput, setUserInput] = useState('');
  const [showInputDialog, setShowInputDialog] = useState(false);

  const languages = [
    'python', 'javascript', 'java', 'cpp', 'c', 'go', 
    'rust', 'ruby', 'php', 'typescript'
  ];

  // Check if code requires input
  const requiresInput = (code: string, lang: string): boolean => {
    const inputPatterns: { [key: string]: RegExp[] } = {
      python: [/input\s*\(/],
      javascript: [/prompt\s*\(/, /readline\s*\(/],
      java: [/Scanner/, /BufferedReader/, /\.nextLine\(/, /\.nextInt\(/],
      cpp: [/cin\s*>>/, /scanf\s*\(/],
      c: [/scanf\s*\(/, /gets\s*\(/],
      go: [/fmt\.Scan/, /bufio\.NewReader/],
      ruby: [/gets/, /STDIN\.gets/],
      php: [/fgets\s*\(STDIN/],
    };

    const patterns = inputPatterns[lang] || [];
    return patterns.some(pattern => pattern.test(code));
  };

  const executeCode = async () => {
    // Check if code requires input
    if (requiresInput(code, language) && !userInput && !showInputDialog) {
      setShowInputDialog(true);
      return;
    }

    setIsExecuting(true);
    setOutput('Executing code...');
    setAiSuggestion('');
    setShowInputDialog(false);
    
    const apiUrl = process.env.REACT_APP_API_URL || '';
    
    try {
      const response = await fetch(`${apiUrl}/playground/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ 
          code, 
          language,
          input: userInput || undefined
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setOutput(data.output || 'Code executed successfully!');
        if (data.ai_suggestion) {
          setAiSuggestion(data.ai_suggestion);
        }
      } else {
        setOutput(`Error: ${data.error || 'Execution failed'}`);
        if (data.ai_explanation) {
          setAiSuggestion(`💡 AI Help: ${data.ai_explanation}`);
        }
      }
      setIsExecuting(false);
    } catch (error) {
      console.error('API error:', error);
      setOutput(`Error: Unable to execute code. Please check your connection and try again.`);
      setIsExecuting(false);
    }
  };

  const getAiCompletion = async () => {
    const apiUrl = process.env.REACT_APP_API_URL || '';
    
    try {
      const response = await fetch(`${apiUrl}/code/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ code, language })
      });

      const data = await response.json();
      
      if (data.success && data.analysis) {
        const analysis = data.analysis;
        let suggestionText = `💡 AI Code Analysis:\n\n`;
        
        if (analysis.explanation) {
          suggestionText += `${analysis.explanation}\n\n`;
        }
        
        if (analysis.improvements && analysis.improvements.length > 0) {
          suggestionText += `🔧 Suggested Improvements:\n`;
          analysis.improvements.slice(0, 3).forEach((imp: any, i: number) => {
            suggestionText += `${i + 1}. ${imp.title}: ${imp.description}\n`;
          });
          suggestionText += `\n`;
        }
        
        if (analysis.issues && analysis.issues.length > 0) {
          suggestionText += `⚠️ Issues Found:\n`;
          analysis.issues.slice(0, 3).forEach((issue: any, i: number) => {
            suggestionText += `${i + 1}. [${issue.severity}] ${issue.message}\n`;
          });
          suggestionText += `\n`;
        }
        
        if (analysis.best_practices && analysis.best_practices.length > 0) {
          suggestionText += `✨ Best Practices:\n`;
          analysis.best_practices.slice(0, 3).forEach((bp: string, i: number) => {
            suggestionText += `• ${bp}\n`;
          });
        }
        
        setAiSuggestion(suggestionText);
      }
    } catch (error) {
      console.error('Error getting AI suggestions:', error);
      setAiSuggestion('Unable to get AI suggestions. Please try again.');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}
    >
      <div style={{ 
        background: 'rgba(99, 102, 241, 0.05)', 
        border: '1px solid var(--border)',
        borderRadius: '12px',
        padding: '2rem',
        marginBottom: '2rem'
      }}>
        <h2 style={{ color: 'var(--primary-light)', marginBottom: '1.5rem', fontSize: '1.8rem' }}>
          💻 Interactive Code Playground
        </h2>
        
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ color: 'var(--text-primary)', marginRight: '1rem', fontWeight: 600 }}>Language:</label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            style={{
              background: 'var(--bg-dark)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
              padding: '0.5rem 1rem',
              borderRadius: '8px',
              fontSize: '1rem',
              cursor: 'pointer'
            }}
          >
            {languages.map(lang => (
              <option key={lang} value={lang}>
                {lang.toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Write your code here..."
          style={{
            width: '100%',
            minHeight: '300px',
            background: 'var(--bg-darker)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '1rem',
            color: 'var(--text-primary)',
            fontSize: '0.95rem',
            fontFamily: 'JetBrains Mono, monospace',
            resize: 'vertical',
            marginBottom: '1rem'
          }}
        />

        {/* Input Dialog */}
        {showInputDialog && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            style={{
              background: 'rgba(99, 102, 241, 0.1)',
              border: '1px solid var(--primary)',
              borderRadius: '8px',
              padding: '1rem',
              marginBottom: '1rem'
            }}
          >
            <label style={{ color: 'var(--primary-light)', fontWeight: 600, display: 'block', marginBottom: '0.5rem' }}>
              📥 Your code requires input. Enter values below (one per line):
            </label>
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Enter input values here...\nExample:\nJohn\n25\nNew York"
              rows={5}
              style={{
                width: '100%',
                background: 'var(--bg-darker)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '0.75rem',
                color: 'var(--text-primary)',
                fontSize: '0.95rem',
                fontFamily: 'JetBrains Mono, monospace',
                resize: 'vertical',
                marginBottom: '0.75rem'
              }}
            />
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={executeCode}
                style={{
                  background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)',
                  border: 'none',
                  color: 'white',
                  padding: '0.6rem 1.5rem',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: '600'
                }}
              >
                ▶️ Run with Input
              </motion.button>
              <button
                onClick={() => setShowInputDialog(false)}
                style={{
                  background: 'var(--bg-dark)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                  padding: '0.6rem 1.5rem',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.9rem'
                }}
              >
                Cancel
              </button>
            </div>
          </motion.div>
        )}

        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <motion.button
            whileHover={{ scale: 1.05, boxShadow: '0 0 20px rgba(99, 102, 241, 0.5)' }}
            whileTap={{ scale: 0.95 }}
            onClick={executeCode}
            disabled={isExecuting}
            style={{
              background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)',
              border: 'none',
              color: 'white',
              padding: '0.8rem 2rem',
              borderRadius: '8px',
              cursor: isExecuting ? 'not-allowed' : 'pointer',
              fontSize: '1rem',
              fontWeight: '600',
              opacity: isExecuting ? 0.6 : 1
            }}
          >
            {isExecuting ? '⏳ Executing...' : '▶️ Run Code'}
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05, boxShadow: '0 0 20px rgba(139, 92, 246, 0.5)' }}
            whileTap={{ scale: 0.95 }}
            onClick={getAiCompletion}
            style={{
              background: 'rgba(139, 92, 246, 0.2)',
              border: '1px solid var(--secondary)',
              color: 'var(--secondary)',
              padding: '0.8rem 2rem',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: '600'
            }}
          >
            🤖 AI Suggestions
          </motion.button>

          {userInput && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                setUserInput('');
                setShowInputDialog(false);
              }}
              style={{
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid #ef4444',
                color: '#ef4444',
                padding: '0.8rem 1.5rem',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '1rem',
                fontWeight: '600'
              }}
            >
              🗑️ Clear Input
            </motion.button>
          )}
        </div>

        {userInput && !showInputDialog && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid #10b981',
              borderRadius: '8px',
              padding: '0.75rem 1rem',
              marginBottom: '1rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <span style={{ fontSize: '1.2rem' }}>✅</span>
            <span style={{ color: '#10b981', fontSize: '0.9rem', fontWeight: '600' }}>
              Input provided ({userInput.split('\n').filter(l => l.trim()).length} line(s))
            </span>
          </motion.div>
        )}

        {output && (
              fontWeight: '600',
        {output && (
          <div style={{
            background: 'var(--bg-darker)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1rem'
          }}>
            <h3 style={{ color: 'var(--primary-light)', marginBottom: '0.5rem' }}>Output:</h3>
            <pre style={{ 
              color: 'var(--text-primary)', 
              margin: 0, 
              whiteSpace: 'pre-wrap',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '0.9rem'
            }}>
              {output}
            </pre>
          </div>
        )}

        {aiSuggestion && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              background: 'rgba(139, 92, 246, 0.1)',
              border: '1px solid var(--secondary)',
              borderRadius: '8px',
              padding: '1rem'
            }}
          >
            <pre style={{ 
              color: 'var(--secondary)', 
              margin: 0, 
              whiteSpace: 'pre-wrap',
              fontFamily: 'Inter, sans-serif',
              fontSize: '0.9rem'
            }}>
              {aiSuggestion}
            </pre>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default CodePlayground;
