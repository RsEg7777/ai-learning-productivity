'use client';
import { useEffect } from 'react';

export default function ApiGuard() {
  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || '';
    if (!apiBase && typeof window !== 'undefined') {
      const originalFetch = window.fetch.bind(window);
      // Intercept relative fetch calls and return clear JSON error instead of HTML
      (window as any).fetch = async (input: any, init?: any) => {
        try {
          const url = typeof input === 'string' ? input : input instanceof Request ? input.url : '';
          const isRelative = url && (url.startsWith('/') || (!/^[a-zA-Z][a-zA-Z\d+\-.]*:/.test(url) && !apiBase));
          if (isRelative) {
            return new Response(JSON.stringify({ error: 'API URL not configured. Set NEXT_PUBLIC_API_URL in your environment.' }), { status: 400, headers: { 'Content-Type': 'application/json' } });
          }
        } catch (e) {
          // fall through to original fetch on any unexpected issue
        }
        return originalFetch(input, init);
      };
      console.warn('ApiGuard: NEXT_PUBLIC_API_URL missing — intercepting relative fetch calls.');
    }
  }, []);
  return null;
}
