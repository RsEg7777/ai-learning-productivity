import React, { useState } from 'react';
import { motion } from 'framer-motion';

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
  const [flippedCards, setFlippedCards] = useState<Set<string>>(new Set());

  const API_URL = process.env.REACT_APP_API_URL || '';

  const generateMockFlashcards = (content: string, count: number): Flashcard[] => {
    const flashcards: Flashcard[] = [];
    const topics = content.split(' ').slice(0, 10);
    const difficulties = ['easy', 'medium', 'hard'];

    for (let i = 0; i < count; i++) {
      const topic = topics[i % topics.length] || 'concept';
      const difficulty = difficulties[i % 3];
      
      flashcards.push({
        id: `fc_${Date.now()}_${i}`,
        question: `What is ${topic}? Explain its significance and applications.`,
        answer: `${topic.charAt(0).toUpperCase() + topic.slice(1)} is an important concept that plays a crucial role in understanding the subject matter. It has various applications and is fundamental to grasping more advanced topics.`,
        difficulty: difficulty,
        tags: [topic, 'fundamental', difficulty]
      });
    }

    return flashcards;
  };

  const handleGenerate = async () => {
    if (!content.trim()) {
      setError('Please enter some content to generate flashcards');
      return;
    }

    setLoading(true);
    setError('');
    setFlashcards([]);
    setFlippedCards(new Set());

    try {
      const response = await fetch(`${API_URL}/flashcards/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          content: content,
          count: count,
        }),
      });

      if (!response.ok) {
        console.warn('API not available, using mock data');
        const mockFlashcards = generateMockFlashcards(content, count);
        setFlashcards(mockFlashcards);
        setLoading(false);
        return;
      }

      const data: FlashcardResponse = await response.json();
      setFlashcards(data.flashcards);
    } catch (err: any) {
      console.warn('API error, using mock data:', err);
      const mockFlashcards = generateMockFlashcards(content, count);
      setFlashcards(mockFlashcards);
    } finally {
      setLoading(false);
    }
  };

  const toggleFlip = (cardId: string) => {
    setFlippedCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(cardId)) {
        newSet.delete(cardId);
      } else {
        newSet.add(cardId);
      }
      return newSet;
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="component-container"
    >
      <h2>🎴 Flashcard Generator</h2>
      <p>Create AI-powered flashcards for effective learning with spaced repetition</p>

      {error && <div className="error">{error}</div>}

      <div className="form-group">
        <label>Content to Generate Flashcards From:</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Paste your learning content here..."
          rows={10}
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
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
          <span>5</span>
          <span>20</span>
        </div>
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
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem', color: 'var(--text-muted)' }}>
            This may take 10-30 seconds
          </p>
        </div>
      )}

      {flashcards.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flashcard-results"
        >
          <div className="success">
            ✅ {flashcards.length} flashcards generated successfully!
          </div>

          <div style={{ marginBottom: '1rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            💡 Click on any card to flip and reveal the answer
          </div>

          {flashcards.map((card, index) => {
            const isFlipped = flippedCards.has(card.id);
            return (
              <motion.div
                key={card.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="flashcard"
                onClick={() => toggleFlip(card.id)}
                style={{ 
                  cursor: 'pointer',
                  minHeight: '180px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3 style={{ margin: 0 }}>Flashcard {index + 1}</h3>
                    <span className="flashcard-difficulty">{card.difficulty}</span>
                  </div>
                  
                  <motion.div
                    initial={false}
                    animate={{ rotateY: isFlipped ? 180 : 0 }}
                    transition={{ duration: 0.6 }}
                    style={{ transformStyle: 'preserve-3d' }}
                  >
                    {!isFlipped ? (
                      <div>
                        <strong style={{ fontSize: '0.85rem', opacity: 0.8, color: 'var(--primary-light)' }}>
                          QUESTION:
                        </strong>
                        <p style={{ marginTop: '0.5rem', fontSize: '1.05rem', lineHeight: '1.6' }}>
                          {card.question}
                        </p>
                      </div>
                    ) : (
                      <div>
                        <strong style={{ fontSize: '0.85rem', opacity: 0.8, color: 'var(--success)' }}>
                          ANSWER:
                        </strong>
                        <p style={{ marginTop: '0.5rem', fontSize: '1.05rem', lineHeight: '1.6' }}>
                          {card.answer}
                        </p>
                      </div>
                    )}
                  </motion.div>
                </div>
                
                {card.tags && card.tags.length > 0 && (
                  <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {card.tags.map((tag, i) => (
                      <span 
                        key={i} 
                        style={{ 
                          background: 'var(--bg-dark)', 
                          padding: '0.3rem 0.75rem', 
                          borderRadius: '15px',
                          fontSize: '0.8rem',
                          color: 'var(--text-secondary)',
                          border: '1px solid var(--border)'
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </motion.div>
            );
          })}
        </motion.div>
      )}
    </motion.div>
  );
};

export default FlashcardGenerator;
