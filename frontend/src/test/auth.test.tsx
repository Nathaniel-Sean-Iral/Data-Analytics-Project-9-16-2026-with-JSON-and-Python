import { describe, expect, it, vi, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/auth/AuthContext';
import { setSession } from '@/api/client';
import type { User } from '@/api/types';

const MOCK_USER: User = {
  id: 1,
  username: 'admin',
  full_name: 'Admin User',
  role: 'admin',
};

function Protected({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <p>login required</p>;
}

function renderApp() {
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <AuthProvider>
        <Routes>
          <Route
            path="/dashboard"
            element={
              <Protected>
                <p>dashboard content</p>
              </Protected>
            }
          />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

function unauthorized() {
  return vi.fn().mockResolvedValue({
    status: 401,
    ok: false,
    headers: { get: () => 'application/json' },
    json: async () => ({ detail: 'Session expired' }),
    text: async () => 'Session expired',
  });
}

describe('AuthProvider session invalidation', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('treats a stored session as authenticated on first render', () => {
    setSession({ access_token: 'token', token_type: 'bearer', user: MOCK_USER });
    renderApp();
    expect(screen.getByText('dashboard content')).toBeInTheDocument();
  });

  // Regression: the 401 handler cleared localStorage but left AuthContext state
  // intact, so the app stayed on protected pages re-issuing failing requests.
  it('drops the user when a request comes back 401', async () => {
    setSession({ access_token: 'stale-token', token_type: 'bearer', user: MOCK_USER });
    renderApp();
    expect(screen.getByText('dashboard content')).toBeInTheDocument();

    const { http } = await import('@/api/client');
    vi.stubGlobal('fetch', unauthorized());
    await act(async () => {
      await expect(http.get('/centers')).rejects.toMatchObject({ status: 401 });
    });

    expect(screen.getByText('login required')).toBeInTheDocument();
  });
});
