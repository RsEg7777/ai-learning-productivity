'use client';
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
const API_URL = () => process.env.NEXT_PUBLIC_API_URL || '';

interface GamificationDashboardProps { authToken: string; }

const GamificationDashboard: React.FC<GamificationDashboardProps> = ({ authToken }) => {
  const [stats, setStats] = useState<any>(null);
  const [achievements, setAchievements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    if (!API_URL()) { setError('API URL not configured.'); setLoading(false); return; }
    setLoading(true); setError('');
    try {
      const [sr, ar] = await Promise.all([
        fetch(`${API_URL()}/gamification/stats/user123`, { headers: { Authorization: `Bearer ${authToken}` } }),
        fetch(`${API_URL()}/gamification/achievements/user123?include_locked=true`, { headers: { Authorization: `Bearer ${authToken}` } }),
      ]);
      if (!sr.ok || !ar.ok) throw new Error('Failed to load gamification data');
      const sd = await sr.json(); const ad = await ar.json();
      setStats(sd.stats); setAchievements(ad.achievements || []);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  if (loading) return <div className="loading"><p>Loading your stats…</p></div>;
  if (error) return <div className="component-container"><div className="error">⚠️ {error}<br /><button onClick={fetchAll} className="btn-secondary" style={{ marginTop: '0.75rem', padding: '0.5rem 1rem' }}>Retry</button></div></div>;

  const xpForNext = stats ? Math.pow((stats.level || 1) + 1, 2) * 100 : 100;
  const xpPct = stats ? Math.min(100, ((stats.total_xp || 0) % xpForNext) / xpForNext * 100) : 0;

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ maxWidth: 1100, margin: '0 auto' }}>
      <div className="component-container">
        <h2>🎮 Gamification Dashboard</h2>
        <p>Your XP, achievements, and learning streak — real-time from AWS DynamoDB</p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px,1fr))', gap: '1rem', marginBottom: '2rem' }}>
          {[
            { icon: '⭐', label: 'Level', value: stats?.level || 1, sub: `${stats?.total_xp || 0} / ${xpForNext} XP`, color: '#818cf8', prog: xpPct },
            { icon: '🔥', label: 'Streak', value: `${stats?.current_streak || 0}d`, sub: `Best: ${stats?.longest_streak || 0} days`, color: '#f97316' },
            { icon: '📝', label: 'Quizzes', value: stats?.quizzes_completed || 0, sub: 'completed', color: '#34d399' },
            { icon: '🏅', label: 'Achievements', value: stats?.achievements_unlocked || 0, sub: `of ${achievements.length} total`, color: '#fbbf24' },
          ].map(card => (
            <motion.div key={card.label} whileHover={{ scale: 1.03 }} style={{ background: 'rgba(255,255,255,0.03)', border: `1px solid ${card.color}30`, borderRadius: 18, padding: '1.5rem', textAlign: 'center', boxShadow: `0 0 25px ${card.color}15` }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>{card.icon}</div>
              <div style={{ color: card.color, fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em' }}>{card.label}</div>
              <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1.2, margin: '0.35rem 0' }}>{card.value}</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>{card.sub}</div>
              {card.prog !== undefined && (
                <div style={{ marginTop: '0.75rem', height: 5, background: 'rgba(255,255,255,0.08)', borderRadius: 99, overflow: 'hidden' }}>
                  <motion.div initial={{ width: 0 }} animate={{ width: `${card.prog}%` }} transition={{ duration: 1 }} style={{ height: '100%', background: `linear-gradient(90deg, ${card.color}, ${card.color}99)`, borderRadius: 99 }} />
                </div>
              )}
            </motion.div>
          ))}
        </div>

        <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 18, padding: '1.75rem' }}>
          <h3 style={{ color: 'var(--indigo-light)', marginBottom: '1.25rem', fontSize: '1.05rem', fontWeight: 700 }}>🏅 Achievements</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px,1fr))', gap: '0.85rem' }}>
            {achievements.slice(0, 12).map((a, i) => (
              <motion.div key={a.id} initial={{ opacity: 0, scale: 0.85 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.05 }} whileHover={{ scale: 1.05 }}
                style={{ background: a.unlocked ? 'rgba(99,102,241,0.1)' : 'rgba(255,255,255,0.02)', border: `1px solid ${a.unlocked ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.06)'}`, borderRadius: 14, padding: '1rem', textAlign: 'center', opacity: a.unlocked ? 1 : 0.45, transition: 'all 0.18s' }}>
                <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{a.icon || '🏅'}</div>
                <div style={{ color: a.unlocked ? 'var(--indigo-light)' : 'var(--text-muted)', fontSize: '0.82rem', fontWeight: 700, marginBottom: '0.25rem' }}>{a.name}</div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.74rem', lineHeight: 1.4 }}>{a.description}</div>
                {a.xp_reward && <div style={{ color: '#fbbf24', fontSize: '0.72rem', marginTop: '0.4rem' }}>+{a.xp_reward} XP</div>}
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
};
export default GamificationDashboard;
