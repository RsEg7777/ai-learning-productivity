import React from 'react';

interface ErrorDisplayProps {
  error: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, onRetry, onDismiss }) => {
  return (
    <div style={{
      backgroundColor: '#ff4444',
      color: 'white',
      padding: '1rem',
      borderRadius: '8px',
      marginBottom: '1rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
    }}>
      <div style={{ flex: 1 }}>
        <strong>⚠️ Error:</strong> {error}
      </div>
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        {onRetry && (
          <button
            onClick={onRetry}
            style={{
              backgroundColor: 'white',
              color: '#ff4444',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            Retry
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            style={{
              backgroundColor: 'transparent',
              color: 'white',
              border: '1px solid white',
              padding: '0.5rem 1rem',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
};

interface WarningDisplayProps {
  message: string;
  onDismiss?: () => void;
}

export const WarningDisplay: React.FC<WarningDisplayProps> = ({ message, onDismiss }) => {
  return (
    <div style={{
      backgroundColor: '#ff9800',
      color: 'white',
      padding: '1rem',
      borderRadius: '8px',
      marginBottom: '1rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
    }}>
      <div style={{ flex: 1 }}>
        <strong>⚠️ Warning:</strong> {message}
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          style={{
            backgroundColor: 'transparent',
            color: 'white',
            border: '1px solid white',
            padding: '0.5rem 1rem',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Dismiss
        </button>
      )}
    </div>
  );
};

interface SuccessDisplayProps {
  message: string;
  onDismiss?: () => void;
}

export const SuccessDisplay: React.FC<SuccessDisplayProps> = ({ message, onDismiss }) => {
  return (
    <div style={{
      backgroundColor: '#4caf50',
      color: 'white',
      padding: '1rem',
      borderRadius: '8px',
      marginBottom: '1rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
    }}>
      <div style={{ flex: 1 }}>
        <strong>✓ Success:</strong> {message}
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          style={{
            backgroundColor: 'transparent',
            color: 'white',
            border: '1px solid white',
            padding: '0.5rem 1rem',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Dismiss
        </button>
      )}
    </div>
  );
};
