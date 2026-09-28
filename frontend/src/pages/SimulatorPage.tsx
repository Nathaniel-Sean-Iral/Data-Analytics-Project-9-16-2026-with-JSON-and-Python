import { useState } from 'react';
import { FlaskConical, Play, Users, Building2, Package, AlertTriangle, RefreshCw } from 'lucide-react';
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
import { PageHeader, Card, CardHeader, ProgressBar } from '@/components/ui/card';
import { Button, Spinner } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, Input, FormField } from '@/components/ui/form';
import { useToast } from '@/components/ui/toast';
import { runScenario } from '@/api/services';
import { BARANGAYS } from '@/api/mock';
import type { ScenarioReport } from '@/api/types';
import { formatDateTime, formatNumber } from '@/lib/labels';

const ESTIMATES = [10, 25, 50, 100, 200];

export function SimulatorPage() {
  const { success, error } = useToast();
  const [barangay, setBarangay] = useState<string>(BARANGAYS[0]);
  const [affected, setAffected] = useState(50);
  const [running, setRunning] = useState(false);
  const [report, setReport] = useState<ScenarioReport | null>(null);

  async function handleRun() {
    if (!barangay || affected < 1) {
      error('Pick a barangay and enter a positive household estimate.');
      return;
    }
    setRunning(true);
    try {
      const res = await runScenario({ barangay, affected_households: affected });
      setReport(res);
      success('Scenario computed — review projected loads and resource needs');
    } catch (err) {
      error(err instanceof Error ? err.message : 'Scenario failed to run');
    } finally {
      setRunning(false);
    }
  }

  const chartData =
    report?.resource_needs.map((r) => ({
      name: r.name.split(' ')[0],
      current: r.current,
      required: r.required,
    })) ?? [];

  return (
    <div>
      <PageHeader
        title="Scenario Simulator"
        description="What-if analysis: project evacuation center loads and resource shortfalls before an event hits."
        icon={<FlaskConical className="h-5 w-5" />}
      />

      <Card className="mb-6 p-5">
        <div className="grid grid-cols-1 items-end gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <FormField label="Affected barangay" required>
            <Select value={barangay} onChange={(e) => setBarangay(e.target.value)}>
              {BARANGAYS.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Estimated affected households" required hint="e.g. based on flood depth zones">
            <Input type="number" min={1} value={affected} onChange={(e) => setAffected(Number(e.target.value))} />
          </FormField>
          <div className="flex items-start gap-1.5 xl:pt-6">
            {ESTIMATES.map((e) => (
              <button
                key={e}
                onClick={() => setAffected(e)}
                className={`rounded-md border px-2 py-1 text-xs font-medium transition-colors ${
                  affected === e ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                {e}
              </button>
            ))}
          </div>
          <div className="flex gap-2 xl:justify-end">
            <Button variant="secondary" onClick={() => setReport(null)} disabled={!report}>
              <RefreshCw className="h-4 w-4" />
              Reset
            </Button>
            <Button onClick={() => void handleRun()} loading={running}>
              {!running && <Play className="h-4 w-4" />}
              Run scenario
            </Button>
          </div>
        </div>
      </Card>

      {running && !report && (
        <Card className="flex flex-col items-center justify-center py-16">
          <Spinner className="h-8 w-8 text-brand-600" />
          <p className="mt-3 text-sm text-slate-600">
            Simulating “{barangay} affected ({affected} households)”…
          </p>
        </Card>
      )}

      {report && (
        <>
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Card className="p-4">
              <p className="text-xs font-medium uppercase text-slate-500">Scenario</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">{report.scenario.title}</p>
              <p className="text-xs text-slate-500">{formatDateTime(report.allocation.generated_at)}</p>
            </Card>
            <Card className="p-4">
              <p className="flex items-center gap-1.5 text-xs font-medium uppercase text-slate-500">
                <Users className="h-3.5 w-3.5" /> Evacuees
              </p>
              <p className="mt-1 text-2xl font-bold text-slate-900">
                {formatNumber(
                  report.scenario.estimated_evacuees ?? report.scenario.affected_households * 4,
                )}
              </p>
              <p className="text-xs text-slate-500">approx. 4 pax / household</p>
            </Card>
            <Card className="p-4">
              <p className="flex items-center gap-1.5 text-xs font-medium uppercase text-slate-500">
                <Building2 className="h-3.5 w-3.5" /> Centers loaded
              </p>
              <p className="mt-1 text-2xl font-bold text-slate-900">{report.allocation.center_loads.length}</p>
              <p className="text-xs text-slate-500">
                {report.allocation.center_loads.filter((c) => c.load_percent >= 90).length} at or over 90%
              </p>
            </Card>
            <Card className="p-4">
              <p className="flex items-center gap-1.5 text-xs font-medium uppercase text-slate-500">
                <Package className="h-3.5 w-3.5" /> Resource gaps
              </p>
              <p className="mt-1 text-2xl font-bold text-danger-600">
                {report.resource_needs.filter((r) => r.deficit > 0).length}
              </p>
              <p className="text-xs text-slate-500">categories with shortfall</p>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <Card className="xl:col-span-2">
              <CardHeader
                title="Projected center loads"
                subtitle="Occupancy if affected households evacuate now"
              />
              <div className="grid grid-cols-1 gap-4 px-5 py-4 sm:grid-cols-2">
                {report.allocation.center_loads.map((c) => {
                  return (
                    <div key={c.center_id} className="rounded-lg border border-slate-200 p-4">
                      <div className="mb-1 flex items-center justify-between">
                        <p className="truncate pr-2 text-sm font-semibold text-slate-900">{c.center_name}</p>
                        <Badge tone={c.load_percent >= 90 ? 'red' : c.load_percent >= 70 ? 'amber' : 'green'}>
                          {c.load_percent}%
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500">
                        {c.occupants} / {c.capacity} occupants
                      </p>
                      <div className="mt-2">
                        <ProgressBar
                          value={c.load_percent}
                          tone={c.load_percent >= 90 ? 'red' : c.load_percent >= 70 ? 'amber' : 'green'}
                        />
                      </div>
                      {c.load_percent >= 90 && (
                        <p className="mt-1.5 inline-flex items-center gap-1 text-[11px] font-medium text-danger-600">
                          <AlertTriangle className="h-3 w-3" /> Over capacity — redirect evacuees
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>

            <Card>
              <CardHeader title="Resource shortfall" subtitle="Current stock vs. projected need" />
              <div className="space-y-3 px-5 py-4">
                {report.resource_needs.map((r) => (
                  <div key={r.resource_id} className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-800">{r.name}</p>
                      <p className="text-xs text-slate-500">
                        {formatNumber(r.current)} {r.unit} on hand
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      {r.deficit > 0 ? (
                        <Badge tone={r.deficit > r.required * 0.5 ? 'red' : 'amber'}>
                          short {formatNumber(r.deficit)}
                        </Badge>
                      ) : (
                        <Badge tone="green">ok</Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          <Card className="mt-6">
            <CardHeader
              title="Resource need (current vs. required)"
              subtitle="Suggested procurement targets for the projected evacuee count"
            />
            <div className="h-72 px-4 py-3">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: '#f1f5f9' }} />
                  <Legend />
                  <Bar dataKey="current" name="Current stock" fill="#1d6cf5" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="required" name="Required" fill="#e11d3f" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </>
      )}

      {!running && !report && (
        <Card className="flex flex-col items-center justify-center py-16 text-center">
          <FlaskConical className="mb-3 h-10 w-10 text-slate-300" />
          <h3 className="text-sm font-semibold text-slate-900">No scenario run yet</h3>
          <p className="mt-1 max-w-sm text-sm text-slate-500">
            Simulate “What if <b>{barangay}</b> is hit and <b>{affected} households</b> evacuate?” by pressing{' '}
            <b>Run scenario</b>.
          </p>
        </Card>
      )}
    </div>
  );
}