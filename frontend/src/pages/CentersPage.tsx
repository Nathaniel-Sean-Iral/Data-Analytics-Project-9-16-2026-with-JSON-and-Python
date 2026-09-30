import { useMemo, useState } from 'react';
import {
  Building2,
  Plus,
  Pencil,
  Phone,
  MapPin,
  Users,
  ChefHat,
  Droplets,
  Zap,
  Bed,
  Stethoscope,
} from 'lucide-react';
import { PageHeader, Card, ProgressBar } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Modal } from '@/components/ui/modal';
import { Input, Select, FormField } from '@/components/ui/form';
import { useToast } from '@/components/ui/toast';
import { useAuth } from '@/auth/AuthContext';
import { useAsync } from '@/lib/useAsync';
import { fetchCenters, createCenter, updateCenter } from '@/api/services';
import { BARANGAYS } from '@/api/mock';
import { CENTER_STATUS_TONES } from '@/lib/labels';
import { MUNICIPALITY_CENTER } from '@/lib/location';
import type { CenterStatus, EvacuationCenter } from '@/api/types';

const FACILITY_OPTIONS = [
  { value: 'kitchen', label: 'Kitchen', icon: <ChefHat className="h-4 w-4" /> },
  { value: 'water', label: 'Water', icon: <Droplets className="h-4 w-4" /> },
  { value: 'power', label: 'Power', icon: <Zap className="h-4 w-4" /> },
  { value: 'bathrooms', label: 'Bathrooms', icon: <Users className="h-4 w-4" /> },
  { value: 'clinic', label: 'Clinic', icon: <Stethoscope className="h-4 w-4" /> },
  { value: 'beds', label: 'Beds', icon: <Bed className="h-4 w-4" /> },
];

type CenterForm = Omit<EvacuationCenter, 'id'>;

const EMPTY_FORM: CenterForm = {
  name: '',
  barangay: BARANGAYS[0],
  address: '',
  capacity: 100,
  current_occupants: 0,
  facilities: ['water', 'power'],
  contact: '',
  lat: MUNICIPALITY_CENTER[0],
  lng: MUNICIPALITY_CENTER[1],
  status: 'standby',
};

function loadTone(percent: number): 'green' | 'amber' | 'red' {
  return percent >= 90 ? 'red' : percent >= 70 ? 'amber' : 'green';
}

function CenterFormModal({
  open,
  onClose,
  initial,
  onSubmit,
  saving,
  title,
}: {
  open: boolean;
  onClose: () => void;
  initial: CenterForm;
  onSubmit: (form: CenterForm) => Promise<void>;
  saving: boolean;
  title: string;
}) {
  const [form, setForm] = useState<CenterForm>(initial);

  const set = <K extends keyof CenterForm>(key: K, value: CenterForm[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const toggleFacility = (facility: string) =>
    setForm((prev) => ({
      ...prev,
      facilities: prev.facilities.includes(facility)
        ? prev.facilities.filter((f) => f !== facility)
        : [...prev.facilities, facility],
    }));

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      description="Evacuation centers are the destinations used by the allocation algorithm."
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={() => void onSubmit(form)} loading={saving}>
            Save center
          </Button>
        </>
      }
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField label="Center name" required>
          <Input value={form.name} onChange={(e) => set('name', e.target.value)} placeholder="Poblacion Elementary School" />
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
        <FormField label="Address">
          <Input value={form.address} onChange={(e) => set('address', e.target.value)} placeholder="Street / building" />
        </FormField>
        <FormField label="Contact">
          <Input value={form.contact ?? ''} onChange={(e) => set('contact', e.target.value)} placeholder="09xxxxxxxxx" />
        </FormField>
        <FormField label="Capacity" required hint="Maximum number of evacuees">
          <Input type="number" min={1} value={form.capacity} onChange={(e) => set('capacity', Number(e.target.value))} />
        </FormField>
        <FormField label="Current occupants" required>
          <Input type="number" min={0} value={form.current_occupants} onChange={(e) => set('current_occupants', Number(e.target.value))} />
        </FormField>
        <FormField label="Latitude">
          <Input type="number" step="any" value={form.lat} onChange={(e) => set('lat', Number(e.target.value))} />
        </FormField>
        <FormField label="Longitude">
          <Input type="number" step="any" value={form.lng} onChange={(e) => set('lng', Number(e.target.value))} />
        </FormField>
        <div className="sm:col-span-2">
          <FormField label="Status">
            <Select value={form.status} onChange={(e) => set('status', e.target.value as CenterStatus)}>
              <option value="active">Active</option>
              <option value="standby">Standby</option>
              <option value="closed">Closed</option>
            </Select>
          </FormField>
        </div>
        <div className="sm:col-span-2">
          <span className="label">Facilities</span>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {FACILITY_OPTIONS.map((f) => {
              const active = form.facilities.includes(f.value);
              return (
                <button
                  key={f.value}
                  type="button"
                  onClick={() => toggleFacility(f.value)}
                  className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                    active
                      ? 'border-brand-600 bg-brand-50 text-brand-700'
                      : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {f.icon}
                  {f.label}
                  <span className="ml-auto text-xs">{active ? '✓' : ''}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </Modal>
  );
}

export function CentersPage() {
  const { data, loading, refetch } = useAsync(() => fetchCenters());
  const { hasRole } = useAuth();
  const { success, error } = useToast();
  const canEdit = hasRole('admin');

  const [detail, setDetail] = useState<EvacuationCenter | null>(null);
  const [editing, setEditing] = useState<EvacuationCenter | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const totalCapacity = useMemo(() => (data ?? []).reduce((s, c) => s + c.capacity, 0), [data]);
  const totalOccupants = useMemo(() => (data ?? []).reduce((s, c) => s + c.current_occupants, 0), [data]);

  async function handleSubmit(form: CenterForm) {
    setSaving(true);
    try {
      if (editing) {
        await updateCenter(editing.id, form);
        success('Evacuation center updated');
      } else {
        await createCenter(form);
        success('Evacuation center created');
      }
      setModalOpen(false);
      void refetch();
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to save center');
    } finally {
      setSaving(false);
    }
  }

  const facilitiesById = new Map(FACILITY_OPTIONS.map((f) => [f.value, f]));

  return (
    <div>
      <PageHeader
        title="Evacuation Centers"
        description="Facilities where affected households are assigned during operations."
        icon={<Building2 className="h-5 w-5" />}
        actions={
          canEdit ? (
            <Button
              onClick={() => {
                setEditing(null);
                setModalOpen(true);
              }}
            >
              <Plus className="h-4 w-4" />
              Add center
            </Button>
          ) : undefined
        }
      />

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="flex items-center justify-between p-4">
          <div>
            <p className="text-xs font-medium uppercase text-slate-500">Centers</p>
            <p className="text-xl font-bold text-slate-900">{data?.length ?? 0}</p>
          </div>
          <Building2 className="h-5 w-5 text-brand-500" />
        </Card>
        <Card className="flex items-center justify-between p-4">
          <div>
            <p className="text-xs font-medium uppercase text-slate-500">Total capacity</p>
            <p className="text-xl font-bold text-slate-900">{totalCapacity}</p>
          </div>
          <Users className="h-5 w-5 text-emerald-500" />
        </Card>
        <Card className="flex items-center justify-between p-4">
          <div>
            <p className="text-xs font-medium uppercase text-slate-500">Overall occupancy</p>
            <p className="text-xl font-bold text-slate-900">
              {totalCapacity ? Math.round((totalOccupants / totalCapacity) * 100) : 0}%
            </p>
          </div>
          <Users className="h-5 w-5 text-amber-500" />
        </Card>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="h-44 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {(data ?? []).map((c) => {
            const load = Math.round((c.current_occupants / c.capacity) * 100);
            return (
              <Card key={c.id} className="flex flex-col p-5">
                <div className="flex items-start justify-between">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-900">{c.name}</p>
                    <p className="mt-0.5 inline-flex items-center gap-1 text-xs text-slate-500">
                      <MapPin className="h-3 w-3" />
                      {c.barangay}
                    </p>
                  </div>
                  <Badge tone={CENTER_STATUS_TONES[c.status]} dot>
                    {c.status}
                  </Badge>
                </div>
                <div className="mt-4">
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span className="text-slate-500">Occupancy</span>
                    <span className="font-medium text-slate-700">
                      {c.current_occupants} / {c.capacity}
                    </span>
                  </div>
                  <ProgressBar value={load} tone={loadTone(load)} />
                  <p className={`mt-2 text-xs font-semibold ${load >= 70 ? 'text-danger-600' : 'text-emerald-600'}`}>
                    {load >= 90 ? 'Full' : load >= 70 ? 'Near capacity' : 'Plenty of room'}
                    {c.capacity - c.current_occupants > 0 && ` · ${c.capacity - c.current_occupants} spaces left`}
                  </p>
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {c.facilities.map((f) => (
                    <Badge key={f} tone="slate">
                      {facilitiesById.get(f)?.label ?? f}
                    </Badge>
                  ))}
                </div>
                <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
                  {c.contact ? (
                    <span className="inline-flex items-center gap-1 text-xs text-slate-500">
                      <Phone className="h-3 w-3" />
                      {c.contact}
                    </span>
                  ) : (
                    <span />
                  )}
                  <div className="flex gap-1">
                    {canEdit && (
                      <Button
                        variant="ghost"
                        className="!px-2 !py-1"
                        onClick={() => {
                          setEditing(c);
                          setModalOpen(true);
                        }}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                    )}
                    <Button variant="secondary" className="!px-2.5 !py-1 !text-xs" onClick={() => setDetail(c)}>
                      View
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {modalOpen && (
        <CenterFormModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          initial={editing ?? EMPTY_FORM}
          onSubmit={handleSubmit}
          saving={saving}
          title={editing ? `Edit ${editing.name}` : 'Add evacuation center'}
        />
      )}

      <Modal
        open={Boolean(detail)}
        onClose={() => setDetail(null)}
        title={detail?.name ?? ''}
        description={detail ? `${detail.address || detail.barangay} · ${detail.barangay}` : ''}
        footer={
          <Button variant="secondary" onClick={() => setDetail(null)}>
            Close
          </Button>
        }
      >
        {detail && (
          <div className="space-y-4">
            <div>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="font-medium text-slate-700">Occupancy</span>
                <span className="text-slate-500">
                  {detail.current_occupants} of {detail.capacity} ({Math.round((detail.current_occupants / detail.capacity) * 100)}%)
                </span>
              </div>
              <ProgressBar value={(detail.current_occupants / detail.capacity) * 100} tone={loadTone((detail.current_occupants / detail.capacity) * 100)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-xs text-slate-500">Status</p>
                <Badge tone={CENTER_STATUS_TONES[detail.status]} dot className="mt-1 capitalize">
                  {detail.status}
                </Badge>
              </div>
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-xs text-slate-500">Contact</p>
                <p className="mt-1 text-sm font-medium text-slate-800">{detail.contact || '—'}</p>
              </div>
            </div>
            <div>
              <p className="mb-1.5 text-xs font-medium text-slate-500">Coordinates</p>
              <p className="text-sm text-slate-700">
                {detail.lat.toFixed(5)}, {detail.lng.toFixed(5)}
              </p>
            </div>
            <div>
              <p className="mb-1.5 text-xs font-medium text-slate-500">Facilities</p>
              <div className="flex flex-wrap gap-1.5">
                {detail.facilities.map((f) => (
                  <Badge key={f} tone="blue">
                    {facilitiesById.get(f)?.label ?? f}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}