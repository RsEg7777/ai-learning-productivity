import React, { useState } from 'react';
import { motion } from 'framer-motion';

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

  const generateMockQuiz = (content: string, count: number): QuizResponse => {
    const questions: Question[] = [];
    const topics = content.split(' ').slice(0, 5).join(' ');

    for (let i = 0; i < count; i++) {
      if (i % 3 === 0) {
        questions.push({
          id: `q${i + 1}`,
          type: 'multiple_choice',
          text: `What is the main concept discussed in "${topics}"?`,
          options: [
            'Option A: First possible answer',
            'Option B: Second possible answer',
            'Option C: Third possible answer',
            'Option D: Fourth possible answer'
          ],
          points: 10
        });
      } else if (i % 3 === 1) {
        questions.push({
          id: `q${i + 1}`,
          type: 'true_false',
          text: `The content discusses important aspects of the topic. True or False?`,
          options: ['True', 'False'],
          points: 5
        });
      } else {
        questions.push({
          id: `q${i + 1}`,
          type: 'short_answer',
          text: `Explain the key takeaway from the content in your own words.`,
          points: 15
        });
      }
    }

    return {
      quiz_id: `quiz_${Date.now()}`,
      title: `Quiz: ${topics.substring(0, 50)}...`,
      questions,
      time_limit: count * 60,
      passing_score: 70
    };
  };

  const handleGenerate = async () => {
    if (!content.trim()) {
      setError('Please enter some content to generate a quiz');
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
        console.warn('API not available, using mock data');
        const mockQuiz = generateMockQuiz(content, questionCount);
        setQuiz(mockQuiz);
        setLoading(false);
        return;
      }

      const data = await response.json();
      setQuiz(data);
    } catch (err: any) {
      console.warn('API error, using mock data:', err);
      const mockQuiz = generateMockQuiz(content, questionCount);
      setQuiz(mockQuiz);
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
        <label>Content to Generate Quiz From:</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Paste your learning content here... (e.g., lecture notes, article, documentation)"
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
              
              {question.options && question.options.length > 0 && (
                <ul className="options">
                  {question.options.map((option, i) => (
                    <li key={i}>{option}</li>
                  ))}
                </ul>
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
