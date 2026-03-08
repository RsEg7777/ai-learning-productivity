import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import VoiceInput from './VoiceInput';

interface QuizGeneratorProps {
  authToken: string;
}

interface Question {
  id: string;
  type: string;
  text: string;
  options?: string[];
  points: number;
}

interface QuizResponse {
  quiz_id: string;
  title: string;
  questions: Question[];
  time_limit?: number;
  passing_score: number;
}

const QuizGenerator: React.FC<QuizGeneratorProps> = ({ authToken }) => {
  const [content, setContent] = useState('');
  const [questionCount, setQuestionCount] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [quiz, setQuiz] = useState<QuizResponse | null>(null);

  const API_URL = process.env.REACT_APP_API_URL || '';

  const handleVoiceTranscript = useCallback((text: string) => {
    setContent(prev => {
      const needsSpace = prev.length > 0 && !prev.endsWith(' ') && !prev.endsWith('\n');
      return prev + (needsSpace ? ' ' : '') + text;
    });
  }, []);

  const handleGenerate = async () => {
    if (!content.trim()) {
      setError('Please enter some content to generate a quiz');
      return;
    }

    if (!API_URL) {
      setError('API URL not configured. Please set REACT_APP_API_URL environment variable.');
      return;
    }

    setLoading(true);
    setError('');
    setQuiz(null);

    try {
      const response = await fetch(`${API_URL}/quiz/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          content: content,
          question_count: questionCount,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `Server error: ${response.statusText}`);
      }

      const data = await response.json();
      if (data.success) {
        setQuiz(data);
      } else {
        throw new Error(data.detail || 'Quiz generation failed');
      }
    } catch (err: any) {
      console.error('Error generating quiz:', err);
      setError(`Failed to generate quiz: ${err.message}. Please ensure the backend is running.`);
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
      <h2>📝 Quiz Generator</h2>
      <p>Generate AI-powered quizzes from any content with multiple question types</p>

      {error && <div className="error">{error}</div>}

      <div className="form-group">
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          Content to Generate Quiz From:
          <VoiceInput
            onTranscript={handleVoiceTranscript}
            disabled={loading}
          />
        </label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Paste your learning content here, or use the 🎤 mic to dictate..."
          rows={10}
        />
      </div>

      <div className="form-group">
        <label>Number of Questions: {questionCount}</label>
        <input
          type="range"
          min="3"
          max="15"
          value={questionCount}
          onChange={(e) => setQuestionCount(parseInt(e.target.value))}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
          <span>3</span>
          <span>15</span>
        </div>
      </div>

      <button 
        className="btn-primary" 
        onClick={handleGenerate}
        disabled={loading}
      >
        {loading ? '🤖 Generating Quiz...' : '✨ Generate Quiz'}
      </button>

      {loading && (
        <div className="loading">
          <p>AI is analyzing your content and creating questions...</p>
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem', color: 'var(--text-muted)' }}>
            This may take 10-30 seconds
          </p>
        </div>
      )}

      {quiz && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="quiz-results"
        >
          <div className="success">
            ✅ Quiz generated successfully! {quiz.questions.length} questions created.
          </div>

          <div style={{ 
            marginBottom: '2rem', 
            padding: '1.25rem', 
            background: 'var(--bg-dark)', 
            borderRadius: '12px',
            border: '1px solid var(--border)'
          }}>
            <h3 style={{ color: 'var(--primary-light)', marginBottom: '0.5rem', fontSize: '1.3rem' }}>
              {quiz.title}
            </h3>
            <p style={{ color: 'var(--text-secondary)' }}>
              Passing Score: {quiz.passing_score}% | 
              {quiz.time_limit ? ` Time Limit: ${quiz.time_limit}s` : ' No time limit'}
            </p>
          </div>

          {quiz.questions.map((question, index) => (
            <motion.div
              key={question.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="question-card"
            >
              <span className="question-type">{question.type.replace('_', ' ')}</span>
              <h3>Question {index + 1}</h3>
              <p style={{ fontSize: '1.05rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>
                {question.text}
              </p>
              
              {question.options && question.options.length > 0 ? (
                <ul className="options">
                  {question.options.map((option, i) => (
                    <li key={i}>{option}</li>
                  ))}
                </ul>
              ) : (
                <div style={{ marginTop: '1rem' }}>
                  <textarea
                    placeholder="Type your answer here..."
                    rows={4}
                    style={{
                      width: '100%',
                      padding: '1rem',
                      background: 'var(--bg-dark)',
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                      color: 'var(--text-primary)',
                      fontSize: '0.95rem',
                      fontFamily: 'inherit',
                      resize: 'vertical'
                    }}
                  />
                </div>
              )}
              
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '1rem' }}>
                Points: {question.points}
              </p>
            </motion.div>
          ))}
        </motion.div>
      )}
    </motion.div>
  );
};

export default QuizGenerator;
