import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ShieldCheck, LogIn, ShieldAlert, Radio, Eye } from 'lucide-react';
import { useAuth } from '@/auth/AuthContext';
import { Button, Spinner } from '@/components/ui/button';
import { Input, FormField } from '@/components/ui/form';

const DEMO_ACCOUNTS = [
  { username: 'admin', password: 'password', label: 'Admin', desc: 'Full access', icon: <ShieldAlert className="h-4 w-4" /> },
  { username: 'responder', password: 'password', label: 'Responder', desc: 'Field operations', icon: <Radio className="h-4 w-4" /> },
  { username: 'viewer', password: 'password', label: 'Viewer', desc: 'Read-only', icon: <Eye className="h-4 w-4" /> },
];

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? '/dashboard';

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    if (!username || !password) {
      setError('Please enter your username and password.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await login({ username, password });
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  function fillDemo(u: string, p: string) {
    setUsername(u);
    setPassword(p);
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-900 px-4">
      <div className="absolute -top-32 -left-32 h-96 w-96 rounded-full bg-brand-600/30 blur-3xl" />
      <div className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-danger-600/20 blur-3xl" />
      <div className="relative w-full max-w-md">
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-white shadow-lg shadow-brand-600/40">
            <ShieldCheck className="h-8 w-8" />
          </div>
          <h1 className="mt-4 text-2xl font-bold text-white">Disaster Prep</h1>
          <p className="mt-1 text-sm text-slate-400">Local Disaster Preparedness System</p>
        </div>

        <form onSubmit={handleSubmit} className="rounded-2xl border border-white/10 bg-white p-6 shadow-2xl">
          <h2 className="text-lg font-semibold text-slate-900">Sign in</h2>
          <p className="mt-0.5 text-sm text-slate-500">Use an account provided by your local DRRM office.</p>
          <div className="mt-5 space-y-4">
            <FormField label="Username" required>
              <Input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. admin"
                autoComplete="username"
              />
            </FormField>
            <FormField label="Password" required>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
              />
            </FormField>
            {error && (
              <div className="rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-sm text-danger-700">
                {error}
              </div>
            )}
            <Button type="submit" className="w-full" loading={loading}>
              {!loading && <LogIn className="h-4 w-4" />}
              Sign in
            </Button>
          </div>
        </form>

        <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur">
          <p className="mb-2.5 text-center text-xs font-medium uppercase tracking-wider text-slate-400">
            Demo accounts
          </p>
          <div className="grid grid-cols-3 gap-2">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.username}
                type="button"
                onClick={() => fillDemo(acc.username, acc.password)}
                className="flex flex-col items-center gap-1 rounded-lg border border-white/10 bg-white/5 p-2.5 text-center transition-colors hover:border-brand-400 hover:bg-brand-500/10"
              >
                <span className="text-brand-300">{acc.icon}</span>
                <span className="text-xs font-semibold text-white">{acc.label}</span>
                <span className="text-[10px] leading-tight text-slate-400">{acc.desc}</span>
              </button>
            ))}
          </div>
          <p className="mt-2.5 text-center text-[11px] text-slate-400">
            Click a card to fill credentials, then press sign in. This uses the live local API when available.
          </p>
          {loading && (
            <div className="mt-2 flex items-center justify-center gap-2 text-xs text-slate-300">
              <Spinner className="h-3.5 w-3.5" /> Authenticating…
            </div>
          )}
        </div>
      </div>
    </div>
  );
}