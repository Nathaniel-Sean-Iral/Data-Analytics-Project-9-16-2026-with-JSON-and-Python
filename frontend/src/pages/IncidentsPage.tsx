import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Siren, Plus, MapPin, ChevronRight } from 'lucide-react';
import { PageHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DataTable, type Column } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Modal } from '@/components/ui/modal';
import { Input, Select, Textarea, FormField } from '@/components/ui/form';
import { useToast } from '@/components/ui/toast';
import { usePermissions } from '@/lib/permissions';
import { useAsync } from '@/lib/useAsync';
import { fetchIncidents, createIncident, updateIncidentStatus } from '@/api/services';
import { BARANGAYS } from '@/api/mock';
import {
  formatDateTime,
  formatNumber,
  INCIDENT_TYPE_LABELS,
  INCIDENT_TYPE_TONES,
  SEVERITY_TONES,
  STATUS_LABELS,
  STATUS_TONES,
} from '@/lib/labels';
import type { Incident, IncidentSeverity, IncidentStatus, IncidentType } from '@/api/types';

interface NewIncidentForm {
  title: string;
  type: IncidentType;
  barangay: string;
  severity: IncidentSeverity;
  description: string;
  affected_households: number;
  lat: string;
  lng: string;
}

const EMPTY_INCIDENT: NewIncidentForm = {
  title: '',
  type: 'flood',
  barangay: BARANGAYS[0],
  severity: 'moderate',
  description: '',
  affected_households: 0,
  lat: '',
  lng: '',
};

export function IncidentsPage() {
  const { data, loading, refetch } = useAsync(() => fetchIncidents());
  const { success, error } = useToast();
  const { can, isViewer } = usePermissions();
  const canCreate = can('incident:create');

  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<NewIncidentForm>(EMPTY_INCIDENT);
  const [saving, setSaving] = useState(false);
  const [statusTarget, setStatusTarget] = useState<Incident | null>(null);

  const set = <K extends keyof NewIncidentForm>(key: K, value: NewIncidentForm[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  async function handleCreate() {
    if (!form.title.trim()) {
      error('Title is required.');
      return;
    }
    setSaving(true);
    try {
      await createIncident({
        title: form.title,
        type: form.type,
        barangay: form.barangay,
        severity: form.severity,
        description: form.description,
        affected_households: form.affected_households,
        lat: form.lat ? Number(form.lat) : undefined,
        lng: form.lng ? Number(form.lng) : undefined,
      });
      success('Incident reported');
      setModalOpen(false);
      setForm(EMPTY_INCIDENT);
      void refetch();
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to report incident');
    } finally {
      setSaving(false);
    }
  }

  async function handleStatus(status: IncidentStatus) {
    if (!statusTarget) return;
    try {
      await updateIncidentStatus(statusTarget.id, status);
      success(`Incident marked as ${STATUS_LABELS[status].toLowerCase()}`);
      setStatusTarget(null);
      void refetch();
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to update status');
    }
  }

  const columns: Column<Incident>[] = [
    {
      key: 'title',
      header: 'Incident',
      render: (r) => (
        <div>
          <Link to={`/incidents/${r.id}`} className="font-medium text-slate-900 hover:text-brand-600">
            {r.title}
          </Link>
          <p className="mt-0.5 inline-flex items-center gap-1 text-xs text-slate-500">
            <MapPin className="h-3 w-3" />
            {r.barangay} · {formatDateTime(r.reported_at)}
          </p>
        </div>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      render: (r) => <Badge tone={INCIDENT_TYPE_TONES[r.type]}>{INCIDENT_TYPE_LABELS[r.type]}</Badge>,
    },
    {
      key: 'severity',
      header: 'Severity',
      sortValue: (r) => ({ low: 1, moderate: 2, high: 3, critical: 4 })[r.severity],
      render: (r) => <Badge tone={SEVERITY_TONES[r.severity]} dot>{r.severity}</Badge>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (r) => <Badge tone={STATUS_TONES[r.status]} dot>{STATUS_LABELS[r.status]}</Badge>,
    },
    {
      key: 'affected',
      header: 'Affected HHs',
      sortValue: (r) => r.affected_households ?? 0,
      render: (r) => <span className="text-slate-700">{r.affected_households ? formatNumber(r.affected_households) : '—'}</span>,
    },
    {
      key: 'actions',
      header: '',
      className: 'text-right',
      render: (r) => (
        <div className="flex items-center justify-end gap-2">
          {canCreate && r.status !== 'resolved' && (
            <Button
              variant="secondary"
              className="!px-2.5 !py-1 !text-xs"
              onClick={() => setStatusTarget(r)}
            >
              Update
            </Button>
          )}
          <Link to={`/incidents/${r.id}`} className="inline-flex items-center gap-0.5 text-xs font-medium text-brand-600 hover:text-brand-700">
            Detail <ChevronRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Incidents"
        description="Reported hazards and emergencies across the municipality."
        icon={<Siren className="h-5 w-5" />}
        actions={
          isViewer ? (
            <Badge tone="slate">View only</Badge>
          ) : canCreate ? (
            <>
              <Button
                variant="secondary"
                onClick={() => {
                  setForm(EMPTY_INCIDENT);
                  setModalOpen(true);
                }}
              >
                <Plus className="h-4 w-4" />
                Report incident
              </Button>
            </>
          ) : undefined
        }
      />

      <DataTable
        columns={columns}
        rows={data ?? []}
        keyFor={(r) => r.id}
        loading={loading}
        sortable
        emptyTitle="No incidents reported"
        emptyDescription="Reported incidents will appear here."
      />

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Report incident"
        description="Provide as much detail as possible to help responders."
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} loading={saving}>
              Report incident
            </Button>
          </>
        }
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <FormField label="Title" required>
              <Input value={form.title} onChange={(e) => set('title', e.target.value)} placeholder="e.g. Flash flood along riverbank" />
            </FormField>
          </div>
          <FormField label="Type" required>
            <Select value={form.type} onChange={(e) => set('type', e.target.value as IncidentType)}>
              {(Object.keys(INCIDENT_TYPE_LABELS) as IncidentType[]).map((t) => (
                <option key={t} value={t}>
                  {INCIDENT_TYPE_LABELS[t]}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Barangay" required>
            <Select value={form.barangay} onChange={(e) => set('barangay', e.target.value)}>
              {BARANGAYS.map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Severity" required>
            <Select value={form.severity} onChange={(e) => set('severity', e.target.value as IncidentSeverity)}>
              <option value="low">Low</option>
              <option value="moderate">Moderate</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </Select>
          </FormField>
          <FormField label="Affected households">
            <Input type="number" min={0} value={form.affected_households} onChange={(e) => set('affected_households', Number(e.target.value))} />
          </FormField>
          <FormField label="Latitude">
            <Input value={form.lat} onChange={(e) => set('lat', e.target.value)} placeholder="14.9571" />
          </FormField>
          <FormField label="Longitude">
            <Input value={form.lng} onChange={(e) => set('lng', e.target.value)} placeholder="120.9629" />
          </FormField>
          <div className="sm:col-span-2">
            <FormField label="Description">
              <Textarea
                rows={3}
                value={form.description}
                onChange={(e) => set('description', e.target.value)}
                placeholder="Situation, conditions, initial response…"
              />
            </FormField>
          </div>
        </div>
      </Modal>

      {/* Status update */}
      <Modal
        open={Boolean(statusTarget)}
        onClose={() => setStatusTarget(null)}
        title={`Update status — ${statusTarget?.title ?? ''}`}
        description="Move the incident through the response workflow."
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setStatusTarget(null)}>
              Cancel
            </Button>
          </>
        }
      >
        {statusTarget && (
          <div className="space-y-1.5">
            <p className="mb-2 text-xs text-slate-500">
              Current: <Badge tone={STATUS_TONES[statusTarget.status]} dot>{STATUS_LABELS[statusTarget.status]}</Badge>
            </p>
            {(['reported', 'assessing', 'responding', 'resolved'] as IncidentStatus[])
              .filter((s) => s !== statusTarget.status)
              .map((s) => (
                <button
                  key={s}
                  onClick={() => void handleStatus(s)}
                  className="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:border-brand-400 hover:bg-brand-50 hover:text-brand-700"
                >
                  {STATUS_LABELS[s]}
                  <ChevronRight className="h-4 w-4 text-slate-400" />
                </button>
              ))}
          </div>
        )}
      </Modal>
    </div>
  );
}