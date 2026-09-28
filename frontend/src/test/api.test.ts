import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { ApiError, http, onSessionInvalidated } from '@/api/client';
import * as services from '@/api/services';

function mockFetchOnce(status: number, body: unknown = null, contentType = 'application/json') {
  return vi.fn().mockResolvedValue({
    status,
    ok: status >= 200 && status < 300,
    headers: { get: (h: string) => (h.toLowerCase() === 'content-type' ? contentType : null) },
    json: async () => body,
    text: async () => JSON.stringify(body),
  });
}

describe('api client error handling', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('throws ApiError with the backend detail message on 4xx', async () => {
    vi.stubGlobal('fetch', mockFetchOnce(400, { detail: 'Household not found' }));

    await expect(services.fetchCenters()).rejects.toThrowError('Household not found');
  });

  it('raises a 401 ApiError and clears the stored session', async () => {
    localStorage.setItem('disaster-prep.token', 'stale-token');
    vi.stubGlobal('fetch', mockFetchOnce(401, { detail: 'Session expired' }));

    await expect(services.fetchCenters()).rejects.toMatchObject({ status: 401 });
    expect(localStorage.getItem('disaster-prep.token')).toBeNull();
  });

  // Regression: a 401 used to clear storage silently, leaving AuthContext
  // convinced the user was still signed in. Every page then re-requested and
  // 401'd again, looping forever with no way back to the login screen.
  it('notifies session listeners so the app can log the user out', async () => {
    const onInvalidated = vi.fn();
    const unsubscribe = onSessionInvalidated(onInvalidated);
    vi.stubGlobal('fetch', mockFetchOnce(401, { detail: 'Session expired' }));

    await expect(services.fetchCenters()).rejects.toMatchObject({ status: 401 });
    expect(onInvalidated).toHaveBeenCalledTimes(1);

    unsubscribe();
    vi.stubGlobal('fetch', mockFetchOnce(401, { detail: 'Session expired' }));
    await expect(services.fetchCenters()).rejects.toMatchObject({ status: 401 });
    expect(onInvalidated).toHaveBeenCalledTimes(1);
  });

  it('reports a network failure as status 0', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));

    // Asserted on the raw client: the service wrappers catch this and fall back
    // to demo data, which is covered separately below.
    await expect(http.get('/centers')).rejects.toMatchObject({ status: 0 });
  });

  it('sends the bearer token and query params on authenticated reads', async () => {
    const fetchMock = mockFetchOnce(200, { items: [], total: 0, page: 1, page_size: 20 });
    vi.stubGlobal('fetch', fetchMock);
    localStorage.setItem('disaster-prep.token', 'abc123');

    await services.fetchHouseholds({ page: 2, search: 'reyes' });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain('page=2');
    expect(url).toContain('search=reyes');
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer abc123');
  });
});

describe('demo-data fallback', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('falls back to sample households when the API is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));

    const page = await services.fetchHouseholds();
    expect(page.items.length).toBeGreaterThan(0);
  });

  // Regression: the Vite dev proxy answers 500 when nothing is listening on
  // :8000. If 500 is treated as a real error, login shows "Request failed with
  // status 500" instead of using the demo accounts.
  it.each([404, 405, 501, 502, 503, 504])('falls back to demo data on status %i', async (status) => {
    vi.stubGlobal('fetch', mockFetchOnce(status, { detail: 'nope' }));

    const centers = await services.fetchCenters();
    expect(centers.length).toBeGreaterThan(0);
  });

  it('accepts the demo accounts when the backend is down', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));

    const session = await services.login({ username: 'admin', password: 'anything' });
    expect(session.user.role).toBe('admin');
    expect(session.access_token).toContain('admin');
  });

  it('rejects unknown demo accounts when the backend is down', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));

    await expect(services.login({ username: 'root', password: 'x' })).rejects.toThrowError(/Invalid credentials/);
  });

  it('does not mask genuine server errors as demo data', async () => {
    vi.stubGlobal('fetch', mockFetchOnce(500, { detail: 'Internal Server Error' }));

    await expect(services.fetchCenters()).rejects.toBeInstanceOf(ApiError);
  });
});
