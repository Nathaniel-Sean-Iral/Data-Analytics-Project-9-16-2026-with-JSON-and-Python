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
import { MUNICIPALITY_CENTER } from '@/lib/location';

export const BARANGAYS = [
  'BMA-Balagtas',
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
  'Salapongan',
  'Sampaloc',
  'San Agustin',
  'San Roque',
  'Talacsan',
  'Tambubong',
  'Tukod',
  'Ulingao',
  'Sapang Pahalang',
] as const;

/** Approximate centroids, [lat, lng], spread around MUNICIPALITY_CENTER. */
export const BARANGAY_CENTROIDS: Record<string, [number, number]> = {
  'BMA-Balagtas': [14.9568, 120.9519],
  'Banca-banca': [14.98, 120.974],
  Caingin: [14.9322, 120.954],
  'Coral na Bato': [14.925, 120.992],
  'Cruz na Daan': [14.9905, 120.948],
  'Dagat-dagatan': [14.944, 120.932],
  'Diliman I': [14.97, 120.988],
  'Diliman II': [14.976, 120.996],
  Capihan: [14.961, 120.942],
  Libis: [14.9605, 120.9555],
  Lico: [14.953, 120.969],
  Maasim: [14.996, 120.988],
  'Mabalas-balas': [14.9085, 120.97],
  Maguinao: [14.9355, 120.9845],
  Maronquillo: [14.99, 120.962],
  Paco: [14.92, 120.96],
  Pansumaloc: [14.913, 120.945],
  Pantubig: [14.968, 120.935],
  'Pasong Bangkal': [14.981, 120.954],
  'Pasong Callos': [14.966, 120.97],
  'Pasong Intsik': [14.9645, 120.9665],
  Pinacpinacan: [14.9505, 120.974],
  Poblacion: [14.9571, 120.9629],
  Pulo: [14.94, 120.968],
  'Pulong Bayabas': [14.925, 120.978],
  Salapongan: [14.951, 120.98],
  Sampaloc: [14.964, 120.959],
  'San Agustin': [14.942, 120.99],
  'San Roque': [14.97, 120.978],
  Talacsan: [14.9855, 120.94],
  Tambubong: [14.937, 120.952],
  Tukod: [14.948, 120.94],
  Ulingao: [14.988, 120.972],
  'Sapang Pahalang': [14.915, 120.988],
};

export function coordinatesFor(barangay: string): [number, number] {
  return BARANGAY_CENTROIDS[barangay] ?? MUNICIPALITY_CENTER;
}


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
    const [baseLat, baseLng] = coordinatesFor(barangay);
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
      lat: baseLat + ((i % 5) - 2) * 0.0015,
      lng: baseLng + (((i * 3) % 5) - 2) * 0.0015,
    });
  }
  return households;
}

const centers: EvacuationCenter[] = [
  { id: 1, name: 'Poblacion Elementary School', barangay: 'Poblacion', address: 'Brgy Hall Rd', capacity: 500, current_occupants: 210, facilities: ['kitchen', 'water', 'power', 'bathrooms'], contact: '09171234001', lat: 14.9578, lng: 120.9642, status: 'active' },
  { id: 2, name: 'San Roque Covered Court', barangay: 'San Roque', address: 'Mabini St', capacity: 300, current_occupants: 120, facilities: ['water', 'power'], contact: '09171234002', lat: 14.9692, lng: 120.9788, status: 'active' },
  { id: 3, name: 'Maronquillo High School', barangay: 'Maronquillo', address: 'DRT Highway', capacity: 450, current_occupants: 305, facilities: ['kitchen', 'water', 'power', 'bathrooms', 'clinic'], contact: '09171234003', lat: 14.9903, lng: 120.9625, status: 'active' },
  { id: 4, name: 'BMA-Balagtas Gymnasium', barangay: 'BMA-Balagtas', address: 'Rizal Ave', capacity: 200, current_occupants: 15, facilities: ['water', 'power'], contact: '09171234004', lat: 14.9565, lng: 120.9524, status: 'standby' },
  { id: 5, name: 'Pantubig Barangay Hall', barangay: 'Pantubig', address: 'Pantubig Road', capacity: 150, current_occupants: 88, facilities: ['kitchen', 'water'], contact: '09171234005', lat: 14.968, lng: 120.935, status: 'active' },
  { id: 6, name: 'Sampaloc Community Center', barangay: 'Sampaloc', address: 'Sampaloc Road', capacity: 400, current_occupants: 240, facilities: ['kitchen', 'water', 'power', 'bathrooms'], contact: '09171234006', lat: 14.964, lng: 120.959, status: 'active' },
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
  { id: 1, title: 'Flash flood due to monsoon rains', type: 'flood', barangay: 'Mabalas-balas', severity: 'high', status: 'responding', description: 'River overflow submerged low-lying streets. Residents moved to Sampaloc Community Center.', reported_at: '2026-09-15T06:15:00Z', updated_at: '2026-09-16T08:00:00Z', lat: 14.9085, lng: 120.97, affected_households: 45, reported_by: 'MDRRMO' },
  { id: 2, title: 'Fire broke out in residential area', type: 'fire', barangay: 'Poblacion', severity: 'critical', status: 'assessing', description: 'Fire affected 8 houses near the public market. Fire trucks on scene.', reported_at: '2026-09-16T11:40:00Z', updated_at: '2026-09-16T12:10:00Z', lat: 14.9565, lng: 120.966, affected_households: 8, reported_by: 'BFP' },
  { id: 3, title: 'Landslide along mountain road', type: 'landslide', barangay: 'Coral na Bato', severity: 'moderate', status: 'assessing', description: 'Debris blocked access road; no casualties reported yet.', reported_at: '2026-09-14T14:05:00Z', updated_at: '2026-09-15T07:30:00Z', lat: 14.925, lng: 120.992, affected_households: 3, reported_by: 'Barangay Coral na Bato' },
  { id: 4, title: 'Storm surge warning issued', type: 'typhoon', barangay: 'Ulingao', severity: 'low', status: 'reported', description: 'Pre-emptive evacuation being organized ahead of projected storm surge.', reported_at: '2026-09-16T02:00:00Z', updated_at: '2026-09-16T02:00:00Z', lat: 14.988, lng: 120.972, affected_households: 20, reported_by: 'PAGASA' },
  { id: 5, title: 'River overflow in low-lying areas', type: 'flood', barangay: 'San Roque', severity: 'high', status: 'responding', description: 'Water level at knee-to-waist height along Mabini St.', reported_at: '2026-09-15T05:45:00Z', updated_at: '2026-09-16T07:00:00Z', lat: 14.9698, lng: 120.9782, affected_households: 32, reported_by: 'MDRRMO' },
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
    coverage_gaps: ['Coral na Bato has no evacuation center - pre-position transport assets.'],
  };
}

export { resourceLabels };