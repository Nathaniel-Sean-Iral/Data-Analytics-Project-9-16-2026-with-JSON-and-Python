import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import * as services from '@/api/services';
import { clearSession, getUser, onSessionInvalidated, setSession } from '@/api/client';
import type { LoginRequest, Role, User } from '@/api/types';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  login: (req: LoginRequest) => Promise<User>;
  logout: () => void;
  hasRole: (...roles: Role[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const ROLE_RANK: Record<Role, number> = { viewer: 1, responder: 2, admin: 3 };

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => getUser());

  const login = useCallback(async (req: LoginRequest) => {
    const res = await services.login(req);
    setSession(res);
    setUser(res.user);
    return res.user;
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setUser(null);
  }, []);

  // The API client drops the stored session whenever the backend rejects the
  // token. Mirror that into React state, otherwise a 401 (an expired token, or
  // a demo token left over from running against the mock fallback) would leave
  // the app stuck rendering authenticated pages that only ever 401.
  useEffect(() => onSessionInvalidated(() => setUser(null)), []);

  const hasRole = useCallback(
    (role: Role) => Boolean(user && ROLE_RANK[user.role] >= ROLE_RANK[role]),
    [user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: Boolean(user), login, logout, hasRole }),
    [user, login, logout, hasRole],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}