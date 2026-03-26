'use client';

import React, { useEffect, useState } from 'react';

interface ServiceHealth {
  status: string;
  message: string;
  services: Record<string, boolean>;
  errors?: string[];
  warnings?: string[];
}

interface ServiceStatusProps {
  apiUrl: string;
}

export const ServiceStatus: React.FC<ServiceStatusProps> = ({ apiUrl }) => {
  const [health, setHealth] = useState<ServiceHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    checkHealth();
    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  const checkHealth = async () => {
    if (!apiUrl) {
      setError('API URL not configured');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/health`);
      const data = await response.json();
      setHealth(data);
      setError(null);
    } catch (err) {
      setError('Cannot connect to API server');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{
        padding: '0.5rem 1rem',
        backgroundColor: '#f0f0f0',
        borderRadius: '4px',
        fontSize: '0.9rem',
      }}>
        Checking service status...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        padding: '0.5rem 1rem',
        backgroundColor: '#ff4444',
        color: 'white',
        borderRadius: '4px',
        fontSize: '0.9rem',
        cursor: 'pointer',
      }}
      onClick={() => setExpanded(!expanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>🔴 {error}</span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              checkHealth();
            }}
            style={{
              backgroundColor: 'white',
              color: '#ff4444',
              border: 'none',
              padding: '0.25rem 0.5rem',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.8rem',
            }}
          >
            Retry
          </button>
        </div>
        {expanded && (
          <div style={{ marginTop: '0.5rem', fontSize: '0.85rem' }}>
            <p>Make sure the backend server is running:</p>
            <code style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: '4px', marginTop: '0.5rem' }}>
              python -m uvicorn app:app --reload --port 8000
            </code>
          </div>
        )}
      </div>
    );
  }

  if (!health) {
    return null;
  }

  const getStatusColor = () => {
    switch (health.status) {
      case 'healthy':
        return '#4caf50';
      case 'degraded':
        return '#ff9800';
      case 'unhealthy':
        return '#ff4444';
      default:
        return '#9e9e9e';
    }
  };

  const getStatusIcon = () => {
    switch (health.status) {
      case 'healthy':
        return '🟢';
      case 'degraded':
        return '🟡';
      case 'unhealthy':
        return '🔴';
      default:
        return '⚪';
    }
  };

  return (
    <div
      style={{
        padding: '0.5rem 1rem',
        backgroundColor: getStatusColor(),
        color: 'white',
        borderRadius: '4px',
        fontSize: '0.9rem',
        cursor: 'pointer',
      }}
      onClick={() => setExpanded(!expanded)}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span>{getStatusIcon()} {health.message}</span>
        <span style={{ fontSize: '0.8rem' }}>{expanded ? '▼' : '▶'}</span>
      </div>
      
      {expanded && (
        <div style={{ marginTop: '1rem', fontSize: '0.85rem' }}>
          <div style={{ marginBottom: '0.5rem' }}>
            <strong>Services:</strong>
          </div>
          {Object.entries(health.services).map(([service, status]) => (
            <div key={service} style={{ marginLeft: '1rem', marginBottom: '0.25rem' }}>
              {status ? '✓' : '✗'} {service}
            </div>
          ))}
          
          {health.errors && health.errors.length > 0 && (
            <div style={{ marginTop: '0.5rem' }}>
              <strong>Errors:</strong>
              {health.errors.map((err, i) => (
                <div key={i} style={{ marginLeft: '1rem', marginTop: '0.25rem', fontSize: '0.8rem' }}>
                  • {err}
                </div>
              ))}
            </div>
          )}
          
          {health.warnings && health.warnings.length > 0 && (
            <div style={{ marginTop: '0.5rem' }}>
              <strong>Warnings:</strong>
              {health.warnings.map((warn, i) => (
                <div key={i} style={{ marginLeft: '1rem', marginTop: '0.25rem', fontSize: '0.8rem' }}>
                  • {warn}
                </div>
              ))}
            </div>
          )}
          
          <button
            onClick={(e) => {
              e.stopPropagation();
              checkHealth();
            }}
            style={{
              marginTop: '0.5rem',
              backgroundColor: 'white',
              color: getStatusColor(),
              border: 'none',
              padding: '0.25rem 0.5rem',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.8rem',
            }}
          >
            Refresh Status
          </button>
        </div>
      )}
    </div>
  );
};
