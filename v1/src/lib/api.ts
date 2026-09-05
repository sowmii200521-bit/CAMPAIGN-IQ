/**
 * Centralized API base URL resolver for CampaignIQ.
 * - In local development: defaults to '' (proxied by Vite to http://127.0.0.1:5000).
 * - In Vercel production: works seamlessly with relative paths (via vercel.json rewrites)
 *   or with a dedicated backend URL (via VITE_API_BASE_URL, e.g. https://your-backend.onrender.com).
 */
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export function getApiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}
