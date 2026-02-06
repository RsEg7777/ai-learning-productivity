import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface GamificationDashboardProps {
  authToken: string;
}

interface UserStats {
  xp: number;
  level: number;
  streak: number;
  achievements: Achievement[];
  leaderboard_rank: number;
}

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  unlocked: boolean;
  progress?: number;
  max_progress?: number;
}

const GamificationDashboard: React.FC<GamificationDashboardProps> = ({ authToken }) => {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || ''}/gamification/stats/user123`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      const data = await response.json();
      if (data.success) {
        setStats(data.stats);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: '#00ffff' }}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          style={{ fontSize: '3rem' }}
        >
          ⚡
        </motion.div>
        <p>Loading your stats...</p>
      </div>
    );
  }

  const xpForNextLevel = stats ? Math.pow(stats.level + 1, 2) * 100 : 100;
  const xpProgress = stats ? (stats.xp % xpForNextLevel) / xpForNextLevel * 100 : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}
    >
      <h2 style={{ color: '#00ffff', marginBottom: '2rem', fontSize: '2rem', textAlign: 'center' }}>
        🎮 Your Gaming Stats
      </h2>

      {/* Stats Grid */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: '1.5rem',
        marginBottom: '2rem'
      }}>
        {/* Level Card */}
        <motion.div
          whileHover={{ scale: 1.05, boxShadow: '0 0 30px rgba(0, 255, 255, 0.3)' }}
          style={{
            background: 'linear-gradient(135deg, rgba(0, 255, 255, 0.1) 0%, rgba(0, 200, 200, 0.1) 100%)',
            border: '2px solid rgba(0, 255, 255, 0.3)',
            borderRadius: '16px',
            padding: '1.5rem',
            textAlign: 'center'
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>⭐</div>
          <h3 style={{ color: '#00ffff', fontSize: '1.2rem', marginBottom: '0.5rem' }}>Level</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#fff' }}>
            {stats?.level || 1}
          </div>
          <div style={{ 
            width: '100%', 
            height: '8px', 
            background: 'rgba(0, 0, 0, 0.5)',
            borderRadius: '4px',
            marginTop: '1rem',
            overflow: 'hidden'
          }}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${xpProgress}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
              style={{
                height: '100%',
                background: 'linear-gradient(90deg, #00ffff, #00cccc)',
                borderRadius: '4px'
              }}
            />
          </div>
          <p style={{ color: '#888', fontSize: '0.85rem', marginTop: '0.5rem' }}>
            {stats?.xp || 0} / {xpForNextLevel} XP
          </p>
        </motion.div>

        {/* Streak Card */}
        <motion.div
          whileHover={{ scale: 1.05, boxShadow: '0 0 30px rgba(255, 165, 0, 0.3)' }}
          style={{
            background: 'linear-gradient(135deg, rgba(255, 165, 0, 0.1) 0%, rgba(255, 140, 0, 0.1) 100%)',
            border: '2px solid rgba(255, 165, 0, 0.3)',
            borderRadius: '16px',
            padding: '1.5rem',
            textAlign: 'center'
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>🔥</div>
          <h3 style={{ color: '#ffa500', fontSize: '1.2rem', marginBottom: '0.5rem' }}>Streak</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#fff' }}>
            {stats?.streak || 0}
          </div>
          <p style={{ color: '#888', fontSize: '0.85rem', marginTop: '0.5rem' }}>
            days in a row
          </p>
        </motion.div>

        {/* Rank Card */}
        <motion.div
          whileHover={{ scale: 1.05, boxShadow: '0 0 30px rgba(255, 215, 0, 0.3)' }}
          style={{
            background: 'linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 193, 7, 0.1) 100%)',
            border: '2px solid rgba(255, 215, 0, 0.3)',
            borderRadius: '16px',
            padding: '1.5rem',
            textAlign: 'center'
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>🏆</div>
          <h3 style={{ color: '#ffd700', fontSize: '1.2rem', marginBottom: '0.5rem' }}>Rank</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#fff' }}>
            #{stats?.leaderboard_rank || 'N/A'}
          </div>
          <p style={{ color: '#888', fontSize: '0.85rem', marginTop: '0.5rem' }}>
            on leaderboard
          </p>
        </motion.div>
      </div>

      {/* Achievements */}
      <div style={{
        background: 'rgba(0, 255, 255, 0.05)',
        border: '1px solid rgba(0, 255, 255, 0.2)',
        borderRadius: '16px',
        padding: '2rem'
      }}>
        <h3 style={{ color: '#00ffff', fontSize: '1.5rem', marginBottom: '1.5rem' }}>
          🏅 Achievements
        </h3>
        
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
          gap: '1rem'
        }}>
          {stats?.achievements?.slice(0, 6).map((achievement, index) => (
            <motion.div
              key={achievement.id}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.05 }}
              style={{
                background: achievement.unlocked 
                  ? 'rgba(0, 255, 255, 0.1)' 
                  : 'rgba(100, 100, 100, 0.1)',
                border: `1px solid ${achievement.unlocked ? 'rgba(0, 255, 255, 0.3)' : 'rgba(100, 100, 100, 0.3)'}`,
                borderRadius: '12px',
                padding: '1rem',
                textAlign: 'center',
                opacity: achievement.unlocked ? 1 : 0.5
              }}
            >
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>
                {achievement.icon}
              </div>
              <h4 style={{ 
                color: achievement.unlocked ? '#00ffff' : '#888', 
                fontSize: '0.9rem',
                marginBottom: '0.3rem'
              }}>
                {achievement.name}
              </h4>
              <p style={{ color: '#888', fontSize: '0.75rem' }}>
                {achievement.description}
              </p>
              {achievement.progress !== undefined && (
                <div style={{ marginTop: '0.5rem' }}>
                  <div style={{ 
                    width: '100%', 
                    height: '4px', 
                    background: 'rgba(0, 0, 0, 0.5)',
                    borderRadius: '2px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${(achievement.progress / (achievement.max_progress || 1)) * 100}%`,
                      height: '100%',
                      background: '#00ffff',
                      borderRadius: '2px'
                    }} />
                  </div>
                  <p style={{ color: '#888', fontSize: '0.7rem', marginTop: '0.2rem' }}>
                    {achievement.progress}/{achievement.max_progress}
                  </p>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default GamificationDashboard;
