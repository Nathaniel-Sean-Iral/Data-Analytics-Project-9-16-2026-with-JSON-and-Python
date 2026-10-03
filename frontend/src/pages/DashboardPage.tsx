import { Link } from 'react-router-dom';
import {
  Users,
  AlertTriangle,
  Building2,
  Package,
  Activity,
  ChevronRight,
  UserRound,
  Siren,
  Boxes,
  Gauge,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { PageHeader, StatCard, Card, CardHeader, ProgressBar } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Spinner } from '@/components/ui/button';
import { useAsync } from '@/lib/useAsync';
import { fetchDashboardStats, fetchResourceSummaries, fetchIncidents, fetchCenterLoads } from '@/api/services';
import {
  formatNumber,
  INCIDENT_TYPE_LABELS,
  INCIDENT_TYPE_TONES,
  SEVERITY_TONES,
  STATUS_LABELS,
  STATUS_TONES,
  formatDateTime,
} from '@/lib/labels';
import { useAuth } from '@/auth/AuthContext';
import type { CenterLoad, DashboardStats, Incident, IncidentSeverity } from '@/api/types';

const SEVERITY_ORDER: Record<IncidentSeverity, number> = {
  critical: 0,
  high: 1,
  moderate: 2,
  low: 3,
};

function StatsGrid({ s }: { s: DashboardStats | null }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        label="Households"
        value={formatNumber(s?.households ?? 0)}
        icon={<Users className="h-5 w-5" />}
        iconClass="bg-brand-50 text-brand-600"
      />
      <StatCard
        label="Vulnerable Members"
        value={formatNumber(s?.vulnerable_members ?? 0)}
        icon={<UserRound className="h-5 w-5" />}
        iconClass="bg-violet-50 text-violet-600"
      />
      <StatCard
        label="Active Incidents"
        value={formatNumber(s?.active_incidents ?? 0)}
        icon={<AlertTriangle className="h-5 w-5" />}
        iconClass="bg-danger-50 text-danger-600"
      />
      <StatCard
        label="Resource Types Low on Stock"
        value={formatNumber(s?.low_stock_resources ?? 0)}
        icon={<Package className="h-5 w-5" />}
        iconClass="bg-amber-50 text-amber-600"
      />
    </div>
  );
}

function ResourceAvailabilityCard({
  chartData,
  loading,
}: {
  chartData: { name: string; available: number; required: number }[];
  loading: boolean;
}) {
  return (
    <Card className="xl:col-span-2">
      <CardHeader
        title="Resource availability by type"
        subtitle="Available stock vs. required (based on configured thresholds)"
      />
      <div className="h-72 px-4 py-3">
        {loading ? (
          <div className="flex h-full items-center justify-center">
            <Spinner className="h-6 w-6 text-brand-600" />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: '#f1f5f9' }} />
              <Legend />
              <Bar dataKey="available" name="Available" fill="#1d6cf5" radius={[4, 4, 0, 0]} />
              <Bar dataKey="required" name="Required" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  );
}

function CenterLoadsCard({
  centerLoads,
}: {
  centerLoads: CenterLoad[] | null;
}) {
  return (
    <Card>
      <CardHeader
        title="Evacuation center loads"
        subtitle="Occupancy against capacity"
        action={<Building2 className="h-4 w-4 text-slate-400" />}
      />
      <div className="space-y-4 px-5 py-4">
        {centerLoads?.map((c) => (
          <div key={c.center_id}>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="font-medium text-slate-700">{c.center_name}</span>
              <span className="text-slate-500">{c.load_percent}%</span>
            </div>
            <ProgressBar
              value={c.load_percent}
              tone={c.load_percent >= 90 ? 'red' : c.load_percent >= 70 ? 'amber' : 'green'}
            />
          </div>
        ))}
      </div>
    </Card>
  );
}

function IncidentsCard({
  incidents,
  title,
  subtitle,
}: {
  incidents: Incident[];
  title: string;
  subtitle: string;
}) {
  return (
    <Card className="xl:col-span-2">
      <CardHeader
        title={title}
        subtitle={subtitle}
        action={
          <Link to="/incidents" className="inline-flex items-center gap-1 text-xs font-medium text-brand-600 hover:text-brand-700">
            View all <ChevronRight className="h-3.5 w-3.5" />
          </Link>
        }
      />
      <div className="divide-y divide-slate-100">
        {incidents.slice(0, 5).map((inc) => (
          <Link
            key={inc.id}
            to={`/incidents/${inc.id}`}
            className="flex items-center gap-3 px-5 py-3 transition-colors hover:bg-slate-50"
          >
            <div className="rounded-lg bg-slate-100 p-2 text-slate-500">
              <Activity className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-900">{inc.title}</p>
              <p className="text-xs text-slate-500">
                {inc.barangay} · {formatDateTime(inc.reported_at)}
              </p>
            </div>
            <div className="hidden gap-1.5 sm:flex">
              <Badge tone={INCIDENT_TYPE_TONES[inc.type]}>{INCIDENT_TYPE_LABELS[inc.type]}</Badge>
              <Badge tone={SEVERITY_TONES[inc.severity]}>{inc.severity}</Badge>
              <Badge tone={STATUS_TONES[inc.status]} dot>{STATUS_LABELS[inc.status]}</Badge>
            </div>
          </Link>
        ))}
        {incidents.length === 0 && (
          <p className="px-5 py-8 text-center text-sm text-slate-500">No active incidents. All clear.</p>
        )}
      </div>
    </Card>
  );
}

function QuickSummaryCard({ s, showActions }: { s: DashboardStats | null; showActions: boolean }) {
  return (
    <Card>
      <CardHeader
        title="Quick summary"
        subtitle="Municipality readiness"
      />
      <div className="space-y-3 px-5 py-4 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-slate-600">Evacuation centers</span>
          <span className="font-semibold text-slate-900">{formatNumber(s?.centers ?? 0)}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-600">Available capacity</span>
          <span className="font-semibold text-slate-900">{formatNumber(s?.available_capacity ?? 0)}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-600">Critical incidents</span>
          <span className="font-semibold text-danger-600">{formatNumber(s?.critical_incidents ?? 0)}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-600">Assigned households</span>
          <span className="font-semibold text-slate-900">{formatNumber(s?.assigned_households ?? 0)}</span>
        </div>
        {showActions && (
          <div className="mt-4 flex gap-2 border-t border-slate-100 pt-3">
            <Link to="/allocation" className="btn-secondary flex-1 !text-xs">
              Run allocation
            </Link>
            <Link to="/simulator" className="btn-secondary flex-1 !text-xs">
              New scenario
            </Link>
          </div>
        )}
      </div>
    </Card>
  );
}

export function DashboardPage() {
  const { hasRole } = useAuth();
  const stats = useAsync(() => fetchDashboardStats());
  const summaries = useAsync(() => fetchResourceSummaries());
  const incidents = useAsync(() => fetchIncidents());
  const centerLoads = useAsync(() => fetchCenterLoads());

  if (stats.loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner className="h-8 w-8 text-brand-600" />
      </div>
    );
  }

  const s = stats.data;
  const isAdmin = hasRole('admin');
  const isResponder = !isAdmin && hasRole('responder');

  const activeIncidents = (incidents.data ?? []).filter((i) => i.status !== 'resolved');
  const severityFirst = [...activeIncidents].sort(
    (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity],
  );
  const chartData = (summaries.data ?? []).map((r) => ({
    name: r.label,
    available: r.total_on_hand,
    required: r.total_required,
  }));
  const lowStock = (summaries.data ?? [])
    .filter((r) => r.gap > 0)
    .sort((a, b) => b.gap - a.gap);

  // ---- Admin: unchanged section order and content -------------------------------
  if (isAdmin) {
    return (
      <div>
        <PageHeader
          title="Operations Dashboard"
          description="Real-time snapshot of households, centers, resources and active incidents."
        />

        <StatsGrid s={s} />

        <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
          <ResourceAvailabilityCard chartData={chartData} loading={summaries.loading} />
          <CenterLoadsCard centerLoads={centerLoads.data} />
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
          <IncidentsCard incidents={activeIncidents} title="Active incidents" subtitle="Most recent first" />
          <QuickSummaryCard s={s} showActions />
        </div>
      </div>
    );
  }

  // ---- Responder: action-first, severity-ordered ------------------------------
  if (isResponder) {
    return (
      <div>
        <PageHeader
          title="Incident Response"
          description="Active hazards first. Report, allocate, and monitor municipal response."
        />

        <Card className="p-4">
          <p className="mb-3 text-xs font-medium uppercase text-slate-500">Quick actions</p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Link to="/incidents" className="btn-primary flex items-center justify-center gap-1.5 !text-xs">
              <Siren className="h-4 w-4" />
              Report incident
            </Link>
            <Link to="/allocation" className="btn-secondary flex items-center justify-center gap-1.5 !text-xs">
              <Boxes className="h-4 w-4" />
              Run allocation
            </Link>
            <Link to="/simulator" className="btn-secondary flex items-center justify-center gap-1.5 !text-xs">
              <Gauge className="h-4 w-4" />
              New scenario
            </Link>
            <Link to="/map" className="btn-secondary flex items-center justify-center gap-1.5 !text-xs">
              <Activity className="h-4 w-4" />
              Open map
            </Link>
          </div>
        </Card>

        <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
          <IncidentsCard incidents={severityFirst} title="Active incidents by severity" subtitle="Critical first" />
          <Card>
            <CardHeader
              title="Low-stock alerts"
              subtitle="Shortfall against configured thresholds"
              action={<Package className="h-4 w-4 text-slate-400" />}
            />
            <div className="divide-y divide-slate-100">
              {lowStock.slice(0, 5).map((r) => (
                <div key={r.type} className="flex items-center gap-3 px-5 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-slate-900">{r.label}</p>
                    <p className="text-xs text-slate-500">
                      {formatNumber(r.total_on_hand)} on hand · {formatNumber(r.total_required)} required
                    </p>
                  </div>
                  <Badge tone={r.gap > r.total_required ? 'red' : 'amber'}>
                    Short {formatNumber(r.gap)}
                  </Badge>
                </div>
              ))}
              {lowStock.length === 0 && (
                <p className="px-5 py-8 text-center text-sm text-slate-500">All stock levels are at or above threshold.</p>
              )}
            </div>
          </Card>
        </div>

        <div className="mt-6">
          <StatsGrid s={s} />
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
          <CenterLoadsCard centerLoads={centerLoads.data} />
        </div>

        <div className="mt-6">
          <QuickSummaryCard s={s} showActions={false} />
        </div>
      </div>
    );
  }

  // ---- Viewer: read-only status overview ---------------------------------------
  return (
    <div>
      <PageHeader
        title="Status Overview"
        description="Current municipal readiness. This account has read-only access."
        actions={<Badge tone="slate">View only</Badge>}
      />

      <StatsGrid s={s} />

      <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
        <IncidentsCard incidents={severityFirst} title="Active incidents" subtitle="Critical first" />
        <QuickSummaryCard s={s} showActions={false} />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
        <ResourceAvailabilityCard chartData={chartData} loading={summaries.loading} />
        <CenterLoadsCard centerLoads={centerLoads.data} />
      </div>
    </div>
  );
}