# Data Model — San Rafael Disaster Preparedness System

Scope: Municipality of San Rafael, Bulacan (PSGC `031422000`), 34 barangays.

Source of truth for the schema is the SQLAlchemy models in `backend/app/models/`.
Migrations live in `backend/alembic/versions/`:

| Revision | Change |
| --- | --- |
| `0001_initial_schema` | Base tables: households, evacuation_centers, resources, incidents, users |
| `0002_resource_transactions_and_assignments` | `resource_transactions`, `evacuation_assignments`, `incidents.zone_geojson` |
| `0003_household_contact_optional` | `households.contact` becomes nullable |

## Entities

```
                    ┌──────────────┐
                    │     User     │
                    │──────────────│
                    │ id      PK   │
                    │ username UQ  │
                    │ full_name    │
                    │ role         │  admin | responder | viewer
                    │ email        │
                    │ password_hash│  PBKDF2-SHA256, 600k iterations
                    │ is_active    │
                    │ created_at   │
                    └──────────────┘
                     (no FKs: users are not tied to a geography)

 ┌──────────────┐        ┌─────────────────────┐        ┌──────────────────┐
 │  Household   │        │  EvacuationCenter   │        │     Resource     │
 │──────────────│        │─────────────────────│        │──────────────────│
 │ id       PK  │        │ id              PK  │        │ id           PK  │
 │ household_no UQ│      │ name                │        │ name             │
 │ head_name     │       │ barangay (idx)     │        │ type        (idx)│
 │ address       │       │ address            │        │ unit             │
 │ barangay (idx)│       │ capacity           │        │ quantity_on_hand │
 │ size          │       │ current_occupants  │        │ threshold        │
 │ children_count│       │ facilities  CSV    │        │ expiry           │
 │ elderly_count │       │ contact            │        │ stored_in        │
 │ pwd_count     │       │ lat / lng          │        │ updated_at       │
 │ contact  (null)│      │ status             │        └────────┬─────────┘
 │ lat / lng     │       └──────────┬──────────┘                 │
 │ notes         │                  │                            │ 1:N
 │ is_active     │                  │                            │
 └────┬─────────┘                   │                            │
      │ 1:N                         │ 1:N                        │
      │                             │                            │
      │                    ┌────────┴────────────────────────────┴─────────┐
      │                    │        EvacuationAssignment                 │
      └───────────────────>│─────────────────────────────────────────────│
                           │ id                 PK                       │
                           │ request_id     (idx)  groups one run        │
                           │ household_id       FK -> households         │
                           │ center_id          FK -> evacuation_centers│
                           │ occupants      people, NOT households       │
                           │ distance_km    haversine                    │
                           │ status         assigned | overflow          │
                           │ assigned_at        DateTime                 │
                           └─────────────────────────────────────────────┘

 ┌────────────────────┐
 │ ResourceTransaction│  append-only stock audit trail
 │────────────────────│
 │ id            PK  │
 │ resource_id      FK -> resources   (CASCADE)
 │ delta            signed change
 │ quantity_after   running balance after the change
 │ reason           created | stock-in | stock-out | custom
 │ note
 │ performed_by     username
 │ created_at       DateTime (idx)
 └────────────────────┘

 ┌──────────────┐
 │   Incident   │
 │──────────────│
 │ id        PK │
 │ title        │
 │ type         │  flood | fire | earthquake | landslide | typhoon | other
 │ barangay     │
 │ severity     │  low | moderate | high | critical
 │ status       │  reported | assessing | responding | resolved
 │ description  │
 │ lat / lng    │
 │ zone_geojson │  JSON text: Polygon/MultiPolygon of the affected area
 │ affected_households │
 │ reported_by  │  free text; mirrors User.username
 │ reported_at  │  String (ISO-8601)
 │ updated_at   │  String (ISO-8601)
 └──────────────┘
```

## Design notes

**Occupancy is counted in people, not households.** `EvacuationAssignment.occupants`
carries the household's own `size`, and the allocator refuses to split a household
across two centers. The first implementation incremented center load by 1 per
household, which under-reported load and could overfill a center.

**`resource_transactions` is written in the same transaction as the quantity
change.** A rejected adjustment (one that would drive stock negative) raises before
any row is written, so the ledger and `quantity_on_hand` cannot disagree.

**`evacuation_assignments` is opt-in.** `POST /evacuations/allocate` only writes rows
when `persist: true` is passed, so a dashboard stat never creates data. Rows are
grouped by `request_id` and readable via `GET /evacuations/assignments/{request_id}`.

**`barangay` is a validated string, not an FK.** Valid values live in
`app/core/barangays.py` (34 names) and are served by `GET /api/location`. The API
does not yet reject unknown barangay values on write; that is tracked as a gap.

**`households.contact` is nullable** (revision `0003`). Requiring a phone number made
registration and import fail with an opaque NOT NULL error, which is unrealistic for
household registration.

**`households.lat`/`lng` are NOT NULL but optional on input.** When omitted, the API
falls back to the barangay centroid in `app/core/location.py` so every household is
placed on the map.

**Timestamps are inconsistent.** `Incident.reported_at` and `updated_at` are
`String` columns holding ISO-8601; every other time column is a real `DateTime`.
A follow-up migration should convert them.

**`facilities` is a comma-separated string.** `serialize_center` splits on commas and
strips whitespace. A join table would be more correct; left as-is for now.

**SQLite by default, PostgreSQL supported.** `DATABASE_URL` selects the backend. Note
that `String` columns have no length limit and become `VARCHAR` without length on
PostgreSQL. Nullability changes need `op.batch_alter_table` because SQLite cannot
`ALTER` a column in place.

## Migrations

```bash
cd backend
alembic upgrade head                      # apply
alembic downgrade base                    # roll back everything
alembic revision --autogenerate -m "..."  # after changing a model
alembic check                             # verify models match migrations
```

The app also calls `Base.metadata.create_all` on startup, which is convenient for a
fresh clone but will not alter existing tables. Use Alembic for anything beyond
first run. CI runs `alembic check` so a model change without a migration fails the
build.
