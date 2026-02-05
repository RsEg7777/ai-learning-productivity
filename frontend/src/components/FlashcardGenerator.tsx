import React, { useState } from 'react';

interface FlashcardGeneratorProps {
  authToken: string;
}

interface Flashcard {
  id: string;
  question: string;
  answer: string;
  difficulty: string;
  tags: string[];
}

interface FlashcardResponse {
  flashcards: Flashcard[];
  count: number;
}

const FlashcardGenerator: React.FC<FlashcardGeneratorProps> = ({ authToken }) => {
  const [content, setContent] = useState('');
  const [count, setCount] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);

  const API_URL = 'https://qtyf9c08b4.execute-api.ap-south-1.amazonaws.com/dev';

  const handleGenerate = async () => {
    if (!content.trim()) {
      setError('Please enter some content to generate flashcards');
      return;
    }

    setLoading(true);
    setError('');
    setFlashcards([]);

    try {
      const response = await fetch(`${API_URL}/flashcards/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authToken,
        },
        body: JSON.stringify({
          content: content,
          count: count,
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data: FlashcardResponse = await response.json();
      setFlashcards(data.flashcards);
    } catch (err: any) {
      setError(err.message || 'Failed to generate flashcards. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="component-container">
      <h2>🎴 Flashcard Generator</h2>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Create AI-powered flashcards for effective learning with spaced repetition.
      </p>

      {error && <div className="error">{error}</div>}

      <div className="form-group">
        <label>Content to Generate Flashcards From:</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Paste your learning content here..."
          rows={8}
        />
      </div>

      <div className="form-group">
        <label>Number of Flashcards: {count}</label>
        <input
          type="range"
          min="5"
          max="20"
          value={count}
          onChange={(e) => setCount(parseInt(e.target.value))}
          style={{ width: '100%' }}
        />
      </div>

      <button 
        className="btn-primary" 
        onClick={handleGenerate}
        disabled={loading}
      >
        {loading ? '🤖 Generating Flashcards...' : '✨ Generate Flashcards'}
      </button>

      {loading && (
        <div className="loading">
          <p>AI is creating your flashcards...</p>
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>This may take 10-30 seconds</p>
        </div>
      )}

      {flashcards.length > 0 && (
        <div className="flashcard-results">
          <div className="success">
            ✅ {flashcards.length} flashcards generated successfully!
          </div>

          {flashcards.map((card, index) => (
            <div key={card.id} className="flashcard">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3>Flashcard {index + 1}</h3>
                <span className="flashcard-difficulty">{card.difficulty.toUpperCase()}</span>
              </div>
              
              <div style={{ marginBottom: '1.5rem' }}>
                <strong style={{ fontSize: '0.9rem', opacity: 0.8 }}>QUESTION:</strong>
                <p style={{ marginTop: '0.5rem', fontSize: '1.1rem' }}>{card.question}</p>
              </div>
              
              <div>
                <strong style={{ fontSize: '0.9rem', opacity: 0.8 }}>ANSWER:</strong>
                <p style={{ marginTop: '0.5rem', fontSize: '1.1rem' }}>{card.answer}</p>
              </div>
              
              {card.tags && card.tags.length > 0 && (
                <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {card.tags.map((tag, i) => (
                    <span 
                      key={i} 
                      style={{ 
                        background: 'rgba(255,255,255,0.3)', 
                        padding: '0.3rem 0.8rem', 
                        borderRadius: '15px',
                        fontSize: '0.85rem'
                      }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FlashcardGenerator;
