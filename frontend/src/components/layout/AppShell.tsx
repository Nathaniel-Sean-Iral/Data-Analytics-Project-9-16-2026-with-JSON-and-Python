import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Map as MapIcon,
  Users,
  Building2,
  Package,
  Siren,
  ArrowRightLeft,
  FlaskConical,
  Menu,
  X,
  LogOut,
  ShieldCheck,
  LifeBuoy,
} from 'lucide-react';
import { useAuth } from '@/auth/AuthContext';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/cn';
import { MUNICIPALITY_LABEL } from '@/lib/location';
import type { Role } from '@/api/types';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  minRole: Role;
  end?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', icon: <LayoutDashboard className="h-4 w-4" />, minRole: 'viewer', end: true },
  { to: '/map', label: 'Operations Map', icon: <MapIcon className="h-4 w-4" />, minRole: 'viewer' },
  { to: '/households', label: 'Households', icon: <Users className="h-4 w-4" />, minRole: 'viewer' },
  { to: '/centers', label: 'Evacuation Centers', icon: <Building2 className="h-4 w-4" />, minRole: 'viewer' },
  { to: '/resources', label: 'Resources', icon: <Package className="h-4 w-4" />, minRole: 'viewer' },
  { to: '/incidents', label: 'Incidents', icon: <Siren className="h-4 w-4" />, minRole: 'viewer' },
  { to: '/allocation', label: 'Evacuation Allocation', icon: <ArrowRightLeft className="h-4 w-4" />, minRole: 'responder' },
  { to: '/simulator', label: 'Scenario Simulator', icon: <FlaskConical className="h-4 w-4" />, minRole: 'responder' },
];

const ROLE_TONE: Record<Role, 'violet' | 'blue' | 'slate'> = { admin: 'violet', responder: 'blue', viewer: 'slate' };

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const { user, hasRole } = useAuth();
  const items = NAV_ITEMS.filter((item) => hasRole(item.minRole));

  return (
    <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              isActive
                ? 'bg-brand-600 text-white shadow-sm'
                : 'text-slate-300 hover:bg-white/10 hover:text-white',
            )
          }
        >
          {item.icon}
          {item.label}
        </NavLink>
      ))}
      <div className="px-3 pt-6">
        <div className="rounded-lg border border-white/10 bg-white/5 p-3">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-300">
            <LifeBuoy className="h-4 w-4 text-brand-300" />
            {user?.full_name ?? 'User'}
          </div>
          <p className="mt-1 text-[11px] leading-relaxed text-slate-400">
            Sandbox environment — data shown is sample/demo unless the API is connected.
          </p>
        </div>
      </div>
    </nav>
  );
}

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const role = user?.role ?? 'viewer';

  return (
    <div className="flex min-h-screen bg-slate-100">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col bg-slate-900 lg:flex">
        <div className="flex items-center gap-2.5 px-5 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-bold text-white">Disaster Prep</p>
            <p className="text-[11px] text-slate-400">{MUNICIPALITY_LABEL}</p>
          </div>
        </div>
        <SidebarNav />
        <div className="border-t border-white/10 px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex min-w-0 items-center gap-2.5">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-500 text-xs font-bold text-white">
                {(user?.full_name ?? '?').split(' ').map((p) => p[0]).join('').slice(0, 2).toUpperCase()}
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-white">{user?.username}</p>
                <Badge tone={ROLE_TONE[role]} className="mt-0.5 capitalize">
                  {role}
                </Badge>
              </div>
            </div>
            <button
              onClick={() => {
                logout();
                navigate('/login');
              }}
              className="text-slate-400 hover:text-white"
              title="Log out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="fixed inset-x-0 top-0 z-40 flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 lg:hidden">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <p className="text-sm font-bold text-slate-900">Disaster Prep</p>
        </div>
        <button onClick={() => setMobileOpen(true)} className="rounded-lg p-2 text-slate-600 hover:bg-slate-100">
          <Menu className="h-5 w-5" />
        </button>
      </header>

      {/* Mobile sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-[950] lg:hidden">
          <div className="absolute inset-0 bg-slate-950/60" onClick={() => setMobileOpen(false)} />
          <aside className="absolute inset-y-0 left-0 flex w-72 flex-col bg-slate-900 shadow-xl">
            <div className="flex items-center justify-between px-5 py-5">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <p className="text-sm font-bold text-white">Disaster Prep</p>
              </div>
              <button onClick={() => setMobileOpen(false)} className="rounded-lg p-2 text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            <SidebarNav onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <main className="flex-1 lg:pl-64">
        <div className="mx-auto max-w-7xl px-4 py-6 pt-20 sm:px-6 lg:px-8 lg:pt-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}