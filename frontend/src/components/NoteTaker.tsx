import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Note {
  id: string;
  title: string;
  content: string;
  category: string;
  pinned: boolean;
  createdAt: string;
  updatedAt: string;
}

const CATEGORIES = ['General', 'Programming', 'Mathematics', 'Science', 'Languages', 'Other'];

const loadNotes = (): Note[] => {
  try {
    const saved = localStorage.getItem('studyNotes');
    if (saved) return JSON.parse(saved);
  } catch (e) {
    console.warn('Failed to load notes:', e);
  }
  return [];
};

const NoteTaker: React.FC = () => {
  const [notes, setNotes] = useState<Note[]>(loadNotes);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [editingNote, setEditingNote] = useState<Note | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newNote, setNewNote] = useState({ title: '', content: '', category: 'General' });

  // Persist notes
  useEffect(() => {
    try {
      localStorage.setItem('studyNotes', JSON.stringify(notes));
    } catch (e) {
      console.warn('Failed to save notes:', e);
    }
  }, [notes]);

  const createNote = useCallback(() => {
    if (!newNote.title.trim()) return;
    const note: Note = {
      id: Date.now().toString(),
      title: newNote.title,
      content: newNote.content,
      category: newNote.category,
      pinned: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setNotes(prev => [note, ...prev]);
    setNewNote({ title: '', content: '', category: 'General' });
    setIsCreating(false);
  }, [newNote]);

  const updateNote = useCallback(() => {
    if (!editingNote) return;
    setNotes(prev =>
      prev.map(n =>
        n.id === editingNote.id
          ? { ...editingNote, updatedAt: new Date().toISOString() }
          : n
      )
    );
    setEditingNote(null);
  }, [editingNote]);

  const deleteNote = useCallback((id: string) => {
    setNotes(prev => prev.filter(n => n.id !== id));
    if (editingNote?.id === id) setEditingNote(null);
  }, [editingNote]);

  const togglePin = useCallback((id: string) => {
    setNotes(prev =>
      prev.map(n => (n.id === id ? { ...n, pinned: !n.pinned } : n))
    );
  }, []);

  const exportNotes = useCallback(() => {
    const md = notes
      .map(n => `# ${n.title}\n**Category:** ${n.category} | **Created:** ${new Date(n.createdAt).toLocaleDateString()}\n\n${n.content}\n\n---`)
      .join('\n\n');
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'study-notes.md';
    a.click();
    URL.revokeObjectURL(url);
  }, [notes]);

  const filteredNotes = notes
    .filter(n => selectedCategory === 'All' || n.category === selectedCategory)
    .filter(n =>
      searchQuery === '' ||
      n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.content.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => {
      if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
      return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
    });

  const wordCount = notes.reduce((sum, n) => sum + n.content.split(/\s+/).filter(Boolean).length, 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="component-container"
      style={{ maxWidth: '1000px', margin: '0 auto' }}
    >
      <h2>📓 Study Notes</h2>
      <p>Capture and organise your learning notes</p>

      {/* Stats Bar */}
      <div style={{
        display: 'flex',
        gap: '1.5rem',
        marginBottom: '1.5rem',
        padding: '1rem 1.5rem',
        background: 'var(--bg-dark)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        flexWrap: 'wrap'
      }}>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          📝 <strong style={{ color: 'var(--primary)' }}>{notes.length}</strong> notes
        </span>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          📌 <strong style={{ color: 'var(--warning)' }}>{notes.filter(n => n.pinned).length}</strong> pinned
        </span>
        <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          📊 <strong style={{ color: 'var(--accent)' }}>{wordCount}</strong> words total
        </span>
        {notes.length > 0 && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={exportNotes}
            style={{
              marginLeft: 'auto',
              padding: '0.35rem 1rem',
              background: 'rgba(99,102,241,0.1)',
              border: '1px solid var(--primary)',
              borderRadius: '8px',
              color: 'var(--primary)',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            ⬇️ Export Markdown
          </motion.button>
        )}
      </div>

      {/* Search & Filter */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="🔍 Search notes..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          style={{
            flex: 1,
            minWidth: '200px',
            padding: '0.75rem 1rem',
            background: 'var(--bg-dark)',
            border: '1px solid var(--border)',
            borderRadius: '10px',
            color: 'var(--text-primary)',
            fontSize: '0.95rem'
          }}
        />
        <select
          value={selectedCategory}
          onChange={e => setSelectedCategory(e.target.value)}
          style={{
            padding: '0.75rem 1rem',
            background: 'var(--bg-dark)',
            border: '1px solid var(--border)',
            borderRadius: '10px',
            color: 'var(--text-primary)',
            fontSize: '0.95rem'
          }}
        >
          <option value="All">All Categories</option>
          {CATEGORIES.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => { setIsCreating(!isCreating); setEditingNote(null); }}
          style={{
            padding: '0.75rem 1.5rem',
            background: isCreating ? 'var(--bg-card)' : 'linear-gradient(135deg, var(--primary), var(--primary-dark))',
            border: isCreating ? '1px solid var(--border)' : 'none',
            borderRadius: '10px',
            color: 'white',
            fontSize: '0.95rem',
            fontWeight: 700,
            cursor: 'pointer'
          }}
        >
          {isCreating ? '✕ Cancel' : '＋ New Note'}
        </motion.button>
      </div>

      {/* Create / Edit Form */}
      <AnimatePresence>
        {(isCreating || editingNote) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            style={{
              background: 'var(--bg-dark)',
              border: '1px solid var(--border)',
              borderRadius: '12px',
              padding: '1.5rem',
              marginBottom: '1.5rem',
              overflow: 'hidden'
            }}
          >
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>
              {editingNote ? '✏️ Edit Note' : '📝 New Note'}
            </h3>
            <div className="form-group" style={{ marginBottom: '0.75rem' }}>
              <input
                type="text"
                placeholder="Note title"
                value={editingNote ? editingNote.title : newNote.title}
                onChange={e =>
                  editingNote
                    ? setEditingNote({ ...editingNote, title: e.target.value })
                    : setNewNote({ ...newNote, title: e.target.value })
                }
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem',
                  background: 'var(--bg-darker)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                  fontSize: '1rem'
                }}
              />
            </div>
            <div className="form-group" style={{ marginBottom: '0.75rem' }}>
              <textarea
                placeholder="Write your notes here..."
                rows={6}
                value={editingNote ? editingNote.content : newNote.content}
                onChange={e =>
                  editingNote
                    ? setEditingNote({ ...editingNote, content: e.target.value })
                    : setNewNote({ ...newNote, content: e.target.value })
                }
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem',
                  background: 'var(--bg-darker)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                  fontSize: '0.95rem',
                  resize: 'vertical',
                  fontFamily: 'inherit',
                  lineHeight: 1.6
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <select
                value={editingNote ? editingNote.category : newNote.category}
                onChange={e =>
                  editingNote
                    ? setEditingNote({ ...editingNote, category: e.target.value })
                    : setNewNote({ ...newNote, category: e.target.value })
                }
                style={{
                  padding: '0.6rem 1rem',
                  background: 'var(--bg-darker)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem'
                }}
              >
                {CATEGORIES.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={editingNote ? updateNote : createNote}
                className="btn-primary"
                style={{ padding: '0.6rem 1.5rem', width: 'auto' }}
              >
                {editingNote ? '💾 Save Changes' : '✅ Create Note'}
              </motion.button>
              {editingNote && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setEditingNote(null)}
                  style={{
                    padding: '0.6rem 1rem',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    color: 'var(--text-primary)',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </motion.button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Notes List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <AnimatePresence>
          {filteredNotes.map((note, index) => (
            <motion.div
              key={note.id}
              layout
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ delay: index * 0.05 }}
              style={{
                background: 'var(--bg-dark)',
                border: `1px solid ${note.pinned ? 'var(--warning)' : 'var(--border)'}`,
                borderRadius: '12px',
                padding: '1.25rem',
                position: 'relative'
              }}
            >
              {note.pinned && (
                <div style={{ position: 'absolute', top: '0.75rem', right: '0.75rem', fontSize: '1.1rem' }}>📌</div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                <h3 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '1.1rem', flex: 1 }}>
                  {note.title}
                </h3>
                <span style={{
                  padding: '0.2rem 0.6rem',
                  background: 'rgba(99,102,241,0.15)',
                  color: 'var(--primary-light)',
                  borderRadius: '8px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  marginLeft: '0.75rem'
                }}>
                  {note.category}
                </span>
              </div>
              <p style={{
                color: 'var(--text-secondary)',
                fontSize: '0.9rem',
                lineHeight: 1.6,
                whiteSpace: 'pre-wrap',
                marginBottom: '0.75rem',
                maxHeight: '120px',
                overflow: 'hidden'
              }}>
                {note.content || 'No content'}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  Updated {new Date(note.updatedAt).toLocaleDateString()}
                </span>
                <div style={{ display: 'flex', gap: '0.4rem' }}>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => togglePin(note.id)}
                    title={note.pinned ? 'Unpin' : 'Pin'}
                    style={{
                      padding: '0.4rem 0.6rem',
                      background: note.pinned ? 'rgba(245,158,11,0.15)' : 'var(--bg-card)',
                      border: `1px solid ${note.pinned ? 'var(--warning)' : 'var(--border)'}`,
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                      color: 'var(--text-primary)'
                    }}
                  >
                    📌
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => { setEditingNote(note); setIsCreating(false); }}
                    title="Edit"
                    style={{
                      padding: '0.4rem 0.6rem',
                      background: 'rgba(99,102,241,0.1)',
                      border: '1px solid var(--primary)',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                      color: 'var(--primary)'
                    }}
                  >
                    ✏️
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => deleteNote(note.id)}
                    title="Delete"
                    style={{
                      padding: '0.4rem 0.6rem',
                      background: 'rgba(239,68,68,0.1)',
                      border: '1px solid var(--error)',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                      color: 'var(--error)'
                    }}
                  >
                    🗑️
                  </motion.button>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {filteredNotes.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📓</div>
          <p>{notes.length === 0 ? 'No notes yet. Create your first note!' : 'No notes match your search.'}</p>
        </div>
      )}
    </motion.div>
  );
};

export default NoteTaker;
