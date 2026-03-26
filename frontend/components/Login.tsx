'use client';
import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface LoginProps { onLogin: (token: string) => void; }

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGuestLogin = () => {
    const token = 'guest_' + Date.now();
    localStorage.setItem('authToken', token);
    localStorage.setItem('username', 'Guest');
    onLogin(token);
  };

  const handleGoogleLogin = () => {
    const cognitoDomain = 'https://ai-learning-assistant-2026.auth.ap-south-1.amazoncognito.com';
    const clientId = '49n7akp9lublvpa04dbt2qjoa2';
    const redirectUri = encodeURIComponent(typeof window !== 'undefined' ? window.location.origin : '');
    window.location.href = `${cognitoDomain}/oauth2/authorize?identity_provider=Google&redirect_uri=${redirectUri}&response_type=token&client_id=${clientId}&scope=email+openid+profile`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(''); setLoading(true);
    if (!username.trim() || !password.trim()) { setError('Please enter both username and password'); setLoading(false); return; }
    try {
      const res = await fetch('https://cognito-idp.ap-south-1.amazonaws.com/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-amz-json-1.1', 'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth' },
        body: JSON.stringify({ AuthFlow: 'USER_PASSWORD_AUTH', ClientId: '49n7akp9lublvpa04dbt2qjoa2', AuthParameters: { USERNAME: username, PASSWORD: password } }),
      });
      const data = await res.json();
      if (data.AuthenticationResult?.IdToken) {
        localStorage.setItem('authToken', data.AuthenticationResult.IdToken);
        localStorage.setItem('username', username);
        onLogin(data.AuthenticationResult.IdToken);
      } else { setError(data.message || 'Authentication failed'); }
    } catch (err: any) { setError(err.message || 'Login failed'); }
    finally { setLoading(false); }
  };

  return (
    <div className="login-container">
      {/* Floating orbs */}
      {[
        { size: 320, top: '-80px', left: '-80px', color: 'rgba(99,102,241,0.15)' },
        { size: 240, bottom: '-60px', right: '-60px', color: 'rgba(139,92,246,0.12)' },
        { size: 180, top: '40%', right: '15%', color: 'rgba(6,182,212,0.08)' },
      ].map((orb, i) => (
        <div key={i} style={{ position: 'fixed', width: orb.size, height: orb.size, borderRadius: '50%',
          background: orb.color, filter: 'blur(60px)', pointerEvents: 'none', zIndex: 0,
          top: (orb as any).top, left: (orb as any).left, right: (orb as any).right, bottom: (orb as any).bottom }} />
      ))}

      <motion.div className="login-box"
        initial={{ opacity: 0, scale: .9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: .6, ease: [.16, 1, .3, 1] }}>

        <div className="login-brand">
          <motion.div className="login-brand-icon"
            animate={{ boxShadow: ['0 0 20px rgba(99,102,241,0.3)', '0 0 40px rgba(99,102,241,0.5)', '0 0 20px rgba(99,102,241,0.3)'] }}
            transition={{ duration: 3, repeat: Infinity }}>
            🎓
          </motion.div>
          <h2>AI Learning Assistant</h2>
          <p className="login-subtitle">AWS AI Bharat Hackathon 2026 · Powered by Amazon Bedrock</p>
        </div>

        {error && (
          <motion.div className="error" initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }}>
            ⚠️ {error}
          </motion.div>
        )}

        {/* Guest mode */}
        <motion.button className="btn-guest" onClick={handleGuestLogin}
          whileHover={{ scale: 1.02 }} whileTap={{ scale: .98 }}
          style={{ marginBottom: '1rem' }}>
          🚀 Continue as Guest (Demo Mode)
        </motion.button>

        {/* Google */}
        <motion.button className="btn-google" onClick={handleGoogleLogin}
          whileHover={{ scale: 1.02 }} whileTap={{ scale: .98 }}>
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Sign in with Google
        </motion.button>

        <div className="login-divider">or</div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)}
              placeholder="Enter your username" disabled={loading} autoComplete="username" />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="Enter your password" disabled={loading} autoComplete="current-password" />
          </div>
          <motion.button type="submit" className="btn-primary"
            whileHover={{ scale: loading ? 1 : 1.02 }} whileTap={{ scale: loading ? 1 : .98 }}
            disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </motion.button>
        </form>

        <div className="demo-hint">
          <p style={{ fontWeight: 600, color: 'var(--indigo-light)', marginBottom: '.4rem' }}>🔑 Demo Credentials</p>
          <p>Username: <code>testuser</code></p>
          <p>Password: <code>TestPass123!</code></p>
          <p style={{ marginTop: '.4rem', fontSize: '.75rem' }}>Or click <strong style={{ color: 'var(--indigo-light)' }}>Continue as Guest</strong> for instant access</p>
        </div>
      </motion.div>
    </div>
  );
};
export default Login;
