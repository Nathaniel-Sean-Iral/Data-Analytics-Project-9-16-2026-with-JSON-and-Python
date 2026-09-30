import { useMemo, useRef, useState } from 'react';
import { Users, Pencil, Trash2, Plus, FileUp, Phone, Home } from 'lucide-react';
import { PageHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DataTable, type Column } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Modal } from '@/components/ui/modal';
import { Input, Select, Textarea, FormField } from '@/components/ui/form';
import { useToast } from '@/components/ui/toast';
import { useAuth } from '@/auth/AuthContext';
import { useAsync } from '@/lib/useAsync';
import {
  fetchHouseholds,
  createHousehold,
  updateHousehold,
  deleteHousehold,
  importHouseholdsCsv,
} from '@/api/services';
import { BARANGAYS } from '@/api/mock';
import type { Household } from '@/api/types';
import { formatNumber } from '@/lib/labels';
import { MUNICIPALITY_CENTER } from '@/lib/location';

type HouseholdForm = Omit<Household, 'id'>;

const EMPTY_FORM: HouseholdForm = {
  household_no: '',
  head_name: '',
  address: '',
  barangay: BARANGAYS[0],
  size: 1,
  children_count: 0,
  elderly_count: 0,
  pwd_count: 0,
  contact: '',
<<<<<<< HEAD
  lat: MUNICIPALITY_CENTER[0],
  lng: MUNICIPALITY_CENTER[1],
=======
  lat: 14.95,
  lng: 121.10,
>>>>>>> 9845aeb (Your descriptive commit message here)
  notes: '',
};

interface FormErrors {
  [key: string]: string | undefined;
}

function validate(form: HouseholdForm): FormErrors {
  const errors: FormErrors = {};
  if (!form.household_no.trim()) errors.household_no = 'Household number is required';
  if (!form.head_name.trim()) errors.head_name = 'Head of household is required';
  if (!form.address.trim()) errors.address = 'Address is required';
  if (!form.barangay) errors.barangay = 'Barangay is required';
  if (form.size < 1) errors.size = 'At least 1 member';
  if (form.children_count < 0) errors.children_count = 'Cannot be negative';
  if (form.elderly_count < 0) errors.elderly_count = 'Cannot be negative';
  if (form.pwd_count < 0) errors.pwd_count = 'Cannot be negative';
  if (form.lat < -90 || form.lat > 90) errors.lat = 'Latitude must be between -90 and 90';
  if (form.lng < -180 || form.lng > 180) errors.lng = 'Longitude must be between -180 and 180';
  return errors;
}

function HouseholdFormModal({
  open,
  onClose,
  initial,
  onSubmit,
  saving,
  title,
}: {
  open: boolean;
  onClose: () => void;
  initial: HouseholdForm;
  onSubmit: (form: HouseholdForm) => Promise<void>;
  saving: boolean;
  title: string;
}) {
  const [form, setForm] = useState<HouseholdForm>(initial);
  const [errors, setErrors] = useState<FormErrors>({});

  const set = <K extends keyof HouseholdForm>(key: K, value: HouseholdForm[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  async function handleSubmit() {
    const nextErrors = validate(form);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;
    await onSubmit(form);
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      description="Household details are used for the evacuation allocation algorithm."
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} loading={saving}>
            Save household
          </Button>
        </>
      }
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField label="Household no." required error={errors.household_no}>
          <Input value={form.household_no} onChange={(e) => set('household_no', e.target.value)} placeholder="HH-0001" />
        </FormField>
        <FormField label="Head of household" required error={errors.head_name}>
          <Input value={form.head_name} onChange={(e) => set('head_name', e.target.value)} placeholder="Juan Dela Cruz" />
        </FormField>
        <FormField label="Address" required error={errors.address} hint="Street, purok, sitio">
          <Input value={form.address} onChange={(e) => set('address', e.target.value)} placeholder="Blk 1, Lot 2, Purok 3" />
        </FormField>
        <FormField label="Barangay" required error={errors.barangay}>
          <Select value={form.barangay} onChange={(e) => set('barangay', e.target.value)}>
            {BARANGAYS.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </Select>
        </FormField>
        <FormField label="Household size" required error={errors.size}>
          <Input type="number" min={1} value={form.size} onChange={(e) => set('size', Number(e.target.value))} />
        </FormField>
        <FormField label="Contact number" error={errors.contact}>
          <Input value={form.contact} onChange={(e) => set('contact', e.target.value)} placeholder="09xxxxxxxxx" />
        </FormField>
        <FormField label="Children (0–17)" error={errors.children_count}>
          <Input type="number" min={0} value={form.children_count} onChange={(e) => set('children_count', Number(e.target.value))} />
        </FormField>
        <FormField label="Elderly (60+)" error={errors.elderly_count}>
          <Input type="number" min={0} value={form.elderly_count} onChange={(e) => set('elderly_count', Number(e.target.value))} />
        </FormField>
        <FormField label="Persons with disability" error={errors.pwd_count}>
          <Input type="number" min={0} value={form.pwd_count} onChange={(e) => set('pwd_count', Number(e.target.value))} />
        </FormField>
        <FormField label="Latitude" error={errors.lat}>
          <Input type="number" step="any" value={form.lat} onChange={(e) => set('lat', Number(e.target.value))} />
        </FormField>
        <FormField label="Longitude" error={errors.lng}>
          <Input type="number" step="any" value={form.lng} onChange={(e) => set('lng', Number(e.target.value))} />
        </FormField>
        <div className="sm:col-span-2">
          <FormField label="Notes">
            <Textarea rows={2} value={form.notes ?? ''} onChange={(e) => set('notes', e.target.value)} placeholder="Special needs, mobility constraints, pets, etc." />
          </FormField>
        </div>
      </div>
    </Modal>
  );
}

function ConfirmDeleteModal({
  open,
  onClose,
  onConfirm,
  household,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  household: Household | null;
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Delete household"
      description="This action cannot be undone."
      size="sm"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="danger" onClick={onConfirm}>
            Delete
          </Button>
        </>
      }
    >
      <p className="text-sm text-slate-600">
        Remove <b>{household?.head_name}</b> ({household?.household_no}) and its allocation assignments?
      </p>
    </Modal>
  );
}

export function HouseholdsPage() {
  const { data, loading, refetch } = useAsync(() => fetchHouseholds());
  const { hasRole } = useAuth();
  const { success, error } = useToast();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const canEdit = hasRole('admin');
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Household | null>(null);
  const [deleting, setDeleting] = useState<Household | null>(null);
  const [saving, setSaving] = useState(false);

  const pageSize = 10;

  const filtered = useMemo(() => {
    const items = data?.items ?? [];
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (h) =>
        h.head_name.toLowerCase().includes(q) ||
        h.household_no.toLowerCase().includes(q) ||
        h.address.toLowerCase().includes(q) ||
        h.barangay.toLowerCase().includes(q),
    );
  }, [data, query]);

  const pageRows = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filtered.slice(start, start + pageSize);
  }, [filtered, page]);

  async function handleCreate(form: HouseholdForm) {
    setSaving(true);
    try {
      await createHousehold(form);
      success('Household created');
      setModalOpen(false);
      void refetch();
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to create household');
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdate(form: HouseholdForm) {
    if (!editing) return;
    setSaving(true);
    try {
      await updateHousehold(editing.id, form);
      success('Household updated');
      setModalOpen(false);
      void refetch();
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to update household');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!deleting) return;
    try {
      await deleteHousehold(deleting.id);
      success('Household deleted');
      setDeleting(null);
      void refetch();
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to delete household');
    }
  }

  async function handleImport(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const result = await importHouseholdsCsv(text);
      success(`${result.created} households imported`);
      event.target.value = '';
      void refetch();
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to import household CSV');
    }
  }

  const columns: Column<Household>[] = [
    {
      key: 'household_no',
      header: 'Household no.',
      sortValue: (r) => r.household_no,
      render: (r) => (
        <div className="flex items-center gap-2">
          <div className="rounded-md bg-slate-100 p-1.5 text-slate-500">
            <Home className="h-3.5 w-3.5" />
          </div>
          <div>
            <p className="font-medium text-slate-900">{r.household_no}</p>
            <p className="text-xs text-slate-500">{r.head_name}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'address',
      header: 'Address',
      render: (r) => (
        <div>
          <p className="text-slate-900">{r.address}</p>
          <Badge tone="slate" className="mt-0.5">{r.barangay}</Badge>
        </div>
      ),
    },
    {
      key: 'size',
      header: 'Size',
      sortValue: (r) => r.size,
      render: (r) => <span className="font-semibold text-slate-900">{r.size}</span>,
    },
    {
      key: 'vulnerable',
      header: 'Vulnerable',
      render: (r) => {
        const total = r.children_count + r.elderly_count + r.pwd_count;
        return <Badge tone={total > 0 ? 'amber' : 'slate'}>{total > 0 ? `${formatNumber(total)} member(s)` : 'None'}</Badge>;
      },
    },
    {
      key: 'contact',
      header: 'Contact',
      render: (r) =>
        r.contact ? (
          <span className="inline-flex items-center gap-1.5 text-slate-600">
            <Phone className="h-3.5 w-3.5 text-slate-400" />
            {r.contact}
          </span>
        ) : (
          <span className="text-slate-400">—</span>
        ),
    },
    {
      key: 'actions',
      header: '',
      className: 'text-right',
      render: (r) =>
        canEdit ? (
          <div className="flex justify-end gap-1">
            <Button
              variant="ghost"
              className="!px-2 !py-1.5"
              onClick={() => {
                setEditing(r);
                setModalOpen(true);
              }}
              aria-label={`Edit ${r.household_no}`}
            >
              <Pencil className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              className="!px-2 !py-1.5 !text-danger-600 hover:!bg-danger-50"
              onClick={() => setDeleting(r)}
              aria-label={`Delete ${r.household_no}`}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <span className="text-xs text-slate-400">—</span>
        ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="Households"
        description="Registry of households with vulnerable-member breakdown, used by the allocation engine."
        icon={<Users className="h-5 w-5" />}
        actions={
          canEdit ? (
            <>
              <input ref={fileInputRef} type="file" accept=".csv,text/csv" className="hidden" onChange={handleImport} />
              <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
                <FileUp className="h-4 w-4" />
                Import
              </Button>
              <Button
                onClick={() => {
                  setEditing(null);
                  setModalOpen(true);
                }}
              >
                <Plus className="h-4 w-4" />
                Add household
              </Button>
            </>
          ) : undefined
        }
      />

      <DataTable
        columns={columns}
        rows={pageRows}
        keyFor={(r) => r.id}
        loading={loading}
        searchable
        searchPlaceholder="Search household no., head, address…"
        onSearch={(q) => {
          setQuery(q);
          setPage(1);
        }}
        sortable
        page={page}
        pageSize={pageSize}
        total={filtered.length}
        onPageChange={setPage}
        emptyTitle="No households yet"
        emptyDescription="Add your first household to start tracking the registry."
      />

      {modalOpen && (
        <HouseholdFormModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          initial={editing ? { ...editing, notes: editing.notes ?? '' } : EMPTY_FORM}
          onSubmit={editing ? handleUpdate : handleCreate}
          saving={saving}
          title={editing ? `Edit ${editing.household_no}` : 'Add household'}
        />
      )}

      <ConfirmDeleteModal open={Boolean(deleting)} onClose={() => setDeleting(null)} onConfirm={handleDelete} household={deleting} />
    </div>
  );
}