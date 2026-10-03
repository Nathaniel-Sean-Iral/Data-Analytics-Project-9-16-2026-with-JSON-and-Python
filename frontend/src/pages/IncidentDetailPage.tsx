import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Siren,
  MapPin,
  Clock,
  User as UserIcon,
  Users,
  Building2,
  CheckCircle2,
  ClipboardList,
  Search,
  RadioTower,
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button, Spinner } from '@/components/ui/button';
import { useToast } from '@/components/ui/toast';
import { usePermissions } from '@/lib/permissions';
import { useAsync } from '@/lib/useAsync';
import { fetchIncident, updateIncidentStatus, fetchHouseholds, fetchCenters } from '@/api/services';
import {
  formatDateTime,
  formatNumber,
  INCIDENT_TYPE_LABELS,
  INCIDENT_TYPE_TONES,
  SEVERITY_TONES,
  STATUS_LABELS,
  STATUS_TONES,
} from '@/lib/labels';
import type { IncidentStatus } from '@/api/types';

const WORKFLOW: IncidentStatus[] = ['reported', 'assessing', 'responding', 'resolved'];

export function IncidentDetailPage() {
  const { id } = useParams();
  const { can, isViewer } = usePermissions();
  const { success, error } = useToast();
  const incident = useAsync(() => fetchIncident(Number(id)));
  const households = useAsync(() => fetchHouseholds());
  const centers = useAsync(() => fetchCenters());
  const [updating, setUpdating] = useState(false);

  const canUpdate = can('incident:update');

  const barangayHouseholds = useMemo(() => {
    if (!incident.data || !households.data) return 0;
    return households.data.items.filter((h) => h.barangay === incident.data?.barangay).length;
  }, [incident.data, households.data]);

  const barangayCenters = useMemo(() => {
    if (!incident.data || !centers.data) return 0;
    return centers.data.filter((c) => c.barangay === incident.data?.barangay).length;
  }, [incident.data, centers.data]);

  async function advance() {
    if (!incident.data) return;
    const currentIdx = WORKFLOW.indexOf(incident.data.status);
    if (currentIdx >= WORKFLOW.length - 1) return;
    const next = WORKFLOW[currentIdx + 1];
    setUpdating(true);
    try {
      await updateIncidentStatus(incident.data.id, next);
      success(`Incident moved to "${STATUS_LABELS[next]}"`);
      void incident.refetch();
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to update status');
    } finally {
      setUpdating(false);
    }
  }

  if (incident.loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner className="h-8 w-8 text-brand-600" />
      </div>
    );
  }

  if (!incident.data) {
    return (
      <div className="flex h-64 flex-col items-center justify-center text-center">
        <Siren className="h-8 w-8 text-slate-300" />
        <p className="mt-3 text-sm text-slate-500">Incident not found.</p>
        <Link to="/incidents" className="btn-secondary mt-4 !text-sm">
          Back to incidents
        </Link>
      </div>
    );
  }

  const inc = incident.data;
  const currentIdx = WORKFLOW.indexOf(inc.status);

  return (
    <div>
      <Link to="/incidents" className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" />
        Back to incidents
      </Link>

      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="rounded-lg bg-danger-50 p-2.5 text-danger-600">
            <Siren className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">{inc.title}</h1>
            <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
              <Badge tone={INCIDENT_TYPE_TONES[inc.type]}>{INCIDENT_TYPE_LABELS[inc.type]}</Badge>
              <Badge tone={SEVERITY_TONES[inc.severity]} dot>{inc.severity}</Badge>
              <Badge tone={STATUS_TONES[inc.status]} dot>{STATUS_LABELS[inc.status]}</Badge>
              {isViewer && <Badge tone="slate">View only</Badge>}
            </div>
          </div>
        </div>
        {canUpdate && (
          <div className="flex gap-2">
            {inc.status !== 'resolved' && (
              <Button onClick={() => void advance()} loading={updating}>
                <CheckCircle2 className="h-4 w-4" />
                Mark as {WORKFLOW[Math.min(currentIdx + 1, WORKFLOW.length - 1)]}
              </Button>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card className="p-5">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900">
              <ClipboardList className="h-4 w-4 text-brand-600" />
              Description
            </h3>
            <p className="text-sm leading-relaxed text-slate-700">
              {inc.description || 'No description provided yet. Add field observations when available.'}
            </p>
          </Card>

          <Card className="p-5">
            <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-900">
              <RadioTower className="h-4 w-4 text-brand-600" />
              Response workflow
            </h3>
            <div className="flex items-center">
              {WORKFLOW.map((step, idx) => (
                <div key={step} className="flex flex-1 items-center last:flex-none">
                  <div className="flex flex-col items-center">
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${
                        idx < currentIdx
                          ? 'bg-emerald-500 text-white'
                          : idx === currentIdx
                            ? 'bg-brand-600 text-white ring-4 ring-brand-100'
                            : 'bg-slate-200 text-slate-500'
                      }`}
                    >
                      {idx < currentIdx ? <CheckCircle2 className="h-4 w-4" /> : idx + 1}
                    </div>
                    <span
                      className={`mt-1.5 text-[11px] font-medium ${idx <= currentIdx ? 'text-slate-800' : 'text-slate-400'}`}
                    >
                      {STATUS_LABELS[step]}
                    </span>
                  </div>
                  {idx < WORKFLOW.length - 1 && (
                    <div className={`mx-1 mb-5 h-0.5 flex-1 rounded ${idx < currentIdx ? 'bg-emerald-400' : 'bg-slate-200'}`} />
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="p-5">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900">
              <Search className="h-4 w-4 text-brand-600" />
              Details
            </h3>
            <dl className="space-y-3 text-sm">
              <div className="flex items-start justify-between">
                <dt className="flex items-center gap-1.5 text-slate-500">
                  <MapPin className="h-3.5 w-3.5" /> Barangay
                </dt>
                <dd className="font-medium text-slate-800">{inc.barangay}</dd>
              </div>
              <div className="flex items-start justify-between">
                <dt className="flex items-center gap-1.5 text-slate-500">
                  <Clock className="h-3.5 w-3.5" /> Reported
                </dt>
                <dd className="text-right font-medium text-slate-800">{formatDateTime(inc.reported_at)}</dd>
              </div>
              <div className="flex items-start justify-between">
                <dt className="flex items-center gap-1.5 text-slate-500">
                  <Clock className="h-3.5 w-3.5" /> Updated
                </dt>
                <dd className="text-right font-medium text-slate-800">{formatDateTime(inc.updated_at)}</dd>
              </div>
              <div className="flex items-start justify-between">
                <dt className="flex items-center gap-1.5 text-slate-500">
                  <UserIcon className="h-3.5 w-3.5" /> Reported by
                </dt>
                <dd className="font-medium text-slate-800">{inc.reported_by ?? '—'}</dd>
              </div>
              {inc.lat !== undefined && inc.lng !== undefined && (
                <div className="flex items-start justify-between">
                  <dt className="flex items-center gap-1.5 text-slate-500">
                    <MapPin className="h-3.5 w-3.5" /> Coordinates
                  </dt>
                  <dd className="text-right font-medium text-slate-800">
                    {inc.lat.toFixed(4)}, {inc.lng.toFixed(4)}
                  </dd>
                </div>
              )}
            </dl>
          </Card>

          <Card className="p-5">
            <h3 className="mb-3 text-sm font-semibold text-slate-900">Readiness in {inc.barangay}</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-brand-50 p-3">
                <Users className="mb-1 h-4 w-4 text-brand-600" />
                <p className="text-lg font-bold text-slate-900">{formatNumber(barangayHouseholds)}</p>
                <p className="text-xs text-slate-500">households</p>
              </div>
              <div className="rounded-lg bg-emerald-50 p-3">
                <Building2 className="mb-1 h-4 w-4 text-emerald-600" />
                <p className="text-lg font-bold text-slate-900">{barangayCenters}</p>
                <p className="text-xs text-slate-500">evacuation centers</p>
              </div>
              <div className="rounded-lg bg-danger-50 p-3">
                <Users className="mb-1 h-4 w-4 text-danger-600" />
                <p className="text-lg font-bold text-slate-900">
                  {inc.affected_households ? formatNumber(inc.affected_households) : '—'}
                </p>
                <p className="text-xs text-slate-500">affected households</p>
              </div>
              <div className="rounded-lg bg-amber-50 p-3">
                <Siren className="mb-1 h-4 w-4 text-amber-600" />
                <p className="text-lg font-bold capitalize text-slate-900">{inc.severity}</p>
                <p className="text-xs text-slate-500">severity</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}