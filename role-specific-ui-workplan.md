# Workplan — Role-Specific UI (viewer / responder)

**Audience:** a developer or coding agent with no prior context on this repository.
**Scope:** frontend only. 6 files. No backend, no tests, no route changes.

---

## 1. Project context

A disaster-preparedness operations system for the Municipality of San Rafael, Bulacan.

| | |
|---|---|
| Repo root | `C:\Portfolio for Projects\Data-Analytics-Project-9-16-2026-with-JSON-and-Python` |
| Backend | FastAPI + SQLAlchemy + SQLite, `backend/` |
| Frontend | React 18 + TypeScript + Vite + Tailwind + React Router v6, `frontend/` |
| Auth | JWT. Roles stored in the token and exposed by an auth context hook |
| Branch | `Front-end-initial-design-copy` |

Key frontend locations:

| Path | Purpose |
|---|---|
| `frontend/src/App.tsx` | Routes, `Protected` wrapper, `RoleGate` wrapper |
| `frontend/src/auth/AuthContext.tsx` | `useAuth()` → `{ user, hasRole }` |
| `frontend/src/components/layout/AppShell.tsx` | Sidebar, nav items, role badge |
| `frontend/src/components/ui/card.tsx` | `PageHeader`, `StatCard`, `Card`, `CardHeader`, `ProgressBar` |
| `frontend/src/components/ui/badge.tsx` | `Badge` (prop `tone`) |
| `frontend/src/pages/*.tsx` | One file per route |

---

## 2. Objective

Today all three roles land on the same admin-oriented dashboard, and the frontend's
edit-button permissions contradict the tested backend contract. Deliver:

1. **Three distinct dashboards** — one per role, each answering a different question.
2. **Consistent page-level permissions** — aligned to the backend contract.
3. **A visible read-only affordance** for viewers, so hidden buttons read as
   intentional rather than as a bug.

---

## 3. Hard constraints (violating any of these fails the task)

1. **Do not modify any file under `backend/`.** No exceptions.
2. **Do not edit any test.** `backend/tests/` must stay untouched.
3. **Do not modify `App.tsx`** — no new routes, no `RoleGate` changes.
4. **Do not modify `AppShell.tsx`** — the nav set stays exactly as it is.
5. **The admin dashboard must render identically to today** — same sections in the
   same order producing the same DOM. The *source* may be reorganised into section
   components (section 6.5 requires that), but no visual or behavioural change is
   permitted for admins. Verify with `git stash` + reload before/after.
6. **Reuse the existing design system only.** Do not add component libraries,
   CSS frameworks, or new dependency packages.
7. **Do not add dependencies.** `package.json` must not change.
8. Use `hasRole` from `useAuth()` for all gating. Never read `user.role` directly.

**Success gate:** `pytest` reports `113 passed` with zero test files modified,
`tsc --noEmit` exits 0, `npm run build` succeeds.

---

## 4. Permission model — source of truth

The backend contract is explicitly tested in
`backend/tests/test_api_contract.py`, whose docstring says:

> "every core endpoint must answer with the expected HTTP status for each role,
> so a bad wiring change fails loudly instead of **silently breaking the frontend**"

Relevant rows of its `ROUTE_MATRIX`:

```python
("POST", "/api/households",          {"admin", "responder"}),
("POST", "/api/centers",             {"admin", "responder"}),
("POST", "/api/resources",           {"admin", "responder"}),
("POST", "/api/households/import",   {"admin", "responder"}),
("POST", "/api/households/import/geojson", {"admin", "responder"}),
("POST", "/api/resources/adjust",    {"admin", "responder"}),
("POST", "/api/incidents",           {"admin", "responder"}),
("POST", "/api/map/zones",           {"admin", "responder"}),
```

All `DELETE` endpoints are `require_roles("admin")` only.

**Conclusion: the backend is correct and tested. The frontend is the outlier.**
We align the UI to the contract, never the reverse.

### Target matrix

| Capability | viewer | responder | admin |
|---|:--:|:--:|:--:|
| Read every page | ✓ | ✓ | ✓ |
| Create / edit households, centers, resources | ✗ | ✓ | ✓ |
| CSV / GeoJSON household import | ✗ | ✓ | ✓ |
| Adjust resource stock, edit thresholds | ✗ | ✓ | ✓ |
| Report / update incidents, save map zones | ✗ | ✓ | ✓ |
| Run allocation, run simulator | ✗ | ✓ | ✓ |
| Delete anything | ✗ | ✗ | ✓ |
| Create users | ✗ | ✗ | ✓ |

In code terms: **read → write → destroy.**

### `hasRole` semantics

`AuthContext.tsx` defines `hasRole` as rank-based:

```ts
const ROLE_RANK: Record<Role, number> = { viewer: 1, responder: 2, admin: 3 };
const hasRole = (...roles: Role[]) => Boolean(user && ROLE_RANK[user.role] >= ROLE_RANK[roles[0]]);
```

So `hasRole('responder')` is true for **both** responder and admin.

The public type declares `hasRole: (...roles: Role[]) => boolean`, but the
implementation at line 34 accepts only `(role: Role)` and ignores any extra
arguments. Every existing call site passes exactly one role — do the same.
Never write `hasRole('admin', 'responder')`; it will not do what it looks like.

---

## 5. Design decisions (read before implementing)

**D1 — Align the UI to the backend contract, not the reverse.**
Changing `require_roles(...)` would rewrite a documented, tested contract and
force edits to ~7 tests. Changing three frontend boolean expressions costs
nothing and satisfies constraint #2.

**D2 — Viewers keep the Households nav item.**
`test_api_contract.py` line 13 explicitly allows `GET /api/households` for viewer.
Removing the nav item would contradict the contract we are aligning to, and
household density and vulnerability counts are exactly what an observing official
needs. The page simply has no write affordances for them.

**D3 — One dashboard component, composed by role. Do not create three files.**
All three dashboards share identical widgets (stat cards, center loads, resource
data, incident list). Three separate page components would drift — which is the
same bug class that produced the permission mismatch we are fixing now.
Extract small section components inside the single `DashboardPage.tsx` and
compose them per role.

**D4 — Each landing answers a different question.**

| Role | Page title | Question answered |
|---|---|---|
| viewer | `Status Overview` | *What is happening?* |
| responder | `Incident Response` | *What do I do?* |
| admin | `Operations Dashboard` (unchanged) | *How are we doing overall?* |

Differentiation is achieved by **section order, page title, and quick actions** —
not by inventing new data or new endpoints.

**D5 — Viewers get an explicit `View only` badge.**
Today missing buttons simply look like a rendering bug. A small badge makes the
restriction read as deliberate product design.

**D6 — Nav, routes, and role gates are frozen.** Differentiation happens on the
page, not in the sidebar.

---

## 6. Implementation

### 6.1 Permission split — `HouseholdsPage.tsx`

**Current** (near line 198):

```ts
const { hasRole } = useAuth();
const canEdit = hasRole('admin');
```

**Change to:**

```ts
const { hasRole } = useAuth();
const canEdit = hasRole('responder');
const canDelete = hasRole('admin');
const isViewer = !hasRole('responder');
```

Then update three places:

**a) Row actions column** (near line 341). Today a single `canEdit ?` block holds
both the pencil and the trash button, else `—`. Split it:

```tsx
render: (r) =>
  canEdit || canDelete ? (
    <div className="flex justify-end gap-1">
      {canEdit && (
        <Button variant="ghost" className="!px-2 !py-1.5"
          onClick={() => { setEditing(r); setModalOpen(true); }}
          aria-label={`Edit ${r.household_no}`}>
          <Pencil className="h-4 w-4" />
        </Button>
      )}
      {canDelete && (
        <Button variant="ghost" className="!px-2 !py-1.5 !text-danger-600 hover:!bg-danger-50"
          onClick={() => setDeleting(r)}
          aria-label={`Delete ${r.household_no}`}>
          <Trash2 className="h-4 w-4" />
        </Button>
      )}
    </div>
  ) : (
    <span className="text-xs text-slate-400">—</span>
  ),
```

Result: viewer sees `—`, responder sees pencil only, admin sees pencil + trash.

**b) `PageHeader` `actions`** (near line 376). Today `canEdit ? <>Import + Add</> : undefined`.
Change the false branch to the viewer badge:

```tsx
actions={
  isViewer ? (
    <Badge tone="slate">View only</Badge>
  ) : canEdit ? (
    <>
      {/* existing hidden file input + Import button + Add household button, unchanged */}
    </>
  ) : undefined
}
```

Import and Add become responder-visible, matching
`POST /api/households/import` in the contract.

**c)** `Badge` is already imported in `HouseholdsPage.tsx` (line 6) — do not add a
duplicate import. Verify it resolves `@/components/ui/badge`.

---

### 6.2 Permission change — `CentersPage.tsx`

**Current** (near line 176):

```ts
const canEdit = hasRole('admin');
```

**Change to:**

```ts
const canEdit = hasRole('responder');
const isViewer = !hasRole('responder');
```

Two sites:

- **`PageHeader` actions** (near line 214): `canEdit ? <Add center button> : undefined`
  → false branch becomes `<Badge tone="slate">View only</Badge>`.
- **Row edit pencil** (near line 308): `{canEdit && (<Button ...Pencil...>)}` — leave as is.

Note: this page has **no delete button** (the API has admin-only
`DELETE /api/centers`, but no UI exists). Do not add one — that is out of scope.
No `canDelete` is needed here.

`Badge` is already imported in `CentersPage.tsx` (line 17) — reuse it.

---

### 6.3 Permission change — `ResourcesPage.tsx`

**Current** (near line 40):

```ts
const canEdit = hasRole('admin');
```

**Change to:**

```ts
const canEdit = hasRole('responder');
const isViewer = !hasRole('responder');
```

Three sites:

- **Threshold pencil** (near line 118): `{canEdit && (` — leave as is.
- **Row `Adjust` button** (near line 160): `canEdit ? <Button>Adjust</Button> : <span>—</span>` — leave as is.
- **`PageHeader`** (near line 172): currently has **no `actions` prop at all**. Add one:

```tsx
<PageHeader
  title="Resources"
  description="Stock management for relief supplies. Low-stock items are highlighted for replenishment."
  icon={<Package className="h-5 w-5" />}
  actions={isViewer ? <Badge tone="slate">View only</Badge> : undefined}
/>
```

Note: this page has **no delete button and no "add resource" button** in the UI.
Do not add either — out of scope.

`Badge` is already imported at the top of this file (line 16) — reuse it.

---

### 6.4 Read-only badge — `IncidentsPage.tsx` and `IncidentDetailPage.tsx`

No permission changes here; the existing gating is already correct:

- `IncidentsPage.tsx` line 52: `const canCreate = hasRole('responder');`
- `IncidentDetailPage.tsx` line 45: `const canUpdate = hasRole('responder');`

**`IncidentsPage.tsx`** — `PageHeader` `actions` (near line 170) is
`canCreate ? <Report incident button> : undefined`. Change the false branch to
`<Badge tone="slate">View only</Badge>`.

**`IncidentDetailPage.tsx`** — this page has **no `PageHeader`**; it renders a raw
`<h1 className="text-xl font-bold text-slate-900">{inc.title}</h1>` around line 110.
Do not introduce a `PageHeader`. Place the badge inline next to that `<h1>` so it
sits in the existing header row:

```tsx
<div className="flex items-center gap-3">
  <h1 className="text-xl font-bold text-slate-900">{inc.title}</h1>
  {isViewer && <Badge tone="slate">View only</Badge>}
</div>
```

Keep everything else on the page, including the status stepper and the
`{canUpdate && (...)}` action bar, exactly as is.

Add `const isViewer = !hasRole('responder');` where needed.

---

### 6.5 Dashboard restructure — `DashboardPage.tsx`

This is the main deliverable. File is currently 221 lines, a single component
with four inline sections.

#### Step 1 — Extract section components (in-file, no new files)

Keep all existing imports. Add these small components above `DashboardPage`,
each taking only the data it needs:

| Component | Content (move existing JSX verbatim) |
|---|---|
| `StatCards({ s })` | The 4 `StatCard` grid (currently lines 67–92) |
| `ResourceChart({ summaries, loading })` | The resource availability `BarChart` card (lines 95–119) |
| `CenterLoads({ centerLoads })` | The center-load progress card (lines 121–141) |
| `IncidentList({ incidents, order })` | The active-incidents card (lines 145–182). `order: 'recent' \| 'severity'` controls sorting |
| `QuickSummary({ s, showActions })` | The quick-summary card (lines 184–217). `showActions` controls the allocation/simulator links — replace the internal `hasRole('responder')` check with this prop so the section stays pure |
| `QuickActions()` | **New.** Responder action bar (spec below) |
| `LowStockAlerts({ summaries })` | **New.** Low-stock list (spec below) |

Add sorting inside `IncidentList`:

```ts
const SEVERITY_ORDER: Record<IncidentSeverity, number> = {
  critical: 0, high: 1, moderate: 2, low: 3,
};
const sorted = order === 'severity'
  ? [...incidents].sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity])
  : incidents;
```

`IncidentSeverity` is exported from `@/api/types`.

#### Step 2 — Page header per role

```ts
const HEADER: Record<Role, { title: string; description: string }> = {
  admin: {
    title: 'Operations Dashboard',
    description: 'Real-time snapshot of households, centers, resources and active incidents.',
  },
  responder: {
    title: 'Incident Response',
    description: 'Active situations, response tools and capacity at a glance.',
  },
  viewer: {
    title: 'Status Overview',
    description: 'Read-only snapshot of municipality preparedness.',
  },
};
```

`Role` is exported from `@/api/types`.

#### Step 3 — Section composition per role

Build one ordered array from the role:

**admin — byte-identical to today:**

```tsx
[
  <StatCards s={s} />,
  <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
    <ResourceChart className="xl:col-span-2" summaries={summaries} loading={summaries.loading} />
    <CenterLoads centerLoads={centerLoads} />
  </div>,
  <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
    <IncidentList className="xl:col-span-2" incidents={activeIncidents} order="recent" />
    <QuickSummary s={s} showActions />
  </div>,
]
```

`showActions` may be `true` unconditionally for admin (admin outranks responder
in `ROLE_RANK`, so the links were always visible for admin anyway).

**responder — action-first:**

```tsx
[
  <QuickActions />,
  <IncidentList incidents={activeIncidents} order="severity" />,
  <StatCards s={s} />,
  <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
    <CenterLoads centerLoads={centerLoads} />
    <LowStockAlerts summaries={summaries} />
  </div>,
]
```

**viewer — status-first, no actions:**

```tsx
[
  <StatCards s={s} />,
  <IncidentList incidents={activeIncidents} order="recent" />,
  <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
    <CenterLoads centerLoads={centerLoads} />
    <QuickSummary s={s} showActions={false} />
  </div>,
  <ResourceChart summaries={summaries} loading={summaries.loading} />,
]
```

Give `IncidentList` and `ResourceChart` an optional `className` prop so the
grid spans can still be applied; or wrap them in the grid divs as shown above.
The exact grid markup should reproduce the current admin layout precisely —
compare against `git diff` before and after to confirm no admin markup changed.

#### Step 4 — New sections

**`QuickActions()`** — a row of four links. Use the existing `btn-secondary`
utility class (already in `index.css`):

```tsx
<div className="mb-6 flex flex-wrap gap-2">
  <Link to="/incidents" className="btn-primary">Report incident</Link>
  <Link to="/allocation" className="btn-secondary">Run allocation</Link>
  <Link to="/simulator" className="btn-secondary">New scenario</Link>
  <Link to="/map" className="btn-secondary">Open map</Link>
</div>
```

Match the existing button styling used in `DashboardPage` lines 208–212
(`className="btn-secondary flex-1 !text-xs"`) if a more compact row is desired.
Consistency with the existing page beats inventing a new style.

**`LowStockAlerts({ summaries })`** — a `Card` listing only summaries where
`low_stock_count > 0`. `ResourceSummary` has `label`, `total_on_hand`,
`total_required`, `gap`, `low_stock_count`. Show `label`, on-hand vs required,
and an amber `Badge` for the gap. Empty state: `All stock levels are healthy.`
Model the card markup on the existing `CenterLoads` card so spacing and header
style match.

#### Step 5 — Wire it up

```tsx
const { hasRole } = useAuth();
const role: Role = user!.role;   // or derive via hasRole checks if user is null-safe
```

Prefer deriving the role defensively — `user` may be null while auth resolves.
A simple ordering of `hasRole` checks is safest:

```ts
const view = hasRole('admin') ? 'admin' : hasRole('responder') ? 'responder' : 'viewer';
```

Keep the existing early-return `if (stats.loading)` spinner exactly as is.
Keep the existing `useAsync` hooks untouched.

---

## 7. Verification

Run from the paths shown. All four must pass.

```powershell
# 1. Type check + build (repo\frontend)
npx tsc --noEmit
npm run build

# 2. Backend lint + full test suite (repo\backend)
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```

**Expected:** `ruff` → `All checks passed!`; `pytest` → `113 passed`.
If the test count changes or any test fails, a constraint was violated —
revert the offending change rather than editing a test.

Confirm no forbidden files changed:

```powershell
git status --short
```

Permitted changes: `frontend/src/pages/DashboardPage.tsx`,
`frontend/src/pages/HouseholdsPage.tsx`, `frontend/src/pages/CentersPage.tsx`,
`frontend/src/pages/ResourcesPage.tsx`,
`frontend/src/pages/IncidentsPage.tsx`,
`frontend/src/pages/IncidentDetailPage.tsx`.
Anything under `backend/`, `App.tsx`, `AppShell.tsx`, `package.json`,
or `tests/` is a failure.

### Manual role checklist

Start backend (`127.0.0.1:8000`) and frontend dev server (`5173`), then log in
as each demo account — all use password `password`:

| Account | Expected |
|---|---|
| `viewer` | Title **Status Overview**; no quick actions; nav has 8 items minus allocation/simulator; Households/Centers/Resources/Incidents show a **View only** badge; no pencil, no import, no add, no delete anywhere |
| `responder` | Title **Incident Response**; quick-action bar first; incidents sorted critical-first; Import / Add household / Add center / Adjust stock / threshold pencil / Report incident all visible; **no** trash buttons anywhere; allocation + simulator reachable |
| `admin` | Title **Operations Dashboard**; identical layout to before this work; all responder capabilities **plus** trash buttons on Households rows |

`git stash` + reload before/after is a reliable way to confirm the admin
dashboard did not change.

---

## 8. Acceptance criteria

- [ ] `pytest` → 113 passed, zero test files modified
- [ ] `ruff check` clean
- [ ] `tsc --noEmit` exits 0, `npm run build` succeeds
- [ ] `git status` shows only the six permitted page files
- [ ] Admin dashboard renders identically to before (same sections, order, DOM)
- [ ] Viewer, responder, admin each see a different dashboard title and section order
- [ ] Viewer sees a `View only` badge on Household / Center / Resource / Incident pages
- [ ] Responder can create and edit households, centers, and resources in the UI
- [ ] Delete affordances appear for admin only
- [ ] `App.tsx`, `AppShell.tsx`, `package.json` untouched

---

## 9. Out of scope (do not attempt)

1. **User-management UI.** The backend exposes admin-only `POST /api/auth/users`
   with no frontend counterpart. Real gap, but it is new admin functionality,
   not "UI for the other users."
2. **Delete buttons for Centers and Resources.** The API has admin-only deletes;
   the UI has never had them. Adding them is a separate feature.
3. **Backend permission changes.** Explicitly forbidden by constraint #1.
4. **Nav or route changes.** Forbidden by constraints #3 and #4.
5. **Any change to map, allocation, or simulator pages.** Already correct.
6. **Git history rewriting.** There is a pending request to squash two no-op
   commits. It is blocked because another client auto-pulls this branch every
   ~15 minutes and a collaborator may hold unpushed work. Do not attempt it.
