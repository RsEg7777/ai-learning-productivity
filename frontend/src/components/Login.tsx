import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface LoginProps {
  onLogin: (token: string) => void;
}

const containerVariants = {
  initial: { opacity: 0, scale: 0.8 },
  animate: { 
    opacity: 1, 
    scale: 1,
    transition: {
      duration: 0.6,
      ease: [0.6, -0.05, 0.01, 0.99] as any
    }
  }
};

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGoogleLogin = () => {
    // Cognito Hosted UI for Google Sign-In
    const cognitoDomain = 'https://ai-learning-assistant-2026.auth.ap-south-1.amazoncognito.com';
    const clientId = '49n7akp9lublvpa04dbt2qjoa2';
    const redirectUri = encodeURIComponent(window.location.origin);
    const responseType = 'token';
    
    const googleLoginUrl = `${cognitoDomain}/oauth2/authorize?identity_provider=Google&redirect_uri=${redirectUri}&response_type=${responseType}&client_id=${clientId}&scope=email+openid+profile`;
    
    window.location.href = googleLoginUrl;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password');
      setLoading(false);
      return;
    }

    try {
      // AWS Cognito authentication
      const response = await fetch('https://cognito-idp.ap-south-1.amazonaws.com/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-amz-json-1.1',
          'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth'
        },
        body: JSON.stringify({
          AuthFlow: 'USER_PASSWORD_AUTH',
          ClientId: '49n7akp9lublvpa04dbt2qjoa2',
          AuthParameters: {
            USERNAME: username,
            PASSWORD: password
          }
        })
      });

      const data = await response.json();

      if (data.AuthenticationResult && data.AuthenticationResult.IdToken) {
        // Store token in localStorage
        localStorage.setItem('authToken', data.AuthenticationResult.IdToken);
        localStorage.setItem('username', username);
        onLogin(data.AuthenticationResult.IdToken);
      } else {
        setError(data.message || 'Authentication failed. Please check your credentials.');
      }
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <motion.div 
        className="login-box"
        variants={containerVariants}
        initial="initial"
        animate="animate"
      >
        <motion.h2
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
        >
          🎓 AI Learning Assistant
        </motion.h2>
        
        <motion.p 
          style={{ textAlign: 'center', marginBottom: '2rem', color: '#00ffff' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.6 }}
        >
          Sign in to access your learning dashboard
        </motion.p>
        
        {error && (
          <motion.div 
            className="error"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            style={{ 
              background: 'rgba(255, 0, 0, 0.1)', 
              border: '1px solid rgba(255, 0, 0, 0.3)',
              padding: '1rem',
              borderRadius: '8px',
              marginBottom: '1rem',
              color: '#ff6b6b'
            }}
          >
            {error}
          </motion.div>
        )}

        {/* Google Sign-In Button */}
        <motion.button
          onClick={handleGoogleLogin}
          className="btn-google"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          whileHover={{ scale: 1.02, boxShadow: '0 0 30px rgba(0, 255, 255, 0.3)' }}
          whileTap={{ scale: 0.98 }}
          style={{
            width: '100%',
            padding: '1rem',
            marginBottom: '1.5rem',
            background: 'rgba(255, 255, 255, 0.95)',
            border: '2px solid rgba(0, 255, 255, 0.3)',
            borderRadius: '12px',
            cursor: 'pointer',
            fontSize: '1rem',
            fontWeight: '600',
            color: '#0a0e1a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.75rem',
            transition: 'all 0.3s ease'
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continue with Google
        </motion.button>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            margin: '1.5rem 0',
            color: '#88C0D0'
          }}
        >
          <div style={{ flex: 1, height: '1px', background: 'rgba(0, 255, 255, 0.2)' }} />
          <span style={{ fontSize: '0.9rem' }}>OR</span>
          <div style={{ flex: 1, height: '1px', background: 'rgba(0, 255, 255, 0.2)' }} />
        </motion.div>
        
        <form onSubmit={handleSubmit}>
          <motion.div 
            className="form-group"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.6 }}
          >
            <label>Username:</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              disabled={loading}
              autoComplete="username"
            />
          </motion.div>
          
          <motion.div 
            className="form-group"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.6 }}
          >
            <label>Password:</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              disabled={loading}
              autoComplete="current-password"
            />
          </motion.div>
          
          <motion.button 
            type="submit" 
            className="btn-primary"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.6 }}
            whileHover={{ scale: loading ? 1 : 1.02 }}
            whileTap={{ scale: loading ? 1 : 0.98 }}
            disabled={loading}
            style={{ opacity: loading ? 0.7 : 1 }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </motion.button>
        </form>
        
        <motion.div 
          style={{ 
            marginTop: '1.5rem', 
            padding: '1rem', 
            background: 'rgba(0, 255, 255, 0.05)', 
            border: '1px solid rgba(0, 255, 255, 0.2)',
            borderRadius: '12px' 
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9, duration: 0.6 }}
        >
          <p style={{ fontSize: '0.9rem', color: '#00ffff', marginBottom: '0.5rem' }}>
            <strong>Demo Credentials:</strong>
          </p>
          <p style={{ fontSize: '0.85rem', color: '#88C0D0', margin: '0.25rem 0' }}>
            Username: <code style={{ color: '#00ffff' }}>testuser</code>
          </p>
          <p style={{ fontSize: '0.85rem', color: '#88C0D0', margin: '0.25rem 0' }}>
            Password: <code style={{ color: '#00ffff' }}>TestPass123!</code>
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default Login;
