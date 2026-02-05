import React, { useState } from 'react';

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

  const API_URL = 'https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev';

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
          'Authorization': authToken,
        },
        body: JSON.stringify({
          content: content,
          question_count: questionCount,
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      setQuiz(data);
    } catch (err: any) {
      setError(err.message || 'Failed to generate quiz. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="component-container">
      <h2>📝 Quiz Generator</h2>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Generate AI-powered quizzes from any content. Get multiple choice, true/false, and fill-in-the-blank questions.
      </p>

      {error && <div className="error">{error}</div>}

      <div className="form-group">
        <label>Content to Generate Quiz From:</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Paste your learning content here... (e.g., lecture notes, article, documentation)"
          rows={8}
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
          style={{ width: '100%' }}
        />
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
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>This may take 10-30 seconds</p>
        </div>
      )}

      {quiz && (
        <div className="quiz-results">
          <div className="success">
            ✅ Quiz generated successfully! {quiz.questions.length} questions created.
          </div>

          <div style={{ marginBottom: '2rem', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
            <h3 style={{ color: '#667eea', marginBottom: '0.5rem' }}>{quiz.title}</h3>
            <p style={{ color: '#666' }}>
              Passing Score: {quiz.passing_score}% | 
              {quiz.time_limit ? ` Time Limit: ${quiz.time_limit}s` : ' No time limit'}
            </p>
          </div>

          {quiz.questions.map((question, index) => (
            <div key={question.id} className="question-card">
              <span className="question-type">{question.type.replace('_', ' ').toUpperCase()}</span>
              <h3>Question {index + 1}</h3>
              <p style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>{question.text}</p>
              
              {question.options && question.options.length > 0 && (
                <ul className="options">
                  {question.options.map((option, i) => (
                    <li key={i}>{option}</li>
                  ))}
                </ul>
              )}
              
              <p style={{ color: '#666', fontSize: '0.9rem', marginTop: '1rem' }}>
                Points: {question.points}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default QuizGenerator;
