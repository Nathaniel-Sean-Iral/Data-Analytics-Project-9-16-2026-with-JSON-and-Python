import { useMemo, useState } from 'react';
import { Package, Plus, Minus, AlertTriangle, Save, PackageCheck, Wallet } from 'lucide-react';
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
import { PageHeader, Card, CardHeader } from '@/components/ui/card';
import { Button, Spinner } from '@/components/ui/button';
import { DataTable, type Column } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Modal } from '@/components/ui/modal';
import { Input, Select, FormField } from '@/components/ui/form';
import { useToast } from '@/components/ui/toast';
import { usePermissions } from '@/lib/permissions';
import { useAsync } from '@/lib/useAsync';
import {
  fetchResources,
  fetchResourceSummaries,
  adjustStock,
  createResource,
  updateResourceThreshold,
} from '@/api/services';
import { RESOURCE_TYPE_LABELS } from '@/lib/labels';
import { formatNumber, formatDateTime } from '@/lib/labels';
import type { Resource, ResourceType } from '@/api/types';

const ADJUST_REASONS = [
  'New delivery',
  'Distribution to evacuations',
  'Stock count correction',
  'Expired / damaged disposal',
  'Transfer to another warehouse',
];

const RESOURCE_TYPES = Object.keys(RESOURCE_TYPE_LABELS) as ResourceType[];

interface ResourceForm {
  name: string;
  type: ResourceType;
  unit: string;
  quantity_on_hand: number;
  threshold: number;
  stored_in: string;
  expiry: string;
}

const EMPTY_RESOURCE: ResourceForm = {
  name: '',
  type: 'rice',
  unit: 'sacks',
  quantity_on_hand: 0,
  threshold: 0,
  stored_in: '',
  expiry: '',
};

export function ResourcesPage() {
  const { data, loading, refetch } = useAsync(() => fetchResources());
  const summaries = useAsync(() => fetchResourceSummaries());
  const { success, error } = useToast();
  const { can, isViewer } = usePermissions();
  const canEdit = can('resource:update');

  const [adjusting, setAdjusting] = useState<Resource | null>(null);
  const [delta, setDelta] = useState(0);
  const [reason, setReason] = useState(ADJUST_REASONS[1]);
  const [saving, setSaving] = useState(false);
  const [thresholdEditing, setThresholdEditing] = useState<Resource | null>(null);
  const [thresholdValue, setThresholdValue] = useState(0);
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState<ResourceForm>(EMPTY_RESOURCE);

  const lowStock = useMemo(() => (data ?? []).filter((r) => r.quantity_on_hand < r.threshold), [data]);
  const chartData = useMemo(
    () =>
      (summaries.data ?? []).map((r) => ({
        name: r.label,
        available: r.total_on_hand,
        required: r.total_required,
      })),
    [summaries.data],
  );

  async function handleAdjust() {
    if (!adjusting || delta === 0) return;
    setSaving(true);
    try {
      await adjustStock({ resource_id: adjusting.id, delta, reason });
      success(delta > 0 ? 'Stock increased' : 'Stock decreased');
      setAdjusting(null);
      void refetch();
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to adjust stock');
    } finally {
      setSaving(false);
    }
  }

  function openCreate() {
    setForm(EMPTY_RESOURCE);
    setCreateOpen(true);
  }

  async function handleCreate() {
    if (!form.name.trim() || !form.unit.trim()) return;
    setSaving(true);
    try {
      await createResource({
        name: form.name.trim(),
        type: form.type,
        unit: form.unit.trim(),
        quantity_on_hand: Math.max(0, form.quantity_on_hand),
        threshold: Math.max(0, form.threshold),
        stored_in: form.stored_in.trim() || undefined,
        expiry: form.expiry || undefined,
      });
      success(`${form.name.trim()} added to tracked stock`);
      setCreateOpen(false);
      void refetch();
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to add resource');
    } finally {
      setSaving(false);
    }
  }

  async function handleThreshold() {
    if (!thresholdEditing || thresholdValue < 0) return;
    setSaving(true);
    try {
      await updateResourceThreshold(thresholdEditing.id, thresholdValue);
      success('Threshold updated');
      setThresholdEditing(null);
      void refetch();
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to update threshold');
    } finally {
      setSaving(false);
    }
  }

  const columns: Column<Resource>[] = [
    {
      key: 'name',
      header: 'Resource',
      render: (r) => (
        <div>
          <p className="font-medium text-slate-900">{r.name}</p>
          <Badge tone="blue" className="mt-0.5">{RESOURCE_TYPE_LABELS[r.type]}</Badge>
        </div>
      ),
    },
    {
      key: 'qty',
      header: 'On hand',
      sortValue: (r) => r.quantity_on_hand,
      render: (r) => (
        <span className={`font-semibold ${r.quantity_on_hand < r.threshold ? 'text-danger-600' : 'text-slate-900'}`}>
          {formatNumber(r.quantity_on_hand)} <span className="text-xs font-normal text-slate-400">{r.unit}</span>
        </span>
      ),
    },
    {
      key: 'threshold',
      header: 'Threshold',
      sortValue: (r) => r.threshold,
      render: (r) => (
        <span className="inline-flex items-center gap-1.5 text-slate-600">
          {formatNumber(r.threshold)}
          {canEdit && (
            <button
              onClick={() => {
                setThresholdEditing(r);
                setThresholdValue(r.threshold);
              }}
              className="rounded px-1 text-xs text-brand-600 hover:bg-brand-50"
            >
              edit
            </button>
          )}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (r) =>
        r.quantity_on_hand < r.threshold ? (
          <Badge tone="red" dot>
            Low stock
          </Badge>
        ) : r.quantity_on_hand < r.threshold * 1.5 ? (
          <Badge tone="amber" dot>
            Getting low
          </Badge>
        ) : (
          <Badge tone="green" dot>
            Adequate
          </Badge>
        ),
    },
    {
      key: 'expiry',
      header: 'Expiry',
      render: (r) => (r.expiry ? <span className="text-slate-600">{formatDateTime(r.expiry)}</span> : <span className="text-slate-400">—</span>),
    },
    {
      key: 'actions',
      header: '',
      className: 'text-right',
      render: (r) =>
        canEdit ? (
          <Button variant="secondary" className="!px-2.5 !py-1 !text-xs" onClick={() => setAdjusting(r)}>
            Adjust
          </Button>
        ) : (
          <span className="text-xs text-slate-400">—</span>
        ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Resources"
        description="Stock management for relief supplies. Low-stock items are highlighted for replenishment."
        icon={<Package className="h-5 w-5" />}
        actions={
          isViewer ? (
            <Badge tone="slate">View only</Badge>
          ) : canEdit ? (
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4" />
              Add item
            </Button>
          ) : undefined
        }
      />

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="flex items-center justify-between p-4">
          <div>
            <p className="text-xs font-medium uppercase text-slate-500">Tracked items</p>
            <p className="text-xl font-bold text-slate-900">{data?.length ?? 0}</p>
          </div>
          <PackageCheck className="h-5 w-5 text-brand-500" />
        </Card>
        <Card className="flex items-center justify-between p-4">
          <div>
            <p className="text-xs font-medium uppercase text-slate-500">Low stock items</p>
            <p className="text-xl font-bold text-danger-600">{lowStock.length}</p>
          </div>
          <AlertTriangle className="h-5 w-5 text-danger-500" />
        </Card>
        <Card className="flex items-center justify-between p-4">
          <div>
            <p className="text-xs font-medium uppercase text-slate-500">Value (sample)</p>
            <p className="text-xl font-bold text-slate-900">
              ₱{formatNumber((data ?? []).reduce((s, r) => s + r.quantity_on_hand * (r.type === 'water' ? 60 : r.type === 'rice' ? 1200 : 25), 0))}
            </p>
          </div>
          <Wallet className="h-5 w-5 text-emerald-500" />
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader title="Resource availability by type" subtitle="Available stock vs. configured requirements" />
          <div className="h-80 px-4 py-3">
            {summaries.loading ? (
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

        <Card>
          <CardHeader title="Low stock alerts" subtitle="Items at or below threshold" />
          <div className="divide-y divide-slate-100">
            {lowStock.length === 0 && <p className="px-5 py-8 text-center text-sm text-slate-500">No low-stock items.</p>}
            {lowStock.map((r) => (
              <div key={r.id} className="flex items-center justify-between px-5 py-3">
                <div>
                  <p className="text-sm font-medium text-slate-900">{r.name}</p>
                  <p className="text-xs text-danger-600">
                    {r.quantity_on_hand} {r.unit} on hand · threshold {r.threshold}
                  </p>
                </div>
                <AlertTriangle className="h-4 w-4 shrink-0 text-danger-500" />
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="mt-6">
        <DataTable
          columns={columns}
          rows={data ?? []}
          keyFor={(r) => r.id}
          loading={loading}
          sortable
          emptyTitle="No resources tracked yet"
          emptyDescription="Add stock items so the system can compute availability vs. requirements."
        />
      </div>

      <Modal
        open={Boolean(adjusting)}
        onClose={() => setAdjusting(null)}
        title={`Adjust stock — ${adjusting?.name ?? ''}`}
        description="Positive to add stock, negative to issue or remove."
        footer={
          <>
            <Button variant="secondary" onClick={() => setAdjusting(null)}>
              Cancel
            </Button>
            <Button onClick={handleAdjust} loading={saving} disabled={delta === 0}>
              Apply adjustment
            </Button>
          </>
        }
      >
        {adjusting && (
          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3">
              <span className="text-sm text-slate-600">Current on hand</span>
              <span className="text-lg font-bold text-slate-900">
                {formatNumber(adjusting.quantity_on_hand)} {adjusting.unit}
              </span>
            </div>
            <FormField label="Amount to add (+) or remove (−)" required hint={`Result: ${Math.max(0, adjusting.quantity_on_hand + delta)} ${adjusting.unit}`}>
              <Input
                type="number"
                value={delta}
                onChange={(e) => setDelta(Number(e.target.value))}
                placeholder="0"
              />
            </FormField>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                className="flex-1"
                onClick={() => setDelta((d) => d - 10)}
              >
                <Minus className="h-4 w-4" /> −10
              </Button>
              <Button variant="secondary" className="flex-1" onClick={() => setDelta((d) => d + 10)}>
                <Plus className="h-4 w-4" /> +10
              </Button>
            </div>
            <FormField label="Reason">
              <Select value={reason} onChange={(e) => setReason(e.target.value)}>
                {ADJUST_REASONS.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </Select>
            </FormField>
          </div>
        )}
      </Modal>

      <Modal
        open={Boolean(thresholdEditing)}
        onClose={() => setThresholdEditing(null)}
        title={`Set reorder threshold — ${thresholdEditing?.name ?? ''}`}
        description="When on-hand stock falls below this value, the item is flagged low."
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setThresholdEditing(null)}>
              Cancel
            </Button>
            <Button onClick={handleThreshold} loading={saving}>
              <Save className="h-4 w-4" />
              Save threshold
            </Button>
          </>
        }
      >
        <FormField label="Threshold" required hint={`Minimum stock before reordering (${thresholdEditing?.unit})`}>
          <Input
            type="number"
            min={0}
            value={thresholdValue}
            onChange={(e) => setThresholdValue(Number(e.target.value))}
          />
        </FormField>
      </Modal>

      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="Add tracked item"
        description="Register a supply so availability is measured against requirements."
        footer={
          <>
            <Button variant="secondary" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              loading={saving}
              disabled={!form.name.trim() || !form.unit.trim()}
            >
              <Save className="h-4 w-4" />
              Add item
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <FormField label="Item name" required>
            <Input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. 50kg Rice Sack"
            />
          </FormField>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField label="Category" required>
              <Select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value as ResourceType })}
              >
                {RESOURCE_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {RESOURCE_TYPE_LABELS[t]}
                  </option>
                ))}
              </Select>
            </FormField>
            <FormField label="Unit" required hint="e.g. sacks, boxes, liters">
              <Input
                value={form.unit}
                onChange={(e) => setForm({ ...form, unit: e.target.value })}
                placeholder="sacks"
              />
            </FormField>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField label="Quantity on hand" hint="Starting stock for this item">
              <Input
                type="number"
                min={0}
                value={form.quantity_on_hand}
                onChange={(e) => setForm({ ...form, quantity_on_hand: Number(e.target.value) })}
              />
            </FormField>
            <FormField label="Reorder threshold" hint="Flagged low below this level">
              <Input
                type="number"
                min={0}
                value={form.threshold}
                onChange={(e) => setForm({ ...form, threshold: Number(e.target.value) })}
              />
            </FormField>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField label="Stored in" hint="Warehouse or location">
              <Input
                value={form.stored_in}
                onChange={(e) => setForm({ ...form, stored_in: e.target.value })}
                placeholder="Optional"
              />
            </FormField>
            <FormField label="Expiry" hint="Leave blank if not perishable">
              <Input
                type="date"
                value={form.expiry}
                onChange={(e) => setForm({ ...form, expiry: e.target.value })}
              />
            </FormField>
          </div>
        </div>
      </Modal>
    </div>
  );
}