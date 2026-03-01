import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface StudyTimerProps {
  authToken: string;
}

const StudyTimer: React.FC<StudyTimerProps> = ({ authToken }) => {
  const [minutes, setMinutes] = useState(25);
  const [seconds, setSeconds] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const [mode, setMode] = useState<'work' | 'break'>('work');
  const [sessionsCompleted, setSessionsCompleted] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isActive) {
      intervalRef.current = setInterval(() => {
        if (seconds === 0) {
          if (minutes === 0) {
            // Timer completed
            handleTimerComplete();
          } else {
            setMinutes(minutes - 1);
            setSeconds(59);
          }
        } else {
          setSeconds(seconds - 1);
        }
      }, 1000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive, minutes, seconds]);

  const handleTimerComplete = () => {
    setIsActive(false);
    if (mode === 'work') {
      setSessionsCompleted(sessionsCompleted + 1);
      setMode('break');
      setMinutes(5);
      setSeconds(0);
      new Notification('Study Session Complete!', {
        body: 'Time for a 5-minute break!',
      });
    } else {
      setMode('work');
      setMinutes(25);
      setSeconds(0);
      new Notification('Break Complete!', {
        body: 'Ready for another study session?',
      });
    }
  };

  const toggleTimer = () => {
    if (!isActive && 'Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
    setIsActive(!isActive);
  };

  const resetTimer = () => {
    setIsActive(false);
    setMode('work');
    setMinutes(25);
    setSeconds(0);
  };

  const formatTime = (mins: number, secs: number) => {
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = mode === 'work' 
    ? ((25 * 60 - (minutes * 60 + seconds)) / (25 * 60)) * 100
    : ((5 * 60 - (minutes * 60 + seconds)) / (5 * 60)) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="component-container"
      style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}
    >
      <h2>⏱️ Pomodoro Study Timer</h2>
      <p>Stay focused with the Pomodoro Technique</p>

      <div style={{
        background: 'var(--bg-dark)',
        border: '2px solid var(--border)',
        borderRadius: '20px',
        padding: '3rem 2rem',
        marginBottom: '2rem',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Progress Ring */}
        <svg width="250" height="250" style={{ margin: '0 auto', display: 'block' }}>
          <circle
            cx="125"
            cy="125"
            r="110"
            fill="none"
            stroke="var(--border)"
            strokeWidth="12"
          />
          <motion.circle
            cx="125"
            cy="125"
            r="110"
            fill="none"
            stroke={mode === 'work' ? 'var(--primary)' : 'var(--success)'}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={2 * Math.PI * 110}
            strokeDashoffset={2 * Math.PI * 110 * (1 - progress / 100)}
            transform="rotate(-90 125 125)"
            initial={false}
            animate={{ strokeDashoffset: 2 * Math.PI * 110 * (1 - progress / 100) }}
            transition={{ duration: 0.5 }}
          />
        </svg>

        {/* Timer Display */}
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          marginTop: '1rem'
        }}>
          <div style={{
            fontSize: '3.5rem',
            fontWeight: 'bold',
            color: 'var(--text-primary)',
            fontFamily: 'JetBrains Mono, monospace',
            marginBottom: '0.5rem'
          }}>
            {formatTime(minutes, seconds)}
          </div>
          <div style={{
            fontSize: '1rem',
            color: mode === 'work' ? 'var(--primary)' : 'var(--success)',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '2px'
          }}>
            {mode === 'work' ? '🎯 Focus Time' : '☕ Break Time'}
          </div>
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={toggleTimer}
          style={{
            flex: 1,
            padding: '1rem',
            background: isActive 
              ? 'linear-gradient(135deg, var(--warning), var(--error))'
              : 'linear-gradient(135deg, var(--primary), var(--primary-dark))',
            border: 'none',
            borderRadius: '10px',
            color: 'white',
            fontSize: '1.1rem',
            fontWeight: 'bold',
            cursor: 'pointer',
            boxShadow: '0 4px 20px rgba(99, 102, 241, 0.3)'
          }}
        >
          {isActive ? '⏸️ Pause' : '▶️ Start'}
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={resetTimer}
          style={{
            padding: '1rem 1.5rem',
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: '10px',
            color: 'var(--text-primary)',
            fontSize: '1.1rem',
            fontWeight: 'bold',
            cursor: 'pointer'
          }}
        >
          🔄 Reset
        </motion.button>
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '1rem'
      }}>
        <div style={{
          background: 'var(--bg-dark)',
          border: '1px solid var(--border)',
          borderRadius: '12px',
          padding: '1.5rem',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🎯</div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--primary)' }}>
            {sessionsCompleted}
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Sessions Today
          </div>
        </div>

        <div style={{
          background: 'var(--bg-dark)',
          border: '1px solid var(--border)',
          borderRadius: '12px',
          padding: '1.5rem',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>⏰</div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--success)' }}>
            {sessionsCompleted * 25}
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Minutes Focused
          </div>
        </div>
      </div>

      <div style={{
        marginTop: '2rem',
        padding: '1rem',
        background: 'var(--bg-dark)',
        border: '1px solid var(--border)',
        borderRadius: '10px',
        color: 'var(--text-secondary)',
        fontSize: '0.9rem',
        lineHeight: '1.6'
      }}>
        <strong style={{ color: 'var(--primary)' }}>💡 Pomodoro Technique:</strong><br />
        Work for 25 minutes, then take a 5-minute break. After 4 sessions, take a longer 15-30 minute break.
      </div>
    </motion.div>
  );
};

export default StudyTimer;
