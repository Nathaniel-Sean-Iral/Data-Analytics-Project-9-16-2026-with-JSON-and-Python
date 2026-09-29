"""Deterministic demo dataset for San Rafael, Bulacan.

Pure generators back the two demo surfaces:

* On-first-boot DB seeding (``store.seed_demo_data``), and
* The committed sample files in ``sample-data/`` (CSV + GeoJSON) that exercise
  the household import endpoints.

A fixed RNG seed makes every reseed byte-identical, so a demo is reproducible.
All data is fabricated sample data for demonstration purposes only — not a real
census extract.
"""

from __future__ import annotations

import json
import random
from typing import Any

from app.core.barangays import SAN_RAFAEL_BARANGAYS
from app.core.location import coordinates_for

DATA_SEED = 20260929
TARGET_HOUSEHOLDS = 240

FIRST_NAMES = [
    "Maria", "Jose", "Juan", "Ana", "Pedro", "Rosa", "Carlos", "Liza", "Miguel", "Elena",
    "Andres", "Teresa", "Ramon", "Carmen", "Antonio", "Lourdes", "Benito", "Gloria", "Noli", "Imelda",
    "Reynaldo", "Marites", "Edwin", "Jonalyn", "Romeo", "Fe", "Mario", "Riza", "Dante", "Myra",
    "Rogelio", "Cecilia", "Nestor", "Divina", "Ferdinand", "Luzviminda", "Gregorio", "Corazon", "Isagani", "Mercedes",
]

SURNAMES = [
    "Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Garcia", "Mendoza", "Torres", "Flores",
    "Ramos", "Aquino", "Navarro", "Del Rosario", "Villanueva", "Domingo", "Castillo",
    "Gutierrez", "Manalo", "Soriano", "Pascual", "Salazar", "Serrano", "Espino", "Yson",
    "Magpayo", "Tomas", "Santianez", "Mercado", "Vergara", "Buenaventura", "Ilustre",
    "Marquez", "Alcantara", "Gonzales", "Carpio", "Lucero", "Ong", "Santiago",
]

STREETS = [
    "Rizal", "Mabini", "Luna", "Bonifacio", "Del Pilar", "Aguinaldo", "Quezon", "M. Hizon",
    "Burgos", "Jacinto", "San Jose", "Katubusan", "Liberation", "M.H. del Pilar", "Gov. Padilla", "P. Burgos",
]

NOTES_POOL = [
    "Needs wheelchair access",
    "Two infants in household",
    "Pregnant member",
    "Elderly resident living alone",
    "Assisted breathing device",
    "No electricity connection",
    "Single income earner",
    "Recently relocated from flood-prone area",
]

# (name, barangay, capacity, current occupants, facilities, status, contact)
DEMO_CENTERS: list[tuple[Any, ...]] = [
    (
        "San Rafael Central School Evacuation Center",
        "Poblacion", 250, 42, "kitchen,water,power", "active", "09181110001",
    ),
    ("San Roque Barangay Hall", "San Roque", 80, 30, "kitchen,water", "active", "09181110002"),
    ("BMA-Balagtas Covered Court", "BMA-Balagtas", 150, 55, "water,power", "active", "09181110003"),
    ("Maronquillo Elementary School", "Maronquillo", 120, 12, "kitchen,water", "active", "09181110004"),
    ("Maguinao Parish Gymnasium", "Maguinao", 180, 8, "kitchen,water,power", "standby", "09181110005"),
    ("Pasong Bangkal Health Center", "Pasong Bangkal", 100, 0, "water,power", "active", "09181110006"),
    ("Pantubig Multi-Purpose Hall", "Pantubig", 90, 25, "kitchen,water", "active", "09181110007"),
    ("Talacsan High School Gym", "Talacsan", 220, 64, "kitchen,water,power", "active", "09181110008"),
    ("Corregidor Depressed Evacuation Shelter", "Pulong Bayabas", 60, 0, "water", "closed", "09181110009"),
]

# (name, type, unit, on hand, threshold, expiry, stored_in)
DEMO_RESOURCES: list[tuple[Any, ...]] = [
    ("Rice", "rice", "kg", 420, 300, "2027-03-15", "Warehouse A"),
    ("Drinking Water", "water", "liters", 1500, 1200, "2027-06-01", "Warehouse B"),
    ("Medicine", "medicine", "boxes", 80, 100, "2026-12-31", "Clinic Store"),
    ("Blankets", "blankets", "pieces", 180, 160, None, "Relief Shelf"),
    ("Hygiene Kits", "hygiene", "kits", 40, 80, "2027-01-20", "Relief Shelf"),
    ("Canned Goods", "canned_goods", "cans", 950, 900, "2027-09-30", "Warehouse A"),
    ("Sleeping Mats", "mats", "pieces", 120, 150, None, "Warehouse B"),
    ("Family Tents", "tents", "units", 12, 30, "2027-12-01", "Storage Yard"),
]

# (title, type, barangay, severity, status, description, affected_households, reported_by)
DEMO_INCIDENTS: list[tuple[Any, ...]] = [
    (
        "Flooding along Sapang Munti creek",
        "flood",
        "BMA-Balagtas",
        "high",
        "responding",
        "Water level rising in low-lying homes near the creek; pre-emptive evacuation advised.",
        45,
        "responder",
    ),
    (
        "Afternoon structural fire in Poblacion",
        "fire",
        "Poblacion",
        "moderate",
        "assessing",
        "Two residential units damaged near the market; fire out, damage assessment ongoing.",
        8,
        "responder",
    ),
    (
        "Rain-induced landslide threat in Ulingao",
        "landslide",
        "Ulingao",
        "critical",
        "monitoring",
        "Cracks reported on the slope above the road; residents advised to stay alert.",
        15,
        "admin",
    ),
]


def _random_phone(rng: random.Random) -> str:
    return "0917" + "".join(str(rng.randint(0, 9)) for _ in range(7))


def _random_head_name(rng: random.Random) -> str:
    first = rng.choice(FIRST_NAMES)
    surname = rng.choice(SURNAMES)
    return f"{first} {surname}"


def _random_address(rng: random.Random) -> str:
    return f"Purok {rng.randint(1, 6)}, {rng.choice(STREETS)} Street"


def _random_vulnerable_counts(rng: random.Random, size: int) -> tuple[int, int, int]:
    """(children, elderly, pwd) that never exceed ``size`` or each other's budget."""
    remaining = size
    children = rng.randint(0, min(3, remaining))
    remaining -= children
    elderly = rng.randint(0, min(2, remaining)) if remaining else 0
    remaining -= elderly
    pwd = 1 if remaining and rng.random() < 0.12 else 0
    return children, elderly, pwd


def _jitter(rng: random.Random, base: float, spread: float) -> float:
    return round(base + rng.uniform(-spread, spread), 6)


def generate_households(rng: random.Random | None = None) -> list[dict[str, Any]]:
    """~240 households spread across all 34 barangays, deterministic."""
    rng = rng or random.Random(DATA_SEED)

    weights = {barangay: rng.uniform(0.7, 1.3) for barangay in SAN_RAFAEL_BARANGAYS}
    total_weight = sum(weights.values())
    counts = [round(weights[b] / total_weight * TARGET_HOUSEHOLDS) for b in SAN_RAFAEL_BARANGAYS]
    # Reconcile rounding so the total is exactly TARGET_HOUSEHOLDS.
    diff = TARGET_HOUSEHOLDS - sum(counts)
    for index in range(abs(diff)):
        counts[index % len(counts)] += 1 if diff > 0 else -1

    households: list[dict[str, Any]] = []
    sequence = 1
    for barangay, count in zip(SAN_RAFAEL_BARANGAYS, counts, strict=True):
        center_lat, center_lng = coordinates_for(barangay)
        for _ in range(count):
            size = rng.choice([1, 2, 3, 3, 4, 4, 4, 5, 5, 6, 6, 7, 8])
            children, elderly, pwd = _random_vulnerable_counts(rng, size)
            households.append(
                {
                    "household_no": f"H-{sequence:04d}",
                    "head_name": _random_head_name(rng),
                    "address": _random_address(rng),
                    "barangay": barangay,
                    "size": size,
                    "children_count": children,
                    "elderly_count": elderly,
                    "pwd_count": pwd,
                    "contact": _random_phone(rng),
                    "lat": _jitter(rng, center_lat, 0.003),
                    "lng": _jitter(rng, center_lng, 0.003),
                    "notes": rng.choice(NOTES_POOL) if rng.random() < 0.25 else None,
                }
            )
            sequence += 1
    return households


def generate_centers() -> list[dict[str, Any]]:
    centers: list[dict[str, Any]] = []
    for tuple_ in DEMO_CENTERS:
        lat, lng = coordinates_for(tuple_[1])
        centers.append(
            {
                "name": tuple_[0],
                "barangay": tuple_[1],
                "address": f"{tuple_[0]} compound, {tuple_[1]}",
                "capacity": tuple_[2],
                "current_occupants": tuple_[3],
                "facilities": tuple_[4],
                "contact": tuple_[6],
                "lat": lat,
                "lng": lng,
                "status": tuple_[5],
            }
        )
    return centers


def generate_resources() -> list[dict[str, Any]]:
    return [
        {
            "name": tuple_[0],
            "type": tuple_[1],
            "unit": tuple_[2],
            "quantity_on_hand": tuple_[3],
            "threshold": tuple_[4],
            "expiry": tuple_[5],
            "stored_in": tuple_[6],
            "updated_at": "2026-09-25T10:00:00+00:00",
        }
        for tuple_ in DEMO_RESOURCES
    ]


def _incident_zone(lat: float, lng: float) -> dict[str, Any]:
    """A rough rectangular patch around a point, GeoJSON [lng, lat] rings."""
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [round(lng - 0.0025, 6), round(lat - 0.0016, 6)],
                [round(lng + 0.0026, 6), round(lat - 0.0016, 6)],
                [round(lng + 0.0026, 6), round(lat + 0.0017, 6)],
                [round(lng - 0.0025, 6), round(lat + 0.0017, 6)],
                [round(lng - 0.0025, 6), round(lat - 0.0016, 6)],
            ]
        ],
    }


def generate_incidents(now: str = "2026-09-26T07:30:00+00:00") -> list[dict[str, Any]]:
    incidents = []
    for tuple_ in DEMO_INCIDENTS:
        lat, lng = coordinates_for(tuple_[2])
        incidents.append(
            {
                "title": tuple_[0],
                "type": tuple_[1],
                "barangay": tuple_[2],
                "severity": tuple_[3],
                "status": tuple_[4],
                "description": tuple_[5],
                "reported_at": now,
                "updated_at": now,
                "lat": lat,
                "lng": lng,
                "affected_households": tuple_[6],
                "reported_by": tuple_[7],
                "zone_geojson": json.dumps(_incident_zone(lat, lng)),
            }
        )
    return incidents
