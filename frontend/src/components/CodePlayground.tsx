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

  const languages = [
    'python', 'javascript', 'java', 'cpp', 'c', 'go', 
    'rust', 'ruby', 'php', 'typescript'
  ];

  const executeCode = async () => {
    setIsExecuting(true);
    setOutput('Executing code...');
    
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || ''}/playground/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ code, language })
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
    } catch (error) {
      setOutput(`Error: ${error instanceof Error ? error.message : 'Failed to execute code'}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const getAiCompletion = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || ''}/playground/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ code, language })
      });

      const data = await response.json();
      if (data.completion) {
        setAiSuggestion(`💡 AI Suggestion:\n${data.completion}`);
      }
    } catch (error) {
      console.error('Failed to get AI completion:', error);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}
    >
      <div style={{ 
        background: 'rgba(0, 255, 255, 0.05)', 
        border: '1px solid rgba(0, 255, 255, 0.2)',
        borderRadius: '12px',
        padding: '2rem',
        marginBottom: '2rem'
      }}>
        <h2 style={{ color: '#00ffff', marginBottom: '1.5rem', fontSize: '1.8rem' }}>
          💻 Interactive Code Playground
        </h2>
        
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ color: '#00ffff', marginRight: '1rem' }}>Language:</label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            style={{
              background: 'rgba(0, 0, 0, 0.5)',
              border: '1px solid rgba(0, 255, 255, 0.3)',
              color: '#00ffff',
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
            background: 'rgba(0, 0, 0, 0.7)',
            border: '1px solid rgba(0, 255, 255, 0.3)',
            borderRadius: '8px',
            padding: '1rem',
            color: '#00ffff',
            fontSize: '0.95rem',
            fontFamily: 'monospace',
            resize: 'vertical',
            marginBottom: '1rem'
          }}
        />

        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
          <motion.button
            whileHover={{ scale: 1.05, boxShadow: '0 0 20px rgba(0, 255, 255, 0.5)' }}
            whileTap={{ scale: 0.95 }}
            onClick={executeCode}
            disabled={isExecuting}
            style={{
              background: 'linear-gradient(135deg, #00ffff 0%, #00cccc 100%)',
              border: 'none',
              color: '#000',
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
            whileHover={{ scale: 1.05, boxShadow: '0 0 20px rgba(255, 107, 255, 0.5)' }}
            whileTap={{ scale: 0.95 }}
            onClick={getAiCompletion}
            style={{
              background: 'rgba(255, 107, 255, 0.2)',
              border: '1px solid rgba(255, 107, 255, 0.5)',
              color: '#ff6bff',
              padding: '0.8rem 2rem',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: '600'
            }}
          >
            🤖 AI Complete
          </motion.button>
        </div>

        {output && (
          <div style={{
            background: 'rgba(0, 0, 0, 0.7)',
            border: '1px solid rgba(0, 255, 255, 0.3)',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1rem'
          }}>
            <h3 style={{ color: '#00ffff', marginBottom: '0.5rem' }}>Output:</h3>
            <pre style={{ 
              color: '#fff', 
              margin: 0, 
              whiteSpace: 'pre-wrap',
              fontFamily: 'monospace',
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
              background: 'rgba(255, 107, 255, 0.1)',
              border: '1px solid rgba(255, 107, 255, 0.3)',
              borderRadius: '8px',
              padding: '1rem'
            }}
          >
            <pre style={{ 
              color: '#ff6bff', 
              margin: 0, 
              whiteSpace: 'pre-wrap',
              fontFamily: 'monospace',
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
