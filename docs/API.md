# API Reference

Base URL (dev): `http://localhost:8000` · all routes under `/api`. Live interactive spec at `/docs` (OpenAPI).

**Auth:** endpoints require an `Authorization: Bearer <token>` header unless noted. Get a token via `POST /api/auth/login`.

## Roles

| Role | Rank | Capabilities |
| --- | --- | --- |
| `admin` | 3 | everything incl. all mutations |
| `responder` | 2 | reads + incidents/allocation/simulator + resource stock |
| `viewer` | 1 | reads only |

A caller is permitted when their rank ≥ the least-privileged role allowed for the endpoint.

---

## Auth

### `POST /api/auth/login` — no token required
Body: `{ "username": "admin", "password": "admin" }`

200 → `{ "access_token": "<jwt>", "token_type": "bearer", "user": { "id", "username", "full_name", "email", "role" } }`
401 on bad/unknown credentials, 403 if account disabled.

### `GET /api/auth/me`
200 → current user object. 401 if token missing/invalid.

---

## Households

`GET /api/households` — query params: `page` (1), `page_size` (10, ≤100), `q` (searches no/head/address/barangay), `sort` (`household_no|head_name|barangay|size`), `order` (`asc|desc`), `barangay`.

200 → `{ "items": [Household], "total": number, "page": number, "page_size": number }`

`POST /api/households` *(admin)* → 201. 409 if `household_no` taken.
`GET /api/households/{id}` · `PUT /api/households/{id}` *(admin)* · `DELETE /api/households/{id}` *(admin, 204)*.

Household shape: `household_no, head_name, address, barangay, size, children_count, elderly_count, pwd_count, contact?, lat, lng, notes?`.

---

## Centers

`GET /api/centers` — param `status` (`active|standby|closed`). → `[EvacuationCenter]`
`GET /api/centers/{id}` · `POST /api/centers` *(admin, 201)* · `PUT /api/centers/{id}` *(admin)* · `DELETE /api/centers/{id}` *(admin, 204)*.

Center shape: `name, barangay, address?, capacity, current_occupants, facilities: string[], contact?, lat, lng, status`.

---

## Resources

`GET /api/resources` → `[Resource]`
`GET /api/resources/summary` → per-type aggregates: `{ type, label, total_on_hand, total_required, gap, low_stock_count }`
`GET /api/resources/{id}` · `POST /api/resources` *(admin, 201)*
`PATCH /api/resources/{id}` *(admin)* — partial update incl. `threshold`.
`POST /api/resources/{id}/threshold` *(admin)* — `{ threshold: int }`.
`POST /api/resources/adjust` *(admin)* — `{ resource_id, delta, reason? }`; adds `delta` to `quantity_on_hand`, writes a `stock_transactions` audit row; **400 if the result would be negative**.

Resource shape: `name, type, unit, quantity_on_hand, threshold, expiry?, stored_in?, updated_at`.

---

## Incidents

`GET /api/incidents` — params `status`, `severity`, `type`, `barangay`. Sorted by `reported_at` desc. → `[Incident]`
`GET /api/incidents/{id}` · `POST /api/incidents` *(responder+, 201; status forced to `reported`)*
`PATCH /api/incidents/{id}` *(responder+)* — partial update incl. `status`
`DELETE /api/incidents/{id}` *(admin, 204)*

**Status workflow** enforced: `reported → assessing → responding → resolved` (or back to `assessing`). Any other jump → 400.

Incident shape: `title, type, barangay, severity, status, description?, lat?, lng?, affected_households?, reported_by?, reported_at, updated_at`.

---

## Evacuations

`POST /api/evacuations/allocate` *(responder+)* — body `{ "barangay"?: string }` (omit for all).

200 → AllocationResult:
```
{
  "request_id": "ALLOC-260923100102",
  "generated_at": ISO-8601,
  "total_households": int, "assigned_households": int, "overflow_households": int,
  "assignments": [{ id, household_id, household_no, household_head, barangay,
                    center_id, center_name, center_load_percent, assigned_at }],
  "center_loads":    [{ center_id, center_name, barangay, capacity, occupants,
                        load_percent, status: ok|near_capacity|full|overflow }],
  "overflow":        [{ household_id, household_no, head_name, barangay, reason }],
  "coverage_gaps":   ["<barangay> has no evacuation center — pre-position transport assets."]
}
```
Assignments persist to `evacuation_assignments`. Rows are kept for audit, so
re-running the allocator appends a new plan rather than replacing the old one —
`GET /api/dashboard/stats` reports `assigned_households` as the number of
**distinct** households, not the number of rows.

`GET /api/evacuations/center-loads` → current occupancy snapshot (`[CenterLoad]` above, no allocation run).

---

## Simulator

`POST /api/simulator/run` *(responder+)* — body `{ "barangay": "Poblacion", "affected_households": 100 }`.
`barangay` is required; `affected_households` must be ≥ 1.

200 → ScenarioReport:
```
{
  "scenario": { "title", "barangay", "affected_households", "estimated_evacuees" },
  "allocation": AllocationResult,          // dry run, request_id is prefixed "SIM-"
  "resource_needs": [{
     "resource_id", "name", "current", "required", "deficit", "unit",
     "status": adequate|shortage|critical    // critical = deficit > 50% of required
  }]
}
```

The scenario is a **dry run**: nothing is written to `evacuation_assignments`, so
assignment `id` values in the nested `allocation` are `null` (use
`POST /api/evacuations/allocate` when you want a persisted plan).

Both halves of the report describe the same evacuee count. The nested allocation
models exactly `affected_households` households in `barangay` — the registry's
real rows first, then synthetic households anchored at the barangay centroid —
so the projected `center_loads` and `overflow` genuinely reflect the scenario
input rather than however many rows happen to be in the database.

Evacuees modeled as `affected_households × AVG_PERSONS_PER_HOUSEHOLD` (default 4);
water and rice rates are overridable via `DAYS_WATER_PER_PERSON` /
`RICE_SACKS_PER_PERSON`, other rates come from `PER_PERSON_RATES` in
`app/services/common.py`.

---

## Dashboard & Meta

`GET /api/dashboard/stats` → `{ households, vulnerable_members, active_incidents, critical_incidents, centers, available_capacity, low_stock_resources, assigned_households }`
`GET /api/meta/barangays` → `["Poblacion", "San Roque", ...]`

---

## Errors

All non-2xx responses use `{ "detail": "explanation" }` (FastAPI default).

| Code | Meaning |
| --- | --- |
| 400 | validation/business rule (bad status jump, negative stock) |
| 401 | missing/invalid/expired token |
| 403 | authenticated but role too low |
| 404 | resource not found |
| 409 | unique conflict (e.g. duplicate `household_no`) |