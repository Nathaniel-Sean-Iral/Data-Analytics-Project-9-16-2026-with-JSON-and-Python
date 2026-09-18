import type { AuthResponse, User } from './types';

const API_BASE = (import.meta.env.VITE_API_URL ?? '/api').replace(/\/$/, '');

const TOKEN_KEY = 'disaster-prep.token';
const USER_KEY = 'disaster-prep.user';

export class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setSession(data: AuthResponse): void {
  localStorage.setItem(TOKEN_KEY, data.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));
}

export function getUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function api<T>(
  path: string,
  options: { method?: string; body?: unknown; params?: Record<string, string | number | boolean | undefined> } = {},
): Promise<T> {
  const { method = 'GET', body, params } = options;

  const url = new URL(API_BASE + path, window.location.origin);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== '') {
        url.searchParams.set(key, String(value));
      }
    }
  }

  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';

  let response: Response;
  try {
    response = await fetch(url.toString(), {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, 'Network error — unable to reach the API.');
  }

  if (response.status === 401) {
    clearSession();
    throw new ApiError(401, 'Session expired. Please log in again.');
  }

  const isJson = Boolean(response.headers.get('content-type')?.includes('application/json'));
  const data = isJson ? await response.json().catch(() => null) : await response.text().catch(() => null);

  if (!response.ok) {
    // A non-JSON 5xx (e.g. Vite/nginx proxy "can't connect to backend", or a
    // crash dump) means the API is unreachable rather than reporting a real
    // error. Normalize it to a network error so callers fall back to demo data.
    const infraFailure = !isJson && response.status >= 500;
    const status = infraFailure ? 0 : response.status;
    let message: string;
    if (isJson && data && typeof data === 'object' && 'detail' in data) {
      message = typeof data.detail === 'string' ? data.detail : String(JSON.stringify(data.detail));
    } else if (infraFailure) {
      message = 'Network error — unable to reach the API (backend unreachable).';
    } else {
      message = typeof data === 'string' && data ? data : `Request failed with status ${response.status}`;
    }
    throw new ApiError(status, message, message);
  }

  return data as T;
}

export const http = {
  get: <T>(path: string, params?: Record<string, string | number | boolean | undefined>) =>
    api<T>(path, { params }),
  post: <T>(path: string, body?: unknown) => api<T>(path, { method: 'POST', body }),
  put: <T>(path: string, body?: unknown) => api<T>(path, { method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown) => api<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string) => api<T>(path, { method: 'DELETE' }),
};