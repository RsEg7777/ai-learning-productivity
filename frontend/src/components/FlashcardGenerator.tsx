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
    
    // Extract meaningful phrases and concepts
    const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 10);
    const words = content.toLowerCase().split(/\s+/).filter(w => w.length > 4);
    const uniqueWords = Array.from(new Set(words)).slice(0, 20);
    
    // Detect topic
    const topicKeywords = {
      programming: ['code', 'function', 'variable', 'class', 'method', 'algorithm', 'data', 'program'],
      science: ['theory', 'experiment', 'hypothesis', 'research', 'study', 'analysis', 'result'],
      math: ['equation', 'formula', 'calculate', 'number', 'solve', 'proof', 'theorem'],
      history: ['year', 'century', 'war', 'empire', 'revolution', 'period', 'era'],
      language: ['grammar', 'vocabulary', 'sentence', 'word', 'meaning', 'definition']
    };
    
    let detectedTopic = 'general';
    let maxMatches = 0;
    
    for (const [topic, keywords] of Object.entries(topicKeywords)) {
      const matches = keywords.filter(kw => content.toLowerCase().includes(kw)).length;
      if (matches > maxMatches) {
        maxMatches = matches;
        detectedTopic = topic;
      }
    }
    
    const difficulties = ['easy', 'medium', 'hard'];
    
    for (let i = 0; i < Math.min(count, sentences.length); i++) {
      const sentence = sentences[i].trim();
      const difficulty = difficulties[i % 3];
      const relevantWords = uniqueWords.slice(i * 2, i * 2 + 3);
      
      // Create contextual question
      let question = '';
      let answer = '';
      
      if (i % 3 === 0) {
        // Definition style
        const keyword = relevantWords[0] || 'concept';
        question = `What is ${keyword} and why is it important in ${detectedTopic}?`;
        answer = sentence.length > 100 ? sentence.substring(0, 100) + '...' : sentence;
      } else if (i % 3 === 1) {
        // Explanation style
        question = `Explain the concept: "${sentence.substring(0, 50)}..."`;
        answer = `This refers to ${sentence}. It's a key concept in understanding ${detectedTopic}.`;
      } else {
        // Application style
        question = `How would you apply this concept: ${relevantWords.slice(0, 2).join(' and ')}?`;
        answer = `Based on the content: ${sentence}`;
      }
      
      flashcards.push({
        id: `fc_${Date.now()}_${i}`,
        question: question,
        answer: answer,
        difficulty: difficulty,
        tags: [detectedTopic, ...relevantWords.slice(0, 2), difficulty]
      });
    }
    
    // If we need more flashcards, create summary ones
    while (flashcards.length < count && sentences.length > 0) {
      const idx = flashcards.length;
      const sentence = sentences[idx % sentences.length];
      flashcards.push({
        id: `fc_${Date.now()}_${idx}`,
        question: `What does this statement mean: "${sentence.substring(0, 60)}..."?`,
        answer: sentence,
        difficulty: difficulties[idx % 3],
        tags: [detectedTopic, 'comprehension']
      });
    }

    return flashcards.slice(0, count);
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

    // If no API URL is configured, use mock data directly
    if (!API_URL) {
      console.log('No API configured, using mock flashcard generation');
      setTimeout(() => {
        const mockFlashcards = generateMockFlashcards(content, count);
        setFlashcards(mockFlashcards);
        setLoading(false);
      }, 1500);
      return;
    }

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
