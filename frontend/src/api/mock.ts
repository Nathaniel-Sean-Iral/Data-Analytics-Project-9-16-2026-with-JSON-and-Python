import type {
  AllocationResult,
  CenterLoad,
  EvacuationCenter,
  Household,
  Incident,
  Resource,
  ResourceType,
  ResourceSummary,
} from './types';

export const BARANGAYS = [
  'Balagtas',
  'Banca-banca',
  'Caingin',
  'Coral na Bato',
  'Cruz na Daan',
  'Dagat-dagatan',
  'Diliman I',
  'Diliman II',
  'Capihan',
  'Libis',
  'Lico',
  'Maasim',
  'Mabalas-balas',
  'Maguinao',
  'Maronquillo',
  'Paco',
  'Pansumaloc',
  'Pantubig',
  'Pasong Bangkal',
  'Pasong Callos',
  'Pasong Intsik',
  'Pinacpinacan',
  'Poblacion',
  'Pulo',
  'Pulong Bayabas',
  'Salapungan',
  'Sampaloc',
  'San Agustin',
  'San Roque',
  'Talacsan',
  'Tambubong',
  'Tukod',
  'Ulingao',
  'Sapang Pahalang',
] as const;

const householdNames: Array<[string, string]> = [
  ['Reyes', 'Juan'],
  ['Santos', 'Maria'],
  ['Cruz', 'Pedro'],
  ['Bautista', 'Ana'],
  ['Ocampo', 'Ramon'],
  ['Villanueva', 'Liza'],
  ['Ramos', 'Mario'],
  ['Garcia', 'Nena'],
  ['Mendoza', 'Rico'],
  ['Torres', 'Carmen'],
  ['Flores', 'Berto'],
  ['Aquino', 'Gemma'],
  ['Navarro', 'Dante'],
  ['Salazar', 'Corazon'],
  ['Del Rosario', 'Efren'],
  ['Padilla', 'Flor'],
  ['Dizon', 'Gilbert'],
  ['Castillo', 'Helen'],
  ['Mercado', 'Irene'],
  ['Lopez', 'Jose'],
];

function makeHouseholds(count: number): Household[] {
  const households: Household[] = [];
  for (let i = 0; i < count; i++) {
    const [family, given] = householdNames[i % householdNames.length];
    const barangay = BARANGAYS[i % BARANGAYS.length];
    const size = 2 + ((i * 3) % 6);
    const rand = (n: number) => (i * 7 + n * 13) % 100;
    households.push({
      id: i + 1,
      household_no: `HH-${String(i + 1).padStart(4, '0')}`,
      head_name: `${given} ${family}`,
      address: `Blk ${(i % 20) + 1}, Lot ${(i % 8) + 1}, ${barangay}`,
      barangay,
      size,
      children_count: rand(1) % 4,
      elderly_count: rand(2) % 3,
      pwd_count: rand(3) % 2,
      contact: `09${String((i * 123456 + 1000000) % 100000000).padStart(8, '0')}`,
      lat: 14.08 + (i % 8) * 0.02,
      lng: 121.14 + ((i * 3) % 8) * 0.018,
    });
  }
  return households;
}

const centers: EvacuationCenter[] = [
  { id: 1, name: 'Poblacion Elementary School', barangay: 'Poblacion', address: 'Brgy Hall Rd', capacity: 500, current_occupants: 210, facilities: ['kitchen', 'water', 'power', 'bathrooms'], contact: '09171234001', lat: 14.095, lng: 121.148, status: 'active' },
  { id: 2, name: 'San Roque Covered Court', barangay: 'San Roque', address: 'Mabini St', capacity: 300, current_occupants: 120, facilities: ['water', 'power'], contact: '09171234002', lat: 14.082, lng: 121.13, status: 'active' },
  { id: 3, name: 'San Juan High School', barangay: 'San Juan', address: 'National Rd', capacity: 450, current_occupants: 305, facilities: ['kitchen', 'water', 'power', 'bathrooms', 'clinic'], contact: '09171234003', lat: 14.11, lng: 121.16, status: 'active' },
  { id: 4, name: 'Santo Niño Gymnasium', barangay: 'Santo Niño', address: 'Rizal Ave', capacity: 200, current_occupants: 15, facilities: ['water', 'power'], contact: '09171234004', lat: 14.07, lng: 121.125, status: 'standby' },
  { id: 5, name: 'Bagong Silang Barangay Hall', barangay: 'Bagong Silang', address: 'Diversity Rd', capacity: 150, current_occupants: 88, facilities: ['kitchen', 'water'], contact: '09171234005', lat: 14.125, lng: 121.175, status: 'active' },
  { id: 6, name: 'Malanday Community Center', barangay: 'Malanday', address: 'Seaside Rd', capacity: 400, current_occupants: 240, facilities: ['kitchen', 'water', 'power', 'bathrooms'], contact: '09171234006', lat: 14.062, lng: 121.108, status: 'active' },
];

const resources: Resource[] = [
  { id: 1, name: 'Rice (50kg sack)', type: 'rice', unit: 'sacks', quantity_on_hand: 320, threshold: 200, stored_in: 'Municipal Warehouse', updated_at: '2026-09-16T09:00:00Z' },
  { id: 2, name: 'Bottled Water (gallon)', type: 'water', unit: 'gallons', quantity_on_hand: 140, threshold: 400, stored_in: 'Municipal Warehouse', updated_at: '2026-09-16T09:00:00Z' },
  { id: 3, name: 'Medicine Kit', type: 'medicine', unit: 'kits', quantity_on_hand: 45, threshold: 60, stored_in: 'Rural Health Unit', updated_at: '2026-09-16T09:00:00Z' },
  { id: 4, name: 'Blankets', type: 'blankets', unit: 'pc', quantity_on_hand: 260, threshold: 150, stored_in: 'Rotary Store', updated_at: '2026-09-16T09:00:00Z' },
  { id: 5, name: 'Hygiene Kits', type: 'hygiene', unit: 'kits', quantity_on_hand: 90, threshold: 120, stored_in: 'Municipal Warehouse', updated_at: '2026-09-16T09:00:00Z' },
  { id: 6, name: 'Canned Sardines', type: 'canned_goods', unit: 'cans', quantity_on_hand: 480, threshold: 300, stored_in: 'Municipal Warehouse', updated_at: '2026-09-16T09:00:00Z' },
  { id: 7, name: 'Tents', type: 'tents', unit: 'pc', quantity_on_hand: 12, threshold: 30, stored_in: 'MDRRMO Office', updated_at: '2026-09-16T09:00:00Z' },
  { id: 8, name: 'Sleeping Mats', type: 'mats', unit: 'pc', quantity_on_hand: 300, threshold: 180, stored_in: 'Rotary Store', updated_at: '2026-09-16T09:00:00Z' },
];

const incidents: Incident[] = [
  { id: 1, title: 'Flash flood due to monsoon rains', type: 'flood', barangay: 'Malanday', severity: 'high', status: 'responding', description: 'River overflow submerged low-lying streets. Residents moved to Malanday Community Center.', reported_at: '2026-09-15T06:15:00Z', updated_at: '2026-09-16T08:00:00Z', lat: 14.061, lng: 121.107, affected_households: 45, reported_by: 'MDRRMO' },
  { id: 2, title: 'Fire broke out in residential area', type: 'fire', barangay: 'Poblacion', severity: 'critical', status: 'assessing', description: 'Fire affected 8 houses near the public market. Fire trucks on scene.', reported_at: '2026-09-16T11:40:00Z', updated_at: '2026-09-16T12:10:00Z', lat: 14.094, lng: 121.147, affected_households: 8, reported_by: 'BFP' },
  { id: 3, title: 'Landslide along mountain road', type: 'landslide', barangay: 'Kalayaan', severity: 'moderate', status: 'assessing', description: 'Debris blocked access road; no casualties reported yet.', reported_at: '2026-09-14T14:05:00Z', updated_at: '2026-09-15T07:30:00Z', lat: 14.13, lng: 121.2, affected_households: 3, reported_by: 'Barangay Tanod' },
  { id: 4, title: 'Storm surge warning issued', type: 'typhoon', barangay: 'San Juan', severity: 'low', status: 'reported', description: 'Pre-emptive evacuation being organized ahead of projected storm surge.', reported_at: '2026-09-16T02:00:00Z', updated_at: '2026-09-16T02:00:00Z', lat: 14.109, lng: 121.159, affected_households: 20, reported_by: 'PAGASA' },
  { id: 5, title: 'River overflow in low-lying areas', type: 'flood', barangay: 'San Roque', severity: 'high', status: 'responding', description: 'Water level at knee-to-waist height along Mabini St.', reported_at: '2026-09-15T05:45:00Z', updated_at: '2026-09-16T07:00:00Z', lat: 14.081, lng: 121.129, affected_households: 32, reported_by: 'MDRRMO' },
];

const resourceLabels: Record<ResourceType, string> = {
  rice: 'Rice',
  water: 'Water',
  medicine: 'Medicine',
  blankets: 'Blankets',
  hygiene: 'Hygiene Kits',
  canned_goods: 'Canned Goods',
  clothing: 'Clothing',
  mats: 'Sleeping Mats',
  tents: 'Tents',
  other: 'Other',
};

export function mockHouseholds(): Household[] {
  return makeHouseholds(40);
}

export function mockHousehold(id: number): Household | undefined {
  return makeHouseholds(40).find((h) => h.id === id);
}

export function mockCenters(): EvacuationCenter[] {
  return centers;
}

export function mockResources(): Resource[] {
  return resources;
}

export function mockResourceSummaries(): ResourceSummary[] {
  return resources.map((r) => {
    const required = r.name.startsWith('Bottled Water') ? r.threshold * 3 : r.threshold;
    return {
      type: r.type,
      label: resourceLabels[r.type],
      total_on_hand: r.quantity_on_hand,
      total_required: required,
      gap: r.quantity_on_hand - required,
      low_stock_count: r.quantity_on_hand < r.threshold ? 1 : 0,
    };
  });
}

export function mockIncidents(): Incident[] {
  return incidents;
}

export function mockIncident(id: number): Incident | undefined {
  return incidents.find((i) => i.id === id);
}

export function mockAllocation(barangay?: string): AllocationResult {
  const all = makeHouseholds(40);
  const pool = barangay ? all.filter((h) => h.barangay === barangay) : all;
  const assignments = pool.map((h, idx) => {
    const center = centers[idx % centers.length];
    return {
      id: idx + 1,
      household_id: h.id,
      household_no: h.household_no,
      household_head: h.head_name,
      barangay: h.barangay,
      center_id: center.id,
      center_name: center.name,
      center_load_percent: Math.min(100, Math.round((center.current_occupants / center.capacity) * 100)),
      assigned_at: '2026-09-16T12:00:00Z',
    };
  });

  const centerLoads: CenterLoad[] = centers.map((c) => ({
    center_id: c.id,
    center_name: c.name,
    barangay: c.barangay,
    capacity: c.capacity,
    occupants: c.current_occupants,
    load_percent: Math.round((c.current_occupants / c.capacity) * 100),
    status: c.current_occupants / c.capacity > 0.9 ? 'full' : c.current_occupants / c.capacity > 0.7 ? 'near_capacity' : 'ok',
  }));

  return {
    request_id: `ALLOC-${Date.now().toString(36).toUpperCase()}`,
    generated_at: new Date().toISOString(),
    total_households: pool.length,
    assigned_households: pool.length,
    overflow_households: 0,
    assignments,
    center_loads: centerLoads,
    overflow: [],
    coverage_gaps: ['Kalayaan has no evacuation center — pre-position transport assets.'],
  };
}

export { resourceLabels };