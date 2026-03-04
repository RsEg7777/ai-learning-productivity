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

  const generateMockQuiz = (content: string, count: number): QuizResponse => {
    const questions: Question[] = [];
    
    // Extract sentences and key concepts
    const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 15);
    const words = content.toLowerCase().split(/\s+/).filter(w => w.length > 4);
    const uniqueWords = Array.from(new Set(words));
    
    // Detect facts
    const capitalizedWords = content.match(/\b[A-Z][a-z]+\b/g) || [];
    
    for (let i = 0; i < Math.min(count, sentences.length); i++) {
      const sentence = sentences[i].trim();
      const questionType = i % 4;
      
      if (questionType === 0 && sentence.length > 20) {
        // Multiple choice based on sentence
        const keywords = sentence.split(' ').filter(w => w.length > 5).slice(0, 4);
        const correctAnswer = keywords[0] || 'concept';
        
        questions.push({
          id: `q${i + 1}`,
          type: 'multiple_choice',
          text: `According to the content, which of the following is discussed: "${sentence.substring(0, 60)}..."?`,
          options: [
            `${correctAnswer} and its applications`,
            `Alternative interpretation of ${keywords[1] || 'the topic'}`,
            `Historical context of ${keywords[2] || 'the subject'}`,
            `Future implications of ${keywords[3] || 'the concept'}`
          ],
          points: 10
        });
      } else if (questionType === 1) {
        // True/False
        questions.push({
          id: `q${i + 1}`,
          type: 'true_false',
          text: `True or False: ${sentence}`,
          options: ['True', 'False'],
          points: 5
        });
      } else if (questionType === 2 && uniqueWords.length > i * 2) {
        // Multiple choice with concepts
        const concept1 = uniqueWords[i * 2] || 'concept';
        const concept2 = uniqueWords[i * 2 + 1] || 'topic';
        
        questions.push({
          id: `q${i + 1}`,
          type: 'multiple_choice',
          text: `What is the relationship between ${concept1} and ${concept2} in the given context?`,
          options: [
            `${concept1} directly influences ${concept2}`,
            `They are independent concepts`,
            `${concept2} is a subset of ${concept1}`,
            `They are opposing concepts`
          ],
          points: 10
        });
      } else {
        // Short answer
        const topic = uniqueWords[i] || 'main concept';
        questions.push({
          id: `q${i + 1}`,
          type: 'short_answer',
          text: `Explain the significance of "${topic}" as mentioned in the content. Provide specific details.`,
          points: 15
        });
      }
    }
    
    // Ensure we have the requested count
    while (questions.length < count) {
      const idx = questions.length;
      questions.push({
        id: `q${idx + 1}`,
        type: 'short_answer',
        text: `Summarize the key points from the content in your own words.`,
        points: 15
      });
    }

    const title = capitalizedWords.length > 0 
      ? `Quiz: ${capitalizedWords.slice(0, 3).join(', ')}`
      : `Quiz: ${uniqueWords.slice(0, 3).join(', ')}`;

    return {
      quiz_id: `quiz_${Date.now()}`,
      title: title.substring(0, 60),
      questions: questions.slice(0, count),
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

    // If no API URL is configured, use mock data directly
    if (!API_URL) {
      console.log('No API configured, using mock quiz generation');
      setTimeout(() => {
        const mockQuiz = generateMockQuiz(content, questionCount);
        setQuiz(mockQuiz);
        setLoading(false);
      }, 1500);
      return;
    }

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
