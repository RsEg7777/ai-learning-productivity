import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders AI Learning Assistant', () => {
  render(<App />);
  const titleElement = screen.getByText(/AI Learning Assistant/i);
  expect(titleElement).toBeInTheDocument();
});

test('renders login page when not authenticated', () => {
  render(<App />);
  const googleButton = screen.getByText(/Continue with Google/i);
  expect(googleButton).toBeInTheDocument();
});
