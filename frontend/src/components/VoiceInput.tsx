import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
  /** 'inline' renders a small icon button; 'standalone' renders a larger labeled button */
  variant?: 'inline' | 'standalone';
  placeholder?: string;
}

const VoiceInput: React.FC<VoiceInputProps> = ({
  onTranscript,
  disabled = false,
  variant = 'inline',
  placeholder = 'Listening...',
}) => {
  const [isListening, setIsListening] = useState(false);
  const [interimText, setInterimText] = useState('');
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      setSupported(false);
    }
    return () => {
      // Clean up on unmount
      recognitionRef.current?.abort();
    };
  }, []);

  const toggleListening = useCallback(() => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      setSupported(false);
      return;
    }

    const recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognitionRef.current = recognition;

    recognition.onstart = () => {
      setIsListening(true);
      setInterimText('');
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }

      setInterimText(interim);

      if (final) {
        onTranscript(final);
        setInterimText('');
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      setInterimText('');
    };

    recognition.onend = () => {
      setIsListening(false);
      setInterimText('');
    };

    recognition.start();
  }, [isListening, onTranscript]);

  if (!supported) {
    return null; // Don't render anything if browser doesn't support speech recognition
  }

  return (
    <div className="voice-input-wrapper" style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
      <motion.button
        type="button"
        onClick={toggleListening}
        disabled={disabled}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        className={`voice-btn ${isListening ? 'voice-btn--active' : ''} ${variant === 'standalone' ? 'voice-btn--standalone' : ''}`}
        title={isListening ? 'Stop listening' : 'Start voice input'}
        aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
      >
        {/* Mic icon */}
        <svg
          width={variant === 'standalone' ? 20 : 16}
          height={variant === 'standalone' ? 20 : 16}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <rect x="9" y="1" width="6" height="13" rx="3" />
          <path d="M5 10a7 7 0 0 0 14 0" />
          <line x1="12" y1="17" x2="12" y2="21" />
          <line x1="8" y1="21" x2="16" y2="21" />
        </svg>
        {variant === 'standalone' && (
          <span style={{ marginLeft: '0.5rem' }}>
            {isListening ? 'Stop' : 'Voice'}
          </span>
        )}
      </motion.button>

      {/* Interim transcript tooltip */}
      <AnimatePresence>
        {isListening && interimText && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="voice-interim"
          >
            {interimText || placeholder}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default VoiceInput;
