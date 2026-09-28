import { useState } from 'react';
import { ArrowRightLeft, Play, Download, AlertTriangle, PackageOpen, Loader2 } from 'lucide-react';
import { PageHeader, Card, CardHeader, ProgressBar } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DataTable, type Column } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Select, FormField } from '@/components/ui/form';
import { useToast } from '@/components/ui/toast';
import { runAllocation } from '@/api/services';
import { BARANGAYS } from '@/api/mock';
import type { AllocationResult, EvacuationAssignment } from '@/api/types';
import { formatDateTime } from '@/lib/labels';

function loadTone(percent: number): 'green' | 'amber' | 'red' {
  return percent >= 90 ? 'red' : percent >= 70 ? 'amber' : 'green';
}

export function AllocationPage() {
  const { success, error } = useToast();
  const [barangay, setBarangay] = useState('ALL');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<AllocationResult | null>(null);

  async function handleRun() {
    setRunning(true);
    try {
      const res = await runAllocation(barangay === 'ALL' ? undefined : barangay);
      setResult(res);
      success('Allocation complete — review the plan below');
    } catch (err) {
      error(err instanceof Error ? err.message : 'Allocation failed');
    } finally {
      setRunning(false);
    }
  }

  function handleDownload() {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.request_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
    success('Allocation plan exported');
  }

  const columns: Column<EvacuationAssignment>[] = [
    { key: 'household_no', header: 'Household', render: (r) => <span className="font-medium text-slate-900">{r.household_no}</span> },
    { key: 'head', header: 'Head', render: (r) => <span className="text-slate-700">{r.household_head}</span> },
    { key: 'barangay', header: 'Barangay', render: (r) => <Badge tone="slate">{r.barangay}</Badge> },
    { key: 'center', header: 'Assigned center', render: (r) => <span className="text-slate-700">{r.center_name}</span> },
    { key: 'load', header: 'Center load', render: (r) => <span className="text-slate-700">{r.center_load_percent}%</span> },
  ];

  const hasOverflow = (result?.overflow_households ?? 0) > 0;

  return (
    <div>
      <PageHeader
        title="Evacuation Allocation"
        description="Assign affected households to the nearest evacuation center with available capacity."
        icon={<ArrowRightLeft className="h-5 w-5" />}
      />

      <Card className="mb-6 p-5">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="w-full max-w-xs">
            <FormField label="Filter by barangay" hint="All barangays uses the full household registry.">
              <Select value={barangay} onChange={(e) => setBarangay(e.target.value)}>
                <option value="ALL">All barangays</option>
                {BARANGAYS.map((b) => (
                  <option key={b} value={b}>
                    {b}
                  </option>
                ))}
              </Select>
            </FormField>
          </div>
          <div className="flex gap-2">
            {result && (
              <Button variant="secondary" onClick={handleDownload}>
                <Download className="h-4 w-4" />
                Export plan
              </Button>
            )}
            <Button onClick={() => void handleRun()} loading={running}>
              {!running && <Play className="h-4 w-4" />}
              Run allocation
            </Button>
          </div>
        </div>
      </Card>

      {running && !result && (
        <Card className="flex flex-col items-center justify-center py-16">
          <Loader2 className="mb-3 h-8 w-8 animate-spin text-brand-600" />
          <p className="text-sm text-slate-600">Computing nearest-center assignments…</p>
        </Card>
      )}

      {result && (
        <>
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Card className="p-4">
              <p className="text-xs font-medium uppercase text-slate-500">Total households</p>
              <p className="mt-1 text-2xl font-bold text-slate-900">{result.total_households}</p>
            </Card>
            <Card className="p-4">
              <p className="text-xs font-medium uppercase text-slate-500">Assigned</p>
              <p className="mt-1 text-2xl font-bold text-emerald-600">{result.assigned_households}</p>
            </Card>
            <Card className="p-4">
              <p className="text-xs font-medium uppercase text-slate-500">Overflow</p>
              <p className={`mt-1 text-2xl font-bold ${hasOverflow ? 'text-danger-600' : 'text-slate-900'}`}>{result.overflow_households}</p>
            </Card>
            <Card className="p-4">
              <p className="text-xs font-medium uppercase text-slate-500">Generated</p>
              <p className="mt-1 text-sm font-semibold text-slate-700">{formatDateTime(result.generated_at)}</p>
            </Card>
          </div>

          {result.coverage_gaps.length > 0 && (
            <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-amber-800">
                <AlertTriangle className="h-4 w-4" />
                Coverage gaps
              </p>
              <ul className="list-inside list-disc space-y-1 text-sm text-amber-700">
                {result.coverage_gaps.map((g, i) => (
                  <li key={i}>{g}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="mb-6">
            <Card>
              <CardHeader title="Center loads after assignment" subtitle="Capacity utilization per evacuation center" />
              <div className="grid grid-cols-1 gap-4 px-5 py-4 sm:grid-cols-2 xl:grid-cols-3">
                {result.center_loads.map((c) => (
                  <div key={c.center_id} className="rounded-lg border border-slate-200 p-4">
                    <div className="mb-1 flex items-center justify-between">
                      <p className="text-sm font-semibold text-slate-900">{c.center_name}</p>
                      <Badge tone={c.load_percent >= 90 ? 'red' : c.load_percent >= 70 ? 'amber' : 'green'}>
                        {c.load_percent}%
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-500">
                      {c.occupants} / {c.capacity} occupants · {c.barangay}
                    </p>
                    <div className="mt-2">
                      <ProgressBar value={c.load_percent} tone={loadTone(c.load_percent)} />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          <DataTable
            columns={columns}
            rows={result.assignments}
            keyFor={(r) => r.id ?? r.household_no}
            sortable
            emptyTitle="No assignments generated"
          />

          {result.overflow.length > 0 && (
            <Card className="mt-6">
              <CardHeader
                title="Overflow list"
                subtitle="Households that could not be assigned to any center"
                action={<PackageOpen className="h-4 w-4 text-danger-500" />}
              />
              <div className="divide-y divide-slate-100">
                {result.overflow.map((o) => (
                  <div key={o.household_id} className="flex items-center justify-between px-5 py-3">
                    <div>
                      <p className="text-sm font-medium text-slate-900">
                        {o.household_no} — {o.head_name}
                      </p>
                      <p className="text-xs text-slate-500">{o.barangay}</p>
                    </div>
                    <p className="text-xs text-danger-600">{o.reason}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}

      {!running && !result && (
        <Card className="flex flex-col items-center justify-center py-16 text-center">
          <ArrowRightLeft className="mb-3 h-10 w-10 text-slate-300" />
          <h3 className="text-sm font-semibold text-slate-900">Ready to allocate</h3>
          <p className="mt-1 max-w-sm text-sm text-slate-500">
            Pick a barangay (or run for the whole municipality) and press <b>Run allocation</b> to generate an
            evacuation plan with per-center loads and coverage gaps.
          </p>
        </Card>
      )}
    </div>
  );
}