'use client';
import { useEffect } from 'react';

export default function ApiGuard() {
  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || '';
    if (typeof window === 'undefined') return;

    const originalFetch = window.fetch.bind(window);

    // Override fetch in the browser to provide better errors when the API URL is missing
    // or when the API returns HTML (e.g., wrong endpoint) which would break JSON parsing.
    (window as any).fetch = async (input: any, init?: any) => {
      try {
        let url = '';
        if (typeof input === 'string') url = input;
        else if (input instanceof Request) url = input.url;
        else url = String(input || '');

        const looksRelative = url && (url.startsWith('/') || !/^[a-zA-Z][a-zA-Z\d+\-.]*:/.test(url));

        // If API base is not configured and the request is relative, return a clear JSON error.
        if (!apiBase && looksRelative) {
          return new Response(JSON.stringify({ error: 'API URL not configured. Set NEXT_PUBLIC_API_URL in your environment.' }), { status: 400, headers: { 'Content-Type': 'application/json' } });
        }

        // Perform the real fetch
        const resp: Response = await originalFetch(input, init);

        // Only validate responses for requests targeting the API (either relative requests
        // when apiBase is unset, or requests that include apiBase when set).
        const isApiRequest = looksRelative || (apiBase && url.includes(apiBase));
        if (isApiRequest) {
          const contentType = resp.headers ? resp.headers.get('content-type') : null;
          const isJson = contentType && contentType.includes('application/json');
          const allowedNonJson = contentType && (
            contentType.startsWith('application/octet-stream') ||
            contentType.startsWith('audio/') ||
            contentType.startsWith('image/') ||
            contentType.includes('application/pdf')
          );

          if (!isJson && !allowedNonJson) {
            // API returned HTML or another unexpected text — return a friendly JSON error
            let preview = '';
            try {
              const clone = resp.clone();
              const txt = await clone.text();
              preview = txt.slice(0, 512);
            } catch (e) {
              // ignore
            }
            const body = {
              error: 'API returned non-JSON response',
              status: resp.status,
              contentType: contentType || null,
              preview,
            };
            return new Response(JSON.stringify(body), { status: 500, headers: { 'Content-Type': 'application/json' } });
          }
        }

        return resp;
      } catch (err: any) {
        // If fetch itself failed, try original fetch once more; otherwise return JSON error
        try { return await originalFetch(input, init); } catch (_e) {
          return new Response(JSON.stringify({ error: 'Network or fetch error', detail: String(err) }), { status: 500, headers: { 'Content-Type': 'application/json' } });
        }
      }
    };

    console.warn('ApiGuard active — monitoring API responses for JSON.');
  }, []);
  return null;
}
