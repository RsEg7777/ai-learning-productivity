'use client';
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface CollaborativeLearningProps { authToken: string; }

interface StudyRoom {
  id: string; name: string; topic: string; participants: number;
  maxParticipants: number; difficulty: string; aiModeratorActive: boolean;
  createdBy: string; tags: string[];
}

interface Participant { id: string; name: string; avatar: string; isActive: boolean; contributionScore: number; }
interface Message { id: string; sender: string; content: string; type: string; timestamp: string; }

const CollaborativeLearning: React.FC<CollaborativeLearningProps> = ({ authToken }) => {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || '';
  const [rooms, setRooms] = useState<StudyRoom[]>([]);
  const [currentRoom, setCurrentRoom] = useState<StudyRoom | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [userInput, setUserInput] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [newRoom, setNewRoom] = useState({ name: '', topic: '', difficulty: 'medium', maxParticipants: 10 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { loadRooms(); }, []);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const apiCall = async (path: string, method = 'GET', body?: object) => {
    const res = await fetch(`${API_URL}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
    if (!res.ok) { const d = await res.json(); throw new Error(d.detail || `Error ${res.status}`); }
    return res.json();
  };

  const loadRooms = async () => {
    try {
      const data = await apiCall('/collaborative/rooms');
      setRooms(data.rooms || []);
    } catch (e: any) { setError(e.message); }
  };

  const createRoom = async () => {
    if (!newRoom.name || !newRoom.topic) { setError('Name and topic are required'); return; }
    setLoading(true); setError('');
    try {
      const data = await apiCall('/collaborative/create-room', 'POST', newRoom);
      setRooms(r => [...r, data.room]);
      setShowCreate(false);
      setNewRoom({ name: '', topic: '', difficulty: 'medium', maxParticipants: 10 });
      await joinRoom(data.room.id);
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const joinRoom = async (roomId: string) => {
    setLoading(true); setError('');
    try {
      const data = await apiCall('/collaborative/join-room', 'POST', { roomId });
      setCurrentRoom(data.room);
      setParticipants(data.participants || [{ id: 'you', name: 'You', avatar: '😊', isActive: true, contributionScore: 0 }]);
      setMessages(data.recentMessages || []);
      setAiSuggestions([]);
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const sendMessage = async () => {
    if (!userInput.trim() || !currentRoom) return;
    const msg: Message = { id: Date.now().toString(), sender: 'You', content: userInput, type: 'user', timestamp: new Date().toISOString() };
    setMessages(m => [...m, msg]);
    const input = userInput;
    setUserInput('');
    setLoading(true);
    try {
      const data = await apiCall('/collaborative/send-message', 'POST', { roomId: currentRoom.id, message: input });
      if (data.aiResponse) {
        setMessages(m => [...m, { id: Date.now().toString() + '_ai', sender: 'AI Moderator', content: data.aiResponse, type: 'ai', timestamp: new Date().toISOString() }]);
      }
      if (data.suggestions?.length) setAiSuggestions(data.suggestions);
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const diffColor: Record<string,string> = { beginner: '#10b981', medium: '#f59e0b', intermediate: '#f59e0b', advanced: '#ef4444' };

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="component-container">
      <h2>👥 Collaborative Learning</h2>
      <p>AI-moderated study rooms where you learn together — every message gets real-time AI insights from Amazon Bedrock</p>
      {error && <div className="error">⚠️ {error} <button onClick={() => setError('')} style={{ marginLeft: '1rem', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}>✕</button></div>}

      {!currentRoom ? (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h3 style={{ color: 'var(--text-primary)', fontWeight: 700 }}>🌐 Available Rooms ({rooms.length})</h3>
            <div style={{ display: 'flex', gap: '.75rem' }}>
              <motion.button whileHover={{ scale: 1.04 }} whileTap={{ scale: .96 }} onClick={loadRooms}
                style={{ padding: '.5rem 1rem', background: 'var(--bg-glass)', border: '1px solid var(--border-default)', borderRadius: 'var(--r-md)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '.85rem', fontWeight: 600 }}>
                🔄 Refresh
              </motion.button>
              <motion.button whileHover={{ scale: 1.04 }} whileTap={{ scale: .96 }} onClick={() => setShowCreate(!showCreate)}
                style={{ padding: '.5rem 1.2rem', background: 'linear-gradient(135deg,var(--emerald),#059669)', border: 'none', borderRadius: 'var(--r-md)', color: '#fff', cursor: 'pointer', fontSize: '.85rem', fontWeight: 700 }}>
                + Create Room
              </motion.button>
            </div>
          </div>

          <AnimatePresence>
            {showCreate && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                style={{ background: 'rgba(13,13,36,0.6)', backdropFilter: 'blur(12px)', border: '1px solid var(--glass-border)', borderRadius: 'var(--r-lg)', padding: '1.5rem', marginBottom: '1.5rem', overflow: 'hidden' }}>
                <h4 style={{ color: 'var(--indigo-light)', marginBottom: '1rem', fontWeight: 700 }}>Create New Study Room</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                  <input value={newRoom.name} onChange={e => setNewRoom({ ...newRoom, name: e.target.value })} placeholder="Room name"
                    style={{ padding: '.7rem 1rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-default)', borderRadius: 'var(--r-md)', color: 'var(--text-primary)', fontSize: '.9rem', outline: 'none' }} />
                  <input value={newRoom.topic} onChange={e => setNewRoom({ ...newRoom, topic: e.target.value })} placeholder="Topic (e.g. React Hooks)"
                    style={{ padding: '.7rem 1rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-default)', borderRadius: 'var(--r-md)', color: 'var(--text-primary)', fontSize: '.9rem', outline: 'none' }} />
                  <select value={newRoom.difficulty} onChange={e => setNewRoom({ ...newRoom, difficulty: e.target.value })}
                    style={{ padding: '.7rem 1rem', background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 'var(--r-md)', color: 'var(--text-primary)', fontSize: '.9rem' }}>
                    <option value="beginner">Beginner</option><option value="medium">Intermediate</option><option value="advanced">Advanced</option>
                  </select>
                  <input type="number" value={newRoom.maxParticipants} onChange={e => setNewRoom({ ...newRoom, maxParticipants: +e.target.value })} min={2} max={50} placeholder="Max participants"
                    style={{ padding: '.7rem 1rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-default)', borderRadius: 'var(--r-md)', color: 'var(--text-primary)', fontSize: '.9rem', outline: 'none' }} />
                </div>
                <div style={{ display: 'flex', gap: '.75rem' }}>
                  <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: .97 }} onClick={createRoom} disabled={loading}
                    style={{ padding: '.7rem 1.5rem', background: 'linear-gradient(135deg,var(--indigo),var(--violet))', border: 'none', borderRadius: 'var(--r-md)', color: '#fff', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? .6 : 1 }}>
                    {loading ? 'Creating...' : '✨ Create with AI Tags'}
                  </motion.button>
                  <button onClick={() => setShowCreate(false)} style={{ padding: '.7rem 1rem', background: 'var(--bg-glass)', border: '1px solid var(--border-default)', borderRadius: 'var(--r-md)', color: 'var(--text-secondary)', cursor: 'pointer' }}>Cancel</button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(300px,1fr))', gap: '1rem' }}>
            {rooms.length === 0 && !loading && (
              <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>👥</div>
                <p>No rooms yet. Create the first one!</p>
              </div>
            )}
            {rooms.map((room, i) => (
              <motion.div key={room.id} initial={{ opacity: 0, scale: .95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * .05 }}
                style={{ background: 'rgba(13,13,36,0.6)', backdropFilter: 'blur(12px)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--r-lg)', padding: '1.5rem', cursor: 'pointer', transition: 'all .2s' }}
                whileHover={{ scale: 1.02, boxShadow: '0 8px 30px rgba(16,185,129,0.2)', borderColor: 'rgba(16,185,129,0.4)' }}
                onClick={() => joinRoom(room.id)}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '.75rem' }}>
                  <h4 style={{ color: 'var(--text-primary)', fontWeight: 700, flex: 1 }}>{room.name}</h4>
                  {room.aiModeratorActive && <span title="AI Moderator Active" style={{ fontSize: '1.2rem' }}>🤖</span>}
                </div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '.875rem', marginBottom: '1rem' }}>📚 {room.topic}</p>
                <div style={{ display: 'flex', gap: '.4rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                  <span style={{ padding: '.15rem .55rem', background: `${diffColor[room.difficulty] || '#6366f1'}22`, color: diffColor[room.difficulty] || '#6366f1', borderRadius: 'var(--r-full)', fontSize: '.72rem', fontWeight: 700, textTransform: 'uppercase' }}>{room.difficulty}</span>
                  {(room.tags || []).slice(0, 3).map(t => (
                    <span key={t} style={{ padding: '.15rem .55rem', background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)', borderRadius: 'var(--r-full)', fontSize: '.72rem' }}>{t}</span>
                  ))}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '.82rem' }}>👥 {room.participants}/{room.maxParticipants}</span>
                  <span style={{ padding: '.35rem .9rem', background: 'linear-gradient(135deg,var(--emerald),#059669)', color: '#fff', borderRadius: 'var(--r-sm)', fontSize: '.78rem', fontWeight: 700 }}>Join →</span>
                </div>
              </motion.div>
            ))}
          </div>
        </>
      ) : (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{currentRoom.name}</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '.875rem' }}>📚 {currentRoom.topic}</p>
            </div>
            <button onClick={() => { setCurrentRoom(null); setMessages([]); setParticipants([]); setAiSuggestions([]); }}
              style={{ padding: '.45rem 1rem', background: 'var(--bg-glass)', border: '1px solid var(--border-default)', borderRadius: 'var(--r-md)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '.85rem', fontWeight: 600 }}>
              ← Leave Room
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 220px', gap: '1rem' }}>
            {/* Chat */}
            <div style={{ background: 'rgba(13,13,36,0.6)', backdropFilter: 'blur(12px)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--r-lg)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div style={{ padding: '1rem', background: 'linear-gradient(135deg,var(--emerald),#059669)', color: '#fff', fontWeight: 700 }}>💬 Group Discussion</div>

              <div style={{ flex: 1, height: '420px', overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '.75rem' }}>
                {messages.map(msg => (
                  <motion.div key={msg.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                    style={{ padding: '1rem', borderRadius: 'var(--r-md)', background: msg.type === 'ai' ? 'rgba(139,92,246,0.1)' : msg.type === 'system' ? 'rgba(16,185,129,0.1)' : msg.sender === 'You' ? 'rgba(99,102,241,0.12)' : 'rgba(255,255,255,0.04)', border: `1px solid ${msg.type === 'ai' ? 'rgba(139,92,246,0.3)' : msg.type === 'system' ? 'rgba(16,185,129,0.3)' : 'var(--border-subtle)'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '.4rem' }}>
                      <strong style={{ color: msg.type === 'ai' ? 'var(--violet-light)' : msg.sender === 'You' ? 'var(--indigo-light)' : 'var(--emerald)', fontSize: '.82rem' }}>{msg.sender}</strong>
                      <span style={{ color: 'var(--text-muted)', fontSize: '.72rem' }}>{new Date(msg.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p style={{ color: 'var(--text-primary)', fontSize: '.875rem', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                  </motion.div>
                ))}
                {loading && <div style={{ display: 'flex', gap: '.3rem', padding: '.5rem' }}>{[0,1,2].map(i => <motion.div key={i} animate={{ scale: [1,1.4,1] }} transition={{ repeat: Infinity, duration: .6, delay: i*.2 }} style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--indigo)' }} />)}</div>}
                <div ref={messagesEndRef} />
              </div>

              {aiSuggestions.length > 0 && (
                <div style={{ padding: '.75rem 1rem', borderTop: '1px solid rgba(139,92,246,0.2)', background: 'rgba(139,92,246,0.06)' }}>
                  <p style={{ color: 'var(--violet-light)', fontSize: '.75rem', fontWeight: 700, marginBottom: '.4rem' }}>💡 AI Discussion Starters:</p>
                  <div style={{ display: 'flex', gap: '.4rem', flexWrap: 'wrap' }}>
                    {aiSuggestions.map((s, i) => (
                      <span key={i} onClick={() => setUserInput(s)} style={{ padding: '.25rem .6rem', background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.3)', borderRadius: 'var(--r-full)', color: 'var(--violet-light)', fontSize: '.75rem', cursor: 'pointer' }}>{s}</span>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ padding: '1rem', borderTop: '1px solid var(--border-subtle)', display: 'flex', gap: '.75rem' }}>
                <input value={userInput} onChange={e => setUserInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                  placeholder="Share your thoughts... (Enter to send)"
                  style={{ flex: 1, padding: '.7rem 1rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-default)', borderRadius: 'var(--r-md)', color: 'var(--text-primary)', fontSize: '.9rem', outline: 'none' }} />
                <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: .95 }} onClick={sendMessage} disabled={loading || !userInput.trim()}
                  style={{ padding: '.7rem 1.25rem', background: 'linear-gradient(135deg,var(--emerald),#059669)', border: 'none', borderRadius: 'var(--r-md)', color: '#fff', fontWeight: 700, cursor: loading || !userInput.trim() ? 'not-allowed' : 'pointer', opacity: loading || !userInput.trim() ? .5 : 1 }}>
                  Send
                </motion.button>
              </div>
            </div>

            {/* Participants sidebar */}
            <div style={{ background: 'rgba(13,13,36,0.6)', backdropFilter: 'blur(12px)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--r-lg)', padding: '1rem' }}>
              <h4 style={{ color: 'var(--text-primary)', fontWeight: 700, marginBottom: '1rem', fontSize: '.9rem' }}>👥 Participants ({participants.length})</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '.6rem' }}>
                {participants.map(p => (
                  <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '.6rem', padding: '.6rem', background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--r-md)' }}>
                    <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg,var(--indigo),var(--violet))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem', position: 'relative', flexShrink: 0 }}>
                      {p.avatar}
                      {p.isActive && <div style={{ position: 'absolute', bottom: 0, right: 0, width: 10, height: 10, borderRadius: '50%', background: 'var(--emerald)', border: '2px solid var(--bg-surface)' }} />}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ color: 'var(--text-primary)', fontSize: '.82rem', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</p>
                      <p style={{ color: 'var(--text-muted)', fontSize: '.72rem' }}>⭐ {p.contributionScore} pts</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
};
export default CollaborativeLearning;
