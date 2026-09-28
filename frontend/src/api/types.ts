export type Role = 'admin' | 'responder' | 'viewer';

export interface User {
  id: number;
  username: string;
  full_name: string;
  role: Role;
  email?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Household {
  id: number;
  household_no: string;
  head_name: string;
  address: string;
  barangay: string;
  size: number;
  children_count: number;
  elderly_count: number;
  pwd_count: number;
  contact: string;
  lat: number;
  lng: number;
  notes?: string;
}

export type IncidentType = 'flood' | 'fire' | 'earthquake' | 'landslide' | 'typhoon' | 'other';
export type IncidentSeverity = 'low' | 'moderate' | 'high' | 'critical';
export type IncidentStatus = 'reported' | 'assessing' | 'responding' | 'resolved';

export interface Incident {
  id: number;
  title: string;
  type: IncidentType;
  barangay: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  description?: string;
  reported_at: string;
  updated_at: string;
  lat?: number;
  lng?: number;
  affected_households?: number;
  reported_by?: string;
}

export type CenterStatus = 'active' | 'standby' | 'closed';

export interface EvacuationCenter {
  id: number;
  name: string;
  barangay: string;
  address: string;
  capacity: number;
  current_occupants: number;
  facilities: string[];
  contact?: string;
  lat: number;
  lng: number;
  status: CenterStatus;
}

export type ResourceType = 'rice' | 'water' | 'medicine' | 'blankets' | 'hygiene' | 'canned_goods' | 'clothing' | 'mats' | 'tents' | 'other';

export interface Resource {
  id: number;
  name: string;
  type: ResourceType;
  unit: string;
  quantity_on_hand: number;
  threshold: number;
  expiry?: string;
  stored_in?: string;
  updated_at: string;
}

export interface ResourceStockAdjustment {
  resource_id: number;
  delta: number;
  reason?: string;
}

export interface EvacuationAssignment {
  /** Persisted `evacuation_assignments` row id; null for simulated (dry-run) assignments. */
  id: number | null;
  household_id: number;
  household_no: string;
  household_head: string;
  barangay: string;
  center_id: number;
  center_name: string;
  center_load_percent: number;
  assigned_at: string;
}

export interface AllocationResult {
  request_id: string;
  generated_at: string;
  total_households: number;
  assigned_households: number;
  overflow_households: number;
  assignments: EvacuationAssignment[];
  center_loads: CenterLoad[];
  overflow: OverflowEntry[];
  coverage_gaps: string[];
}

export interface CenterLoad {
  center_id: number;
  center_name: string;
  barangay: string;
  capacity: number;
  occupants: number;
  load_percent: number;
  status: 'ok' | 'near_capacity' | 'full' | 'overflow';
}

export interface OverflowEntry {
  household_id: number;
  household_no: string;
  head_name: string;
  barangay: string;
  reason: string;
}

/** Simulation output from the "what-if" scenario engine. */
export interface ScenarioReport {
  scenario: { title: string; barangay: string; affected_households: number; estimated_evacuees: number };
  allocation: AllocationResult;
  resource_needs: ResourceNeed[];
}

export interface ResourceNeed {
  resource_id: number;
  name: string;
  current: number;
  required: number;
  deficit: number;
  unit: string;
  status: 'adequate' | 'shortage' | 'critical';
}

export interface ResourceSummary {
  type: ResourceType;
  label: string;
  total_on_hand: number;
  total_required: number;
  gap: number;
  low_stock_count: number;
}

export interface DashboardStats {
  households: number;
  vulnerable_members: number;
  active_incidents: number;
  critical_incidents: number;
  centers: number;
  available_capacity: number;
  low_stock_resources: number;
  assigned_households: number;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}