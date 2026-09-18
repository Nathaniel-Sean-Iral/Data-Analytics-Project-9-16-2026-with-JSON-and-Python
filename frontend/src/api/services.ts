import { ApiError, http } from './client';
import * as mock from './mock';
import type {
  AllocationResult,
  AuthResponse,
  CenterLoad,
  DashboardStats,
  EvacuationCenter,
  Household,
  Incident,
  IncidentStatus,
  LoginRequest,
  Paginated,
  Resource,
  ResourceSummary,
  ScenarioReport,
  User,
} from './types';

/**
 * True when the API is not yet able to serve a request: no network access, a
 * proxy/gateway failure (502/503/504), or the backend responded with a status
 * meaning "endpoint not implemented" (404 / 405 / 501). In those cases we fall
 * back to bundled sample data so the UI stays fully usable during development.
 */
function backendUnavailable(err: unknown): boolean {
  return (
    err instanceof ApiError &&
    (err.status === 0 || err.status === 404 || err.status === 405 || err.status === 501 || err.status === 502 || err.status === 503 || err.status === 504)
  );
}

async function withMock<T>(request: Promise<T>, fallback: T | (() => T)): Promise<T> {
  try {
    return await request;
  } catch (err) {
    if (!backendUnavailable(err)) throw err;
    return typeof fallback === 'function' ? (fallback as () => T)() : fallback;
  }
}

/* ------------------------------ Auth ------------------------------ */

export async function login(req: LoginRequest): Promise<AuthResponse> {
  try {
    return await http.post<AuthResponse>('/auth/login', req);
  } catch (err) {
    if (backendUnavailable(err)) {
      if (req.username === 'admin' || req.username === 'responder' || req.username === 'viewer') {
        const role = req.username as User['role'];
        const user: User = {
          id: 1,
          username: req.username,
          full_name: role === 'admin' ? 'Admin User' : role === 'responder' ? 'Responder User' : 'Viewer User',
          role,
        };
        return {
          access_token: `mock-token-${role}`,
          token_type: 'bearer',
          user,
        };
      }
      throw new ApiError(401, 'Invalid credentials — try admin / responder / viewer (demo accounts).');
    }
    throw err;
  }
}

/* --------------------------- Households --------------------------- */

export async function fetchHouseholds(params = {}): Promise<Paginated<Household>> {
  return withMock(http.get<Paginated<Household>>('/households', params), () => {
    const items = mock.mockHouseholds();
    return { items, total: items.length, page: 1, page_size: items.length };
  });
}

export async function fetchHousehold(id: number): Promise<Household> {
  return withMock(http.get<Household>(`/households/${id}`), () => {
    const item = mock.mockHousehold(id);
    if (item) return item;
    throw new Error('Household not found');
  });
}

export async function createHousehold(data: Omit<Household, 'id'>): Promise<Household> {
  return withMock(http.post<Household>('/households', data), () => ({ ...data, id: Date.now() }));
}

export async function updateHousehold(id: number, data: Partial<Household>): Promise<Household> {
  return withMock(http.put<Household>(`/households/${id}`, data), () => ({ ...(mock.mockHousehold(id) as Household), ...data, id }));
}

export async function deleteHousehold(id: number): Promise<void> {
  await withMock(http.delete<unknown>(`/households/${id}`), () => undefined);
}

/* ---------------------------- Centers ----------------------------- */

export async function fetchCenters(): Promise<EvacuationCenter[]> {
  return withMock(http.get<EvacuationCenter[]>('/centers'), () => mock.mockCenters());
}

export async function fetchCenter(id: number): Promise<EvacuationCenter> {
  return withMock(http.get<EvacuationCenter>(`/centers/${id}`), () => {
    const item = mock.mockCenters().find((c) => c.id === id);
    if (item) return item;
    throw new Error('Center not found');
  });
}

export async function createCenter(data: Omit<EvacuationCenter, 'id'>): Promise<EvacuationCenter> {
  return withMock(http.post<EvacuationCenter>('/centers', data), () => ({ ...data, id: Date.now() }));
}

export async function updateCenter(id: number, data: Partial<EvacuationCenter>): Promise<EvacuationCenter> {
  return withMock(http.put<EvacuationCenter>(`/centers/${id}`, data), () => ({ ...(mock.mockCenters().find((c) => c.id === id) as EvacuationCenter), ...data, id }));
}

/* ---------------------------- Resources --------------------------- */

export async function fetchResources(): Promise<Resource[]> {
  return withMock(http.get<Resource[]>('/resources'), () => mock.mockResources());
}

export async function fetchResourceSummaries(): Promise<ResourceSummary[]> {
  return withMock(http.get<ResourceSummary[]>('/resources/summary'), () => mock.mockResourceSummaries());
}

export async function adjustStock(body: { resource_id: number; delta: number; reason?: string }): Promise<Resource> {
  return withMock(http.post<Resource>('/resources/adjust', body), () => {
    const item = mock.mockResources().find((r) => r.id === body.resource_id);
    if (!item) throw new Error('Resource not found');
    return { ...item, quantity_on_hand: Math.max(0, item.quantity_on_hand + body.delta) };
  });
}

export async function updateResourceThreshold(id: number, threshold: number): Promise<Resource> {
  return withMock(http.patch<Resource>(`/resources/${id}`, { threshold }), () => {
    const item = mock.mockResources().find((r) => r.id === id);
    if (!item) throw new Error('Resource not found');
    return { ...item, threshold };
  });
}

/* ---------------------------- Incidents --------------------------- */

export async function fetchIncidents(): Promise<Incident[]> {
  return withMock(http.get<Incident[]>('/incidents'), () => mock.mockIncidents());
}

export async function fetchIncident(id: number): Promise<Incident> {
  return withMock(http.get<Incident>(`/incidents/${id}`), () => {
    const item = mock.mockIncident(id);
    if (item) return item;
    throw new Error('Incident not found');
  });
}

export async function createIncident(data: Omit<Incident, 'id' | 'reported_at' | 'updated_at' | 'status'>): Promise<Incident> {
  return withMock(http.post<Incident>('/incidents', data), () => ({
    ...data,
    id: Date.now(),
    status: 'reported',
    reported_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }));
}

export async function updateIncidentStatus(id: number, status: IncidentStatus): Promise<Incident> {
  return withMock(http.patch<Incident>(`/incidents/${id}`, { status }), () => {
    const item = mock.mockIncident(id);
    if (!item) throw new Error('Incident not found');
    return { ...item, status, updated_at: new Date().toISOString() };
  });
}

/* --------------------------- Allocation --------------------------- */

export async function runAllocation(barangay?: string): Promise<AllocationResult> {
  return withMock(http.post<AllocationResult>('/evacuations/allocate', { barangay }), () => mock.mockAllocation(barangay));
}

export async function fetchCenterLoads(): Promise<CenterLoad[]> {
  return withMock(http.get<CenterLoad[]>('/evacuations/center-loads'), () => mock.mockAllocation().center_loads);
}

/* ----------------------------- Simulator -------------------------- */

export async function runScenario(scenario: { barangay: string; affected_households: number }): Promise<ScenarioReport> {
  return withMock(
    http.post<ScenarioReport>('/simulator/run', scenario),
    () => mockScenario(scenario),
  );
}

function mockScenario(scenario: { barangay: string; affected_households: number }): ScenarioReport {
  const allocation = mock.mockAllocation(scenario.barangay);
  const needs: ScenarioReport['resource_needs'] = mock.mockResources().map((r) => {
    const perPerson = r.type === 'rice' ? 0.1 : r.type === 'water' ? 3 : r.name.startsWith('Canned') ? 0.5 : 0.25;
    const required = Math.ceil(scenario.affected_households * 4 * perPerson);
    const deficit = Math.max(0, required - r.quantity_on_hand);
    return {
      resource_id: r.id,
      name: r.name,
      current: r.quantity_on_hand,
      required,
      deficit,
      unit: r.unit,
      status: deficit === 0 ? 'adequate' : deficit > required * 0.5 ? 'critical' : 'shortage',
    };
  });
  return { scenario: { ...scenario, title: `${scenario.barangay} affected (${scenario.affected_households} households evacuees)` }, allocation, resource_needs: needs };
}

/* ------------------------------ Stats ----------------------------- */

export async function fetchDashboardStats(): Promise<DashboardStats> {
  return withMock(http.get<DashboardStats>('/dashboard/stats'), () => {
    const households = mock.mockHouseholds();
    const incidents = mock.mockIncidents();
    const centers = mock.mockCenters();
    const resources = mock.mockResources();
    const vulnerable = households.reduce((sum, h) => sum + h.children_count + h.elderly_count + h.pwd_count, 0);
    const activeIncidents = incidents.filter((i) => i.status !== 'resolved');
    const availableCapacity = centers.reduce(
      (sum, c) => sum + Math.max(0, c.capacity - c.current_occupants),
      0,
    );
    return {
      households: households.length,
      vulnerable_members: vulnerable,
      active_incidents: activeIncidents.length,
      critical_incidents: activeIncidents.filter((i) => i.severity === 'critical').length,
      centers: centers.length,
      available_capacity: availableCapacity,
      low_stock_resources: resources.filter((r) => r.quantity_on_hand < r.threshold).length,
      assigned_households: mock.mockAllocation().assigned_households,
    };
  });
}