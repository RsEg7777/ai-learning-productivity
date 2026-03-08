import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface CollaborativeLearningProps {
  authToken: string;
}

interface StudyRoom {
  id: string;
  name: string;
  topic: string;
  participants: number;
  maxParticipants: number;
  difficulty: string;
  aiModeratorActive: boolean;
  createdBy: string;
  tags: string[];
}

interface Participant {
  id: string;
  name: string;
  avatar: string;
  isActive: boolean;
  contributionScore: number;
}

const CollaborativeLearning: React.FC<CollaborativeLearningProps> = ({ authToken }) => {
  const [rooms, setRooms] = useState<StudyRoom[]>([]);
  const [currentRoom, setCurrentRoom] = useState<StudyRoom | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [messages, setMessages] = useState<Array<{id: string, sender: string, content: string, type: string, timestamp: string}>>([]);
  const [userInput, setUserInput] = useState('');
  const [showCreateRoom, setShowCreateRoom] = useState(false);
  const [newRoom, setNewRoom] = useState({ name: '', topic: '', difficulty: 'medium', maxParticipants: 10 });
  const [loading, setLoading] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);

  const API_URL = process.env.REACT_APP_API_URL || '';

  useEffect(() => {
    loadAvailableRooms();
  }, []);

  const loadAvailableRooms = async () => {
    try {
      // Try API first, fallback to demo mode
      if (API_URL) {
        try {
          const response = await fetch(`${API_URL}/collaborative/rooms`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
          });
          if (response.ok) {
            const data = await response.json();
            setRooms(data.rooms || []);
            return;
          }
        } catch (apiError) {
          console.log('API unavailable, using demo rooms');
        }
      }
      
      // Demo mode fallback
      setRooms([
        {
          id: 'demo-1',
          name: 'Python Study Group',
          topic: 'Python Programming',
          participants: 3,
          maxParticipants: 10,
          difficulty: 'intermediate',
          aiModeratorActive: true,
          createdBy: 'Demo User',
          tags: ['python', 'programming', 'beginner-friendly']
        },
        {
          id: 'demo-2',
          name: 'Web Development',
          topic: 'React & JavaScript',
          participants: 5,
          maxParticipants: 8,
          difficulty: 'intermediate',
          aiModeratorActive: true,
          createdBy: 'Demo User',
          tags: ['react', 'javascript', 'web']
        }
      ]);
    } catch (error) {
      console.error('Error loading rooms:', error);
    }
  };

  const createRoom = async () => {
    if (!newRoom.name || !newRoom.topic) return;

    setLoading(true);
    try {
      // Try API first, fallback to demo mode
      let roomData: any = null;
      
      if (API_URL) {
        try {
          const response = await fetch(`${API_URL}/collaborative/create-room`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(newRoom)
          });

          if (response.ok) {
            roomData = await response.json();
          }
        } catch (apiError) {
          console.log('API unavailable, creating demo room');
        }
      }
      
      // Demo mode fallback
      if (!roomData) {
        roomData = {
          room: {
            id: 'demo-' + Date.now(),
            name: newRoom.name,
            topic: newRoom.topic,
            participants: 1,
            maxParticipants: newRoom.maxParticipants,
            difficulty: newRoom.difficulty,
            aiModeratorActive: true,
            createdBy: 'You',
            tags: [newRoom.topic.toLowerCase()]
          }
        };
      }

      setRooms([...rooms, roomData.room]);
      setShowCreateRoom(false);
      setNewRoom({ name: '', topic: '', difficulty: 'medium', maxParticipants: 10 });
      joinRoom(roomData.room.id);
    } catch (error) {
      console.error('Error creating room:', error);
    }
    setLoading(false);
  };

  const joinRoom = async (roomId: string) => {
    setLoading(true);
    try {
      // Try API first, fallback to demo mode
      let roomData: any = null;
      
      if (API_URL && !roomId.startsWith('demo-')) {
        try {
          const response = await fetch(`${API_URL}/collaborative/join-room`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ roomId })
          });

          if (response.ok) {
            roomData = await response.json();
          }
        } catch (apiError) {
          console.log('API unavailable, using demo room');
        }
      }
      
      // Demo mode fallback
      if (!roomData) {
        const room = rooms.find(r => r.id === roomId);
        roomData = {
          room: room,
          participants: [
            { id: '1', name: 'You', avatar: '👤', isActive: true, contributionScore: 0 },
            { id: '2', name: 'Alex', avatar: '👨‍💻', isActive: true, contributionScore: 85 },
            { id: '3', name: 'Sarah', avatar: '👩‍💻', isActive: true, contributionScore: 92 }
          ],
          recentMessages: [
            { id: '1', sender: 'AI Moderator', content: `Welcome to ${room?.name}! I'm here to facilitate your learning.`, type: 'system', timestamp: new Date().toISOString() }
          ]
        };
      }

      setCurrentRoom(roomData.room);
      setParticipants(roomData.participants);
      setMessages(roomData.recentMessages || []);
        
      // AI moderator welcome message
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        sender: 'AI Moderator',
        content: `Welcome to "${roomData.room.name}"! 🤖\n\nI'm your AI moderator. I'll help facilitate discussions, answer questions, and provide insights. Let's learn together!`,
        type: 'system',
        timestamp: new Date().toISOString()
      }]);
    } catch (error) {
      console.error('Error joining room:', error);
    }
    setLoading(false);
  };

  const sendMessage = async () => {
    if (!userInput.trim() || !currentRoom) return;

    const newMessage = {
      id: Date.now().toString(),
      sender: 'You',
      content: userInput,
      type: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages([...messages, newMessage]);
    setUserInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/collaborative/send-message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          roomId: currentRoom.id,
          message: userInput
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // AI moderator might respond with insights
        if (data.aiResponse) {
          setMessages(prev => [...prev, {
            id: (Date.now() + 1).toString(),
            sender: 'AI Moderator',
            content: data.aiResponse,
            type: 'ai',
            timestamp: new Date().toISOString()
          }]);
        }

        if (data.suggestions) {
          setAiSuggestions(data.suggestions);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
    setLoading(false);
  };

  const leaveRoom = () => {
    setCurrentRoom(null);
    setParticipants([]);
    setMessages([]);
    setAiSuggestions([]);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ width: '100%', maxWidth: '1400px', margin: '0 auto' }}
    >
      <div style={{
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
        border: '1px solid var(--border)',
        borderRadius: '20px',
        padding: '2rem',
        marginBottom: '2rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{
            width: '60px',
            height: '60px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '2rem',
            boxShadow: '0 0 30px rgba(16, 185, 129, 0.5)'
          }}>
            👥
          </div>
          <div>
            <h2 style={{ color: '#10b981', margin: 0, fontSize: '2rem' }}>
              Collaborative Learning Rooms
            </h2>
            <p style={{ color: 'var(--text-secondary)', margin: '0.25rem 0 0 0' }}>
              Learn together with AI-moderated study sessions
            </p>
          </div>
        </div>

        {!currentRoom ? (
          <>
            {/* Room Browser */}
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ color: 'var(--text-primary)', margin: 0 }}>🌐 Available Study Rooms</h3>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setShowCreateRoom(!showCreateRoom)}
                  style={{
                    background: '#10b981',
                    border: 'none',
                    color: 'white',
                    padding: '0.6rem 1.2rem',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    fontWeight: '600'
                  }}
                >
                  + Create Room
                </motion.button>
              </div>

              {showCreateRoom && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border)',
                    borderRadius: '12px',
                    padding: '1.5rem',
                    marginBottom: '1rem'
                  }}
                >
                  <input
                    type="text"
                    placeholder="Room name"
                    value={newRoom.name}
                    onChange={(e) => setNewRoom({ ...newRoom, name: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--bg-dark)',
                      border: '1px solid var(--border)',
                      color: 'var(--text-primary)',
                      padding: '0.75rem',
                      borderRadius: '8px',
                      marginBottom: '1rem',
                      fontSize: '1rem'
                    }}
                  />
                  <input
                    type="text"
                    placeholder="Topic (e.g., React Hooks, Data Structures)"
                    value={newRoom.topic}
                    onChange={(e) => setNewRoom({ ...newRoom, topic: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--bg-dark)',
                      border: '1px solid var(--border)',
                      color: 'var(--text-primary)',
                      padding: '0.75rem',
                      borderRadius: '8px',
                      marginBottom: '1rem',
                      fontSize: '1rem'
                    }}
                  />
                  <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                    <select
                      value={newRoom.difficulty}
                      onChange={(e) => setNewRoom({ ...newRoom, difficulty: e.target.value })}
                      style={{
                        flex: 1,
                        background: 'var(--bg-dark)',
                        border: '1px solid var(--border)',
                        color: 'var(--text-primary)',
                        padding: '0.75rem',
                        borderRadius: '8px',
                        fontSize: '1rem'
                      }}
                    >
                      <option value="beginner">Beginner</option>
                      <option value="medium">Intermediate</option>
                      <option value="advanced">Advanced</option>
                    </select>
                    <input
                      type="number"
                      placeholder="Max participants"
                      value={newRoom.maxParticipants}
                      onChange={(e) => setNewRoom({ ...newRoom, maxParticipants: parseInt(e.target.value) })}
                      min="2"
                      max="50"
                      style={{
                        flex: 1,
                        background: 'var(--bg-dark)',
                        border: '1px solid var(--border)',
                        color: 'var(--text-primary)',
                        padding: '0.75rem',
                        borderRadius: '8px',
                        fontSize: '1rem'
                      }}
                    />
                  </div>
                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={createRoom}
                      disabled={loading}
                      style={{
                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                        border: 'none',
                        color: 'white',
                        padding: '0.75rem 1.5rem',
                        borderRadius: '8px',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        fontSize: '1rem',
                        fontWeight: '600',
                        opacity: loading ? 0.6 : 1
                      }}
                    >
                      {loading ? 'Creating...' : '✨ Create Room'}
                    </motion.button>
                    <button
                      onClick={() => setShowCreateRoom(false)}
                      style={{
                        background: 'var(--bg-dark)',
                        border: '1px solid var(--border)',
                        color: 'var(--text-primary)',
                        padding: '0.75rem 1.5rem',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        fontSize: '1rem'
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </motion.div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
                {rooms.map((room, index) => (
                  <motion.div
                    key={room.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.1 }}
                    style={{
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border)',
                      borderRadius: '12px',
                      padding: '1.5rem',
                      cursor: 'pointer'
                    }}
                    whileHover={{ scale: 1.02, boxShadow: '0 8px 24px rgba(16, 185, 129, 0.2)' }}
                    onClick={() => joinRoom(room.id)}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                      <h4 style={{ color: 'var(--text-primary)', margin: 0 }}>{room.name}</h4>
                      {room.aiModeratorActive && (
                        <span style={{ fontSize: '1.2rem' }} title="AI Moderator Active">🤖</span>
                      )}
                    </div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>
                      📚 {room.topic}
                    </p>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                      <span style={{
                        background: 'rgba(16, 185, 129, 0.2)',
                        color: '#10b981',
                        padding: '0.25rem 0.75rem',
                        borderRadius: '12px',
                        fontSize: '0.8rem'
                      }}>
                        {room.difficulty}
                      </span>
                      {room.tags?.map(tag => (
                        <span key={tag} style={{
                          background: 'var(--bg-dark)',
                          color: 'var(--text-secondary)',
                          padding: '0.25rem 0.75rem',
                          borderRadius: '12px',
                          fontSize: '0.8rem'
                        }}>
                          {tag}
                        </span>
                      ))}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                        👥 {room.participants}/{room.maxParticipants}
                      </span>
                      <span style={{
                        background: '#10b981',
                        color: 'white',
                        padding: '0.4rem 1rem',
                        borderRadius: '6px',
                        fontSize: '0.85rem',
                        fontWeight: '600'
                      }}>
                        Join →
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <>
            {/* Active Room */}
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div>
                  <h3 style={{ color: 'var(--text-primary)', margin: 0 }}>{currentRoom.name}</h3>
                  <p style={{ color: 'var(--text-secondary)', margin: '0.25rem 0 0 0', fontSize: '0.9rem' }}>
                    📚 {currentRoom.topic}
                  </p>
                </div>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={leaveRoom}
                  style={{
                    background: 'var(--bg-dark)',
                    border: '1px solid var(--border)',
                    color: 'var(--text-primary)',
                    padding: '0.6rem 1.2rem',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    fontWeight: '600'
                  }}
                >
                  ← Leave Room
                </motion.button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 250px', gap: '1rem' }}>
                {/* Chat Area */}
                <div style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: '12px',
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column'
                }}>
                  <div style={{
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    padding: '1rem',
                    color: 'white',
                    fontWeight: '600'
                  }}>
                    💬 Group Discussion
                  </div>
                  
                  <div style={{
                    flex: 1,
                    height: '500px',
                    overflowY: 'auto',
                    padding: '1rem'
                  }}>
                    {messages.map((msg) => (
                      <motion.div
                        key={msg.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        style={{
                          marginBottom: '1rem',
                          padding: '1rem',
                          borderRadius: '12px',
                          background: msg.type === 'ai' ? 'rgba(139, 92, 246, 0.1)' :
                                     msg.type === 'system' ? 'rgba(16, 185, 129, 0.1)' :
                                     msg.sender === 'You' ? 'rgba(99, 102, 241, 0.1)' : 'var(--bg-dark)',
                          border: `1px solid ${msg.type === 'ai' ? 'var(--secondary)' : 
                                               msg.type === 'system' ? '#10b981' : 'var(--border)'}`
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                          <strong style={{ color: msg.type === 'ai' ? 'var(--secondary)' : 'var(--primary)' }}>
                            {msg.sender}
                          </strong>
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <p style={{ color: 'var(--text-primary)', margin: 0, whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
                          {msg.content}
                        </p>
                      </motion.div>
                    ))}
                  </div>

                  {aiSuggestions.length > 0 && (
                    <div style={{
                      padding: '1rem',
                      background: 'rgba(139, 92, 246, 0.1)',
                      borderTop: '1px solid var(--secondary)'
                    }}>
                      <strong style={{ color: 'var(--secondary)', fontSize: '0.9rem' }}>💡 AI Suggestions:</strong>
                      <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                        {aiSuggestions.map((suggestion, i) => (
                          <span
                            key={i}
                            onClick={() => setUserInput(suggestion)}
                            style={{
                              background: 'var(--bg-dark)',
                              color: 'var(--text-primary)',
                              padding: '0.4rem 0.8rem',
                              borderRadius: '6px',
                              fontSize: '0.85rem',
                              cursor: 'pointer',
                              border: '1px solid var(--border)'
                            }}
                          >
                            {suggestion}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div style={{
                    padding: '1rem',
                    borderTop: '1px solid var(--border)',
                    display: 'flex',
                    gap: '0.75rem'
                  }}>
                    <input
                      type="text"
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                      placeholder="Share your thoughts..."
                      style={{
                        flex: 1,
                        background: 'var(--bg-dark)',
                        border: '1px solid var(--border)',
                        color: 'var(--text-primary)',
                        padding: '0.75rem',
                        borderRadius: '8px',
                        fontSize: '1rem'
                      }}
                    />
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={sendMessage}
                      disabled={loading || !userInput.trim()}
                      style={{
                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                        border: 'none',
                        color: 'white',
                        padding: '0.75rem 1.5rem',
                        borderRadius: '8px',
                        cursor: loading || !userInput.trim() ? 'not-allowed' : 'pointer',
                        fontSize: '1rem',
                        fontWeight: '600',
                        opacity: loading || !userInput.trim() ? 0.6 : 1
                      }}
                    >
                      Send
                    </motion.button>
                  </div>
                </div>

                {/* Participants Sidebar */}
                <div style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: '12px',
                  padding: '1rem'
                }}>
                  <h4 style={{ color: 'var(--text-primary)', margin: '0 0 1rem 0' }}>
                    👥 Participants ({participants.length})
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {participants.map(participant => (
                      <div
                        key={participant.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.75rem',
                          padding: '0.75rem',
                          background: 'var(--bg-dark)',
                          borderRadius: '8px'
                        }}
                      >
                        <div style={{
                          width: '40px',
                          height: '40px',
                          borderRadius: '50%',
                          background: 'linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '1.2rem',
                          position: 'relative'
                        }}>
                          {participant.avatar}
                          {participant.isActive && (
                            <div style={{
                              position: 'absolute',
                              bottom: 0,
                              right: 0,
                              width: '12px',
                              height: '12px',
                              borderRadius: '50%',
                              background: '#10b981',
                              border: '2px solid var(--bg-dark)'
                            }} />
                          )}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ color: 'var(--text-primary)', fontSize: '0.9rem', fontWeight: '600' }}>
                            {participant.name}
                          </div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                            ⭐ {participant.contributionScore} pts
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </motion.div>
  );
};

export default CollaborativeLearning;
