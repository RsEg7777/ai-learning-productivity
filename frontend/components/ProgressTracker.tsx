'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface ProgressTrackerProps {
  authToken: string;
}

interface LearningGoal {
  id: string;
  title: string;
  description: string;
  progress: number;
  target: number;
  category: string;
  deadline?: string;
}

const defaultGoals: LearningGoal[] = [
  {
    id: '1',
    title: 'Master Python Basics',
    description: 'Complete 50 Python exercises',
    progress: 32,
    target: 50,
    category: 'Programming',
    deadline: '2026-04-01'
  },
  {
    id: '2',
    title: 'Data Structures & Algorithms',
    description: 'Solve 100 DSA problems',
    progress: 45,
    target: 100,
    category: 'Computer Science',
    deadline: '2026-05-15'
  },
  {
    id: '3',
    title: 'Web Development',
    description: 'Build 5 full-stack projects',
    progress: 2,
    target: 5,
    category: 'Development',
    deadline: '2026-06-30'
  }
];

const loadGoals = (): LearningGoal[] => {
  try {
    const saved = localStorage.getItem('learningGoals');
    if (saved) return JSON.parse(saved);
  } catch (e) {
    console.warn('Failed to load goals from localStorage:', e);
  }
  return defaultGoals;
};

const ProgressTracker: React.FC<ProgressTrackerProps> = ({ authToken }) => {
  const [goals, setGoals] = useState<LearningGoal[]>(loadGoals);

  // Persist goals to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem('learningGoals', JSON.stringify(goals));
    } catch (e) {
      console.warn('Failed to save goals to localStorage:', e);
    }
  }, [goals]);

  const [newGoal, setNewGoal] = useState({
    title: '',
    description: '',
    target: 10,
    category: 'Programming'
  });

  const [showAddForm, setShowAddForm] = useState(false);
  const [editingGoal, setEditingGoal] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    target: 10,
    category: 'Programming'
  });

  const addGoal = () => {
    if (!newGoal.title.trim()) return;

    const goal: LearningGoal = {
      id: Date.now().toString(),
      title: newGoal.title,
      description: newGoal.description,
      progress: 0,
      target: newGoal.target,
      category: newGoal.category
    };

    setGoals([...goals, goal]);
    setNewGoal({ title: '', description: '', target: 10, category: 'Programming' });
    setShowAddForm(false);
  };

  const updateProgress = (id: string, increment: number) => {
    setGoals(goals.map(goal => {
      if (goal.id === id) {
        const newProgress = Math.max(0, Math.min(goal.progress + increment, goal.target));
        return { ...goal, progress: newProgress };
      }
      return goal;
    }));
  };

  const deleteGoal = (id: string) => {
    setGoals(goals.filter(goal => goal.id !== id));
  };

  const startEdit = (goal: LearningGoal) => {
    setEditingGoal(goal.id);
    setEditForm({
      title: goal.title,
      description: goal.description,
      target: goal.target,
      category: goal.category
    });
  };

  const saveEdit = () => {
    if (!editingGoal) return;

    setGoals(goals.map(goal => {
      if (goal.id === editingGoal) {
        return {
          ...goal,
          title: editForm.title,
          description: editForm.description,
          target: editForm.target,
          category: editForm.category
        };
      }
      return goal;
    }));

    setEditingGoal(null);
    setEditForm({ title: '', description: '', target: 10, category: 'Programming' });
  };

  const cancelEdit = () => {
    setEditingGoal(null);
    setEditForm({ title: '', description: '', target: 10, category: 'Programming' });
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      'Programming': 'var(--primary)',
      'Computer Science': 'var(--secondary)',
      'Development': 'var(--accent)',
      'Mathematics': 'var(--warning)',
      'Other': 'var(--text-secondary)'
    };
    return colors[category] || colors['Other'];
  };

  const totalProgress = goals.reduce((sum, goal) => sum + (goal.progress / goal.target) * 100, 0) / (goals.length || 1);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="component-container"
    >
      <h2>📊 Learning Progress Tracker</h2>
      <p>Track your learning goals and monitor your progress</p>

      {/* Overall Progress */}
      <div style={{
        background: 'var(--bg-dark)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        padding: '1.5rem',
        marginBottom: '2rem'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ color: 'var(--text-primary)', margin: 0 }}>Overall Progress</h3>
          <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--primary)' }}>
            {Math.round(totalProgress)}%
          </span>
        </div>
        <div style={{
          width: '100%',
          height: '12px',
          background: 'var(--border)',
          borderRadius: '6px',
          overflow: 'hidden'
        }}>
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${totalProgress}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
            style={{
              height: '100%',
              background: 'linear-gradient(90deg, var(--primary), var(--secondary))',
              borderRadius: '6px'
            }}
          />
        </div>
      </div>

      {/* Add Goal Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setShowAddForm(!showAddForm)}
        style={{
          width: '100%',
          padding: '1rem',
          background: showAddForm ? 'var(--bg-card)' : 'linear-gradient(135deg, var(--primary), var(--primary-dark))',
          border: showAddForm ? '1px solid var(--border)' : 'none',
          borderRadius: '10px',
          color: 'white',
          fontSize: '1rem',
          fontWeight: 'bold',
          cursor: 'pointer',
          marginBottom: '1.5rem'
        }}
      >
        {showAddForm ? '❌ Cancel' : '➕ Add New Goal'}
      </motion.button>

      {/* Add Goal Form */}
      {showAddForm && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          style={{
            background: 'var(--bg-dark)',
            border: '1px solid var(--border)',
            borderRadius: '12px',
            padding: '1.5rem',
            marginBottom: '2rem'
          }}
        >
          <div className="form-group">
            <label>Goal Title:</label>
            <input
              type="text"
              value={newGoal.title}
              onChange={(e) => setNewGoal({ ...newGoal, title: e.target.value })}
              placeholder="e.g., Master React Hooks"
            />
          </div>

          <div className="form-group">
            <label>Description:</label>
            <textarea
              value={newGoal.description}
              onChange={(e) => setNewGoal({ ...newGoal, description: e.target.value })}
              placeholder="Describe your goal..."
              rows={3}
            />
          </div>

          <div className="form-group">
            <label>Category:</label>
            <select
              value={newGoal.category}
              onChange={(e) => setNewGoal({ ...newGoal, category: e.target.value })}
            >
              <option value="Programming">Programming</option>
              <option value="Computer Science">Computer Science</option>
              <option value="Development">Development</option>
              <option value="Mathematics">Mathematics</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div className="form-group">
            <label>Target: {newGoal.target}</label>
            <input
              type="range"
              min="5"
              max="100"
              value={newGoal.target}
              onChange={(e) => setNewGoal({ ...newGoal, target: parseInt(e.target.value) })}
            />
          </div>

          <button
            onClick={addGoal}
            className="btn-primary"
          >
            ✅ Create Goal
          </button>
        </motion.div>
      )}

      {/* Goals List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {goals.map((goal, index) => {
          const progressPercent = (goal.progress / goal.target) * 100;
          const isComplete = goal.progress >= goal.target;

          return (
            <motion.div
              key={goal.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              style={{
                background: 'var(--bg-dark)',
                border: `1px solid ${isComplete ? 'var(--success)' : 'var(--border)'}`,
                borderRadius: '12px',
                padding: '1.5rem',
                position: 'relative',
                overflow: 'hidden'
              }}
            >
              {isComplete && (
                <div style={{
                  position: 'absolute',
                  top: '1rem',
                  right: '1rem',
                  fontSize: '2rem'
                }}>
                  🎉
                </div>
              )}

              <div style={{ marginBottom: '1rem' }}>
                {editingGoal === goal.id ? (
                  <div>
                    <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                      <input
                        type="text"
                        value={editForm.title}
                        onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                        placeholder="Goal title"
                        style={{ marginBottom: '0.5rem' }}
                      />
                    </div>
                    <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                      <textarea
                        value={editForm.description}
                        onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                        placeholder="Description"
                        rows={2}
                      />
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                      <select
                        value={editForm.category}
                        onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                        style={{ flex: 1 }}
                        className="form-group"
                      >
                        <option value="Programming">Programming</option>
                        <option value="Computer Science">Computer Science</option>
                        <option value="Development">Development</option>
                        <option value="Mathematics">Mathematics</option>
                        <option value="Other">Other</option>
                      </select>
                      <input
                        type="number"
                        value={editForm.target}
                        onChange={(e) => setEditForm({ ...editForm, target: parseInt(e.target.value) })}
                        min="5"
                        max="100"
                        style={{ width: '100px' }}
                      />
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={saveEdit}
                        style={{
                          flex: 1,
                          padding: '0.5rem',
                          background: 'var(--success)',
                          border: 'none',
                          borderRadius: '8px',
                          color: 'white',
                          fontSize: '0.85rem',
                          fontWeight: 'bold',
                          cursor: 'pointer'
                        }}
                      >
                        ✅ Save
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={cancelEdit}
                        style={{
                          flex: 1,
                          padding: '0.5rem',
                          background: 'var(--bg-card)',
                          border: '1px solid var(--border)',
                          borderRadius: '8px',
                          color: 'var(--text-primary)',
                          fontSize: '0.85rem',
                          fontWeight: 'bold',
                          cursor: 'pointer'
                        }}
                      >
                        ❌ Cancel
                      </motion.button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                      <h3 style={{ color: 'var(--text-primary)', margin: 0, flex: 1 }}>
                        {goal.title}
                      </h3>
                      <span style={{
                        padding: '0.25rem 0.75rem',
                        background: getCategoryColor(goal.category),
                        color: 'white',
                        borderRadius: '12px',
                        fontSize: '0.75rem',
                        fontWeight: 'bold',
                        marginLeft: '1rem'
                      }}>
                        {goal.category}
                      </span>
                    </div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: '0.5rem 0' }}>
                      {goal.description}
                    </p>
                  </>
                )}
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    Progress: {goal.progress} / {goal.target}
                  </span>
                  <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>
                    {Math.round(progressPercent)}%
                  </span>
                </div>
                <div style={{
                  width: '100%',
                  height: '8px',
                  background: 'var(--border)',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progressPercent}%` }}
                    transition={{ duration: 0.5 }}
                    style={{
                      height: '100%',
                      background: isComplete 
                        ? 'var(--success)'
                        : `linear-gradient(90deg, ${getCategoryColor(goal.category)}, var(--primary))`,
                      borderRadius: '4px'
                    }}
                  />
                </div>
              </div>

              {goal.deadline && (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                  📅 Deadline: {new Date(goal.deadline).toLocaleDateString()}
                </div>
              )}

              {editingGoal !== goal.id && (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => updateProgress(goal.id, 1)}
                    disabled={isComplete}
                    style={{
                      flex: 1,
                      padding: '0.75rem',
                      background: isComplete ? 'var(--border)' : 'var(--success)',
                      border: 'none',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '0.9rem',
                      fontWeight: 'bold',
                      cursor: isComplete ? 'not-allowed' : 'pointer',
                      opacity: isComplete ? 0.5 : 1
                    }}
                  >
                    ➕ Progress
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => updateProgress(goal.id, -1)}
                    disabled={goal.progress === 0}
                    style={{
                      padding: '0.75rem 1rem',
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                      color: 'var(--text-primary)',
                      fontSize: '0.9rem',
                      fontWeight: 'bold',
                      cursor: goal.progress === 0 ? 'not-allowed' : 'pointer',
                      opacity: goal.progress === 0 ? 0.5 : 1
                    }}
                  >
                    ➖
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => startEdit(goal)}
                    style={{
                      padding: '0.75rem 1rem',
                      background: 'rgba(99, 102, 241, 0.1)',
                      border: '1px solid var(--primary)',
                      borderRadius: '8px',
                      color: 'var(--primary)',
                      fontSize: '0.9rem',
                      fontWeight: 'bold',
                      cursor: 'pointer'
                    }}
                  >
                    ✏️
                  </motion.button>

                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => deleteGoal(goal.id)}
                    style={{
                      padding: '0.75rem 1rem',
                      background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid var(--error)',
                      borderRadius: '8px',
                      color: 'var(--error)',
                      fontSize: '0.9rem',
                      fontWeight: 'bold',
                      cursor: 'pointer'
                    }}
                  >
                    🗑️
                  </motion.button>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {goals.length === 0 && (
        <div style={{
          textAlign: 'center',
          padding: '3rem',
          color: 'var(--text-secondary)'
        }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🎯</div>
          <p>No goals yet. Create your first learning goal to get started!</p>
        </div>
      )}
    </motion.div>
  );
};

export default ProgressTracker;
