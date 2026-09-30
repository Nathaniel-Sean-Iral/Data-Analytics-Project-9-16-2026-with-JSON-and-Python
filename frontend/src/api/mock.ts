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

/** OSM centroids, [lat, lng]. Mirrors backend/app/core/location.py. */
export const BARANGAY_CENTROIDS: Record<string, [number, number]> = {
  'BMA-Balagtas': [14.96896, 120.96719],
  'Banca-banca': [15.0242, 120.92146],
  Caingin: [14.97175, 120.94344],
  'Coral na Bato': [14.99425, 120.97917],
  'Cruz na Daan': [15.02956, 120.93478],
  'Dagat-dagatan': [15.03384, 120.9145],
  'Diliman I': [15.02433, 120.94924],
  'Diliman II': [15.03318, 120.95317],
  Capihan: [14.99886, 120.93026],
  Libis: [14.95701, 120.96948],
  Lico: [14.96104, 120.95632],
  Maasim: [15.03523, 120.93637],
  'Mabalas-balas': [15.0253, 120.94267],
  Maguinao: [15.02276, 120.93356],
  Maronquillo: [14.96739, 121.0014],
  Paco: [14.99586, 120.90566],
  Pansumaloc: [15.01738, 120.89682],
  Pantubig: [14.9655, 120.95296],
  'Pasong Bangkal': [15.00584, 121.00997],
  'Pasong Callos': [15.00053, 121.00035],
  'Pasong Intsik': [15.01094, 120.96884],
  Pinacpinacan: [14.99773, 120.9133],
  Poblacion: [14.95532, 120.96388],
  Pulo: [14.96192, 121.01451],
  'Pulong Bayabas': [15.0122, 120.90463],
  Salapongan: [15.01957, 120.96386],
  Sampaloc: [14.98183, 120.92646],
  'San Agustin': [15.03042, 120.92718],
  'San Roque': [15.0088, 120.93264],
  Talacsan: [14.96003, 120.97918],
  Tambubong: [14.96867, 120.92642],
  Tukod: [14.99451, 121.04935],
  Ulingao: [14.97155, 120.9131],
  'Sapang Pahalang': [14.99746, 121.0388],
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
<<<<<<< HEAD
      lat: baseLat + ((i % 5) - 2) * 0.0015,
      lng: baseLng + (((i * 3) % 5) - 2) * 0.0015,
=======
      lat: 14.91 + (i % 8) * 0.015,
      lng: 121.06 + ((i * 3) % 8) * 0.012,
>>>>>>> 9845aeb (Your descriptive commit message here)
    });
  }
  return households;
}

const centers: EvacuationCenter[] = [
<<<<<<< HEAD
  { id: 1, name: 'Poblacion Elementary School', barangay: 'Poblacion', address: 'Brgy Hall Rd', capacity: 500, current_occupants: 210, facilities: ['kitchen', 'water', 'power', 'bathrooms'], contact: '09171234001', lat: 14.956, lng: 120.9652, status: 'active' },
  { id: 2, name: 'San Roque Covered Court', barangay: 'San Roque', address: 'Mabini St', capacity: 300, current_occupants: 120, facilities: ['water', 'power'], contact: '09171234002', lat: 15.0095, lng: 120.9334, status: 'active' },
  { id: 3, name: 'Maronquillo High School', barangay: 'Maronquillo', address: 'DRT Highway', capacity: 450, current_occupants: 305, facilities: ['kitchen', 'water', 'power', 'bathrooms', 'clinic'], contact: '09171234003', lat: 14.9681, lng: 121.0019, status: 'active' },
  { id: 4, name: 'BMA-Balagtas Gymnasium', barangay: 'BMA-Balagtas', address: 'Rizal Ave', capacity: 200, current_occupants: 15, facilities: ['water', 'power'], contact: '09171234004', lat: 14.9687, lng: 120.9676, status: 'standby' },
  { id: 5, name: 'Pantubig Barangay Hall', barangay: 'Pantubig', address: 'Pantubig Road', capacity: 150, current_occupants: 88, facilities: ['kitchen', 'water'], contact: '09171234005', lat: 14.9655, lng: 120.953, status: 'active' },
  { id: 6, name: 'Sampaloc Community Center', barangay: 'Sampaloc', address: 'Sampaloc Road', capacity: 400, current_occupants: 240, facilities: ['kitchen', 'water', 'power', 'bathrooms'], contact: '09171234006', lat: 14.9818, lng: 120.9265, status: 'active' },
=======
<<<<<<< HEAD
  { id: 1, name: 'Poblacion Elementary School', barangay: 'Poblacion', address: 'Brgy Hall Rd', capacity: 500, current_occupants: 210, facilities: ['kitchen', 'water', 'power', 'bathrooms'], contact: '09171234001', lat: 14.9578, lng: 120.9642, status: 'active' },
  { id: 2, name: 'San Roque Covered Court', barangay: 'San Roque', address: 'Mabini St', capacity: 300, current_occupants: 120, facilities: ['water', 'power'], contact: '09171234002', lat: 14.9692, lng: 120.9788, status: 'active' },
  { id: 3, name: 'Maronquillo High School', barangay: 'Maronquillo', address: 'DRT Highway', capacity: 450, current_occupants: 305, facilities: ['kitchen', 'water', 'power', 'bathrooms', 'clinic'], contact: '09171234003', lat: 14.9903, lng: 120.9625, status: 'active' },
  { id: 4, name: 'BMA-Balagtas Gymnasium', barangay: 'BMA-Balagtas', address: 'Rizal Ave', capacity: 200, current_occupants: 15, facilities: ['water', 'power'], contact: '09171234004', lat: 14.9565, lng: 120.9524, status: 'standby' },
  { id: 5, name: 'Pantubig Barangay Hall', barangay: 'Pantubig', address: 'Pantubig Road', capacity: 150, current_occupants: 88, facilities: ['kitchen', 'water'], contact: '09171234005', lat: 14.968, lng: 120.935, status: 'active' },
  { id: 6, name: 'Sampaloc Community Center', barangay: 'Sampaloc', address: 'Sampaloc Road', capacity: 400, current_occupants: 240, facilities: ['kitchen', 'water', 'power', 'bathrooms'], contact: '09171234006', lat: 14.964, lng: 120.959, status: 'active' },
=======
  { id: 1, name: 'Poblacion Elementary School', barangay: 'Poblacion', address: 'Brgy Hall Rd', capacity: 500, current_occupants: 210, facilities: ['kitchen', 'water', 'power', 'bathrooms'], contact: '09171234001', lat: 14.95, lng: 121.09, status: 'active' },
  { id: 2, name: 'San Roque Covered Court', barangay: 'San Roque', address: 'Mabini St', capacity: 300, current_occupants: 120, facilities: ['water', 'power'], contact: '09171234002', lat: 14.94, lng: 121.08, status: 'active' },
  { id: 3, name: 'San Juan High School', barangay: 'San Juan', address: 'National Rd', capacity: 450, current_occupants: 305, facilities: ['kitchen', 'water', 'power', 'bathrooms', 'clinic'], contact: '09171234003', lat: 14.97, lng: 121.12, status: 'active' },
  { id: 4, name: 'Santo Niño Gymnasium', barangay: 'Santo Niño', address: 'Rizal Ave', capacity: 200, current_occupants: 15, facilities: ['water', 'power'], contact: '09171234004', lat: 14.93, lng: 121.06, status: 'standby' },
  { id: 5, name: 'Bagong Silang Barangay Hall', barangay: 'Bagong Silang', address: 'Diversity Rd', capacity: 150, current_occupants: 88, facilities: ['kitchen', 'water'], contact: '09171234005', lat: 14.98, lng: 121.13, status: 'active' },
  { id: 6, name: 'Malanday Community Center', barangay: 'Malanday', address: 'Seaside Rd', capacity: 400, current_occupants: 240, facilities: ['kitchen', 'water', 'power', 'bathrooms'], contact: '09171234006', lat: 14.91, lng: 121.07, status: 'active' },
>>>>>>> 9845aeb (Your descriptive commit message here)
>>>>>>> a941357 (Your descriptive commit message here)
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
<<<<<<< HEAD
  { id: 1, title: 'Flash flood due to monsoon rains', type: 'flood', barangay: 'Mabalas-balas', severity: 'high', status: 'responding', description: 'River overflow submerged low-lying streets. Residents moved to Sampaloc Community Center.', reported_at: '2026-09-15T06:15:00Z', updated_at: '2026-09-16T08:00:00Z', lat: 15.0253, lng: 120.9427, affected_households: 45, reported_by: 'MDRRMO' },
  { id: 2, title: 'Fire broke out in residential area', type: 'fire', barangay: 'Poblacion', severity: 'critical', status: 'assessing', description: 'Fire affected 8 houses near the public market. Fire trucks on scene.', reported_at: '2026-09-16T11:40:00Z', updated_at: '2026-09-16T12:10:00Z', lat: 14.9553, lng: 120.9639, affected_households: 8, reported_by: 'BFP' },
  { id: 3, title: 'Landslide along mountain road', type: 'landslide', barangay: 'Coral na Bato', severity: 'moderate', status: 'assessing', description: 'Debris blocked access road; no casualties reported yet.', reported_at: '2026-09-14T14:05:00Z', updated_at: '2026-09-15T07:30:00Z', lat: 14.9942, lng: 120.9792, affected_households: 3, reported_by: 'Barangay Coral na Bato' },
  { id: 4, title: 'Storm surge warning issued', type: 'typhoon', barangay: 'Ulingao', severity: 'low', status: 'reported', description: 'Pre-emptive evacuation being organized ahead of projected storm surge.', reported_at: '2026-09-16T02:00:00Z', updated_at: '2026-09-16T02:00:00Z', lat: 14.9716, lng: 120.9131, affected_households: 20, reported_by: 'PAGASA' },
  { id: 5, title: 'River overflow in low-lying areas', type: 'flood', barangay: 'San Roque', severity: 'high', status: 'responding', description: 'Water level at knee-to-waist height along Mabini St.', reported_at: '2026-09-15T05:45:00Z', updated_at: '2026-09-16T07:00:00Z', lat: 15.0088, lng: 120.9326, affected_households: 32, reported_by: 'MDRRMO' },
=======
<<<<<<< HEAD
  { id: 1, title: 'Flash flood due to monsoon rains', type: 'flood', barangay: 'Mabalas-balas', severity: 'high', status: 'responding', description: 'River overflow submerged low-lying streets. Residents moved to Sampaloc Community Center.', reported_at: '2026-09-15T06:15:00Z', updated_at: '2026-09-16T08:00:00Z', lat: 14.9085, lng: 120.97, affected_households: 45, reported_by: 'MDRRMO' },
  { id: 2, title: 'Fire broke out in residential area', type: 'fire', barangay: 'Poblacion', severity: 'critical', status: 'assessing', description: 'Fire affected 8 houses near the public market. Fire trucks on scene.', reported_at: '2026-09-16T11:40:00Z', updated_at: '2026-09-16T12:10:00Z', lat: 14.9565, lng: 120.966, affected_households: 8, reported_by: 'BFP' },
  { id: 3, title: 'Landslide along mountain road', type: 'landslide', barangay: 'Coral na Bato', severity: 'moderate', status: 'assessing', description: 'Debris blocked access road; no casualties reported yet.', reported_at: '2026-09-14T14:05:00Z', updated_at: '2026-09-15T07:30:00Z', lat: 14.925, lng: 120.992, affected_households: 3, reported_by: 'Barangay Coral na Bato' },
  { id: 4, title: 'Storm surge warning issued', type: 'typhoon', barangay: 'Ulingao', severity: 'low', status: 'reported', description: 'Pre-emptive evacuation being organized ahead of projected storm surge.', reported_at: '2026-09-16T02:00:00Z', updated_at: '2026-09-16T02:00:00Z', lat: 14.988, lng: 120.972, affected_households: 20, reported_by: 'PAGASA' },
  { id: 5, title: 'River overflow in low-lying areas', type: 'flood', barangay: 'San Roque', severity: 'high', status: 'responding', description: 'Water level at knee-to-waist height along Mabini St.', reported_at: '2026-09-15T05:45:00Z', updated_at: '2026-09-16T07:00:00Z', lat: 14.9698, lng: 120.9782, affected_households: 32, reported_by: 'MDRRMO' },
=======
  { id: 1, title: 'Flash flood due to monsoon rains', type: 'flood', barangay: 'Malanday', severity: 'high', status: 'responding', description: 'River overflow submerged low-lying streets. Residents moved to Malanday Community Center.', reported_at: '2026-09-15T06:15:00Z', updated_at: '2026-09-16T08:00:00Z', lat: 14.91, lng: 121.07, affected_households: 45, reported_by: 'MDRRMO' },
  { id: 2, title: 'Fire broke out in residential area', type: 'fire', barangay: 'Poblacion', severity: 'critical', status: 'assessing', description: 'Fire affected 8 houses near the public market. Fire trucks on scene.', reported_at: '2026-09-16T11:40:00Z', updated_at: '2026-09-16T12:10:00Z', lat: 14.95, lng: 121.09, affected_households: 8, reported_by: 'BFP' },
  { id: 3, title: 'Landslide along mountain road', type: 'landslide', barangay: 'Kalayaan', severity: 'moderate', status: 'assessing', description: 'Debris blocked access road; no casualties reported yet.', reported_at: '2026-09-14T14:05:00Z', updated_at: '2026-09-15T07:30:00Z', lat: 14.98, lng: 121.15, affected_households: 3, reported_by: 'Barangay Tanod' },
  { id: 4, title: 'Storm surge warning issued', type: 'typhoon', barangay: 'San Juan', severity: 'low', status: 'reported', description: 'Pre-emptive evacuation being organized ahead of projected storm surge.', reported_at: '2026-09-16T02:00:00Z', updated_at: '2026-09-16T02:00:00Z', lat: 14.96, lng: 121.11, affected_households: 20, reported_by: 'PAGASA' },
  { id: 5, title: 'River overflow in low-lying areas', type: 'flood', barangay: 'San Roque', severity: 'high', status: 'responding', description: 'Water level at knee-to-waist height along Mabini St.', reported_at: '2026-09-15T05:45:00Z', updated_at: '2026-09-16T07:00:00Z', lat: 14.94, lng: 121.08, affected_households: 32, reported_by: 'MDRRMO' },
>>>>>>> 9845aeb (Your descriptive commit message here)
>>>>>>> a941357 (Your descriptive commit message here)
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