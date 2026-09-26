"""Dev seed data mirroring the frontend mock layer.

Run from the backend directory with the venv active:
    python seed.py
"""

from datetime import datetime, timezone

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.center import EvacuationCenter
from app.models.household import Household
from app.models.incident import Incident
from app.models.resource import Resource
from app.models.user import User

BARANGAYS = [
    "Poblacion",
    "San Roque",
    "San Juan",
    "Santo Niño",
    "Bagong Silang",
    "Malanday",
    "San Pablo",
    "Kalayaan",
]

NAMES = [
    ("Reyes", "Juan"), ("Santos", "Maria"), ("Cruz", "Pedro"), ("Bautista", "Ana"),
    ("Ocampo", "Ramon"), ("Villanueva", "Liza"), ("Ramos", "Mario"), ("Garcia", "Nena"),
    ("Mendoza", "Rico"), ("Torres", "Carmen"), ("Flores", "Berto"), ("Aquino", "Gemma"),
    ("Navarro", "Dante"), ("Salazar", "Corazon"), ("Del Rosario", "Efren"), ("Padilla", "Flor"),
    ("Dizon", "Gilbert"), ("Castillo", "Helen"), ("Mercado", "Irene"), ("Lopez", "Jose"),
]


def seed_users(db):
    users = [
        User(username="admin", full_name="Municipal Admin", email="admin@local.gov.ph", role="admin", hashed_password=hash_password("admin"), is_active=True),
        User(username="responder", full_name="MDRRMO Responder", email="responder@local.gov.ph", role="responder", hashed_password=hash_password("responder"), is_active=True),
        User(username="viewer", full_name="Guest Viewer", email="viewer@local.gov.ph", role="viewer", hashed_password=hash_password("viewer"), is_active=True),
    ]
    for u in users:
        if db.query(User).filter(User.username == u.username).first() is None:
            db.add(u)


def seed_households(db):
    if db.query(Household).count():
        return
    for i in range(40):
        family, given = NAMES[i % len(NAMES)]
        barangay = BARANGAYS[i % len(BARANGAYS)]
        size = 2 + ((i * 3) % 6)
        rand = lambda n: (i * 7 + n * 13) % 100  # noqa: E731
        db.add(
            Household(
                household_no=f"HH-{i + 1:04d}",
                head_name=f"{given} {family}",
                address=f"Blk {(i % 20) + 1}, Lot {(i % 8) + 1}, {barangay}",
                barangay=barangay,
                size=size,
                children_count=rand(1) % 4,
                elderly_count=rand(2) % 3,
                pwd_count=rand(3) % 2,
                contact=f"09{(i * 123456 + 1000000) % 100000000:08d}",
                lat=14.08 + (i % 8) * 0.02,
                lng=121.14 + ((i * 3) % 8) * 0.018,
            )
        )


def seed_centers(db):
    centers = [
        ("Poblacion Elementary School", "Poblacion", "Brgy Hall Rd", 500, 210, ["kitchen", "water", "power", "bathrooms"], "09171234001", 14.095, 121.148, "active"),
        ("San Roque Covered Court", "San Roque", "Mabini St", 300, 120, ["water", "power"], "09171234002", 14.082, 121.13, "active"),
        ("San Juan High School", "San Juan", "National Rd", 450, 305, ["kitchen", "water", "power", "bathrooms", "clinic"], "09171234003", 14.11, 121.16, "active"),
        ("Santo Niño Gymnasium", "Santo Niño", "Rizal Ave", 200, 15, ["water", "power"], "09171234004", 14.07, 121.125, "standby"),
        ("Bagong Silang Barangay Hall", "Bagong Silang", "Diversity Rd", 150, 88, ["kitchen", "water"], "09171234005", 14.125, 121.175, "active"),
        ("Malanday Community Center", "Malanday", "Seaside Rd", 400, 240, ["kitchen", "water", "power", "bathrooms"], "09171234006", 14.062, 121.108, "active"),
    ]
    if db.query(EvacuationCenter).count():
        return
    for c in centers:
        db.add(
            EvacuationCenter(
                name=c[0], barangay=c[1], address=c[2], capacity=c[3], current_occupants=c[4],
                facilities=c[5], contact=c[6], lat=c[7], lng=c[8], status=c[9],
            )
        )


def seed_resources(db):
    resources = [
        ("Rice (50kg sack)", "rice", "sacks", 320, 200, "Municipal Warehouse"),
        ("Bottled Water (gallon)", "water", "gallons", 140, 400, "Municipal Warehouse"),
        ("Medicine Kit", "medicine", "kits", 45, 60, "Rural Health Unit"),
        ("Blankets", "blankets", "pc", 260, 150, "Rotary Store"),
        ("Hygiene Kits", "hygiene", "kits", 90, 120, "Municipal Warehouse"),
        ("Canned Sardines", "canned_goods", "cans", 480, 300, "Municipal Warehouse"),
        ("Tents", "tents", "pc", 12, 30, "MDRRMO Office"),
        ("Sleeping Mats", "mats", "pc", 300, 180, "Rotary Store"),
    ]
    if db.query(Resource).count():
        return
    for name, rtype, unit, qty, threshold, stored_in in resources:
        db.add(
            Resource(
                name=name, type=rtype, unit=unit, quantity_on_hand=qty,
                threshold=threshold, stored_in=stored_in,
            )
        )


def seed_incidents(db):
    incidents = [
        ("Flash flood due to monsoon rains", "flood", "Malanday", "high", "responding",
         "River overflow submerged low-lying streets. Residents moved to Malanday Community Center.",
         14.061, 121.107, 45, "MDRRMO", "2026-09-15T06:15:00Z", "2026-09-16T08:00:00Z"),
        ("Fire broke out in residential area", "fire", "Poblacion", "critical", "assessing",
         "Fire affected 8 houses near the public market. Fire trucks on scene.",
         14.094, 121.147, 8, "BFP", "2026-09-16T11:40:00Z", "2026-09-16T12:10:00Z"),
        ("Landslide along mountain road", "landslide", "Kalayaan", "moderate", "assessing",
         "Debris blocked access road; no casualties reported yet.",
         14.13, 121.2, 3, "Barangay Tanod", "2026-09-14T14:05:00Z", "2026-09-15T07:30:00Z"),
        ("Storm surge warning issued", "typhoon", "San Juan", "low", "reported",
         "Pre-emptive evacuation being organized ahead of projected storm surge.",
         14.109, 121.159, 20, "PAGASA", "2026-09-16T02:00:00Z", "2026-09-16T02:00:00Z"),
        ("River overflow in low-lying areas", "flood", "San Roque", "high", "responding",
         "Water level at knee-to-waist height along Mabini St.",
         14.081, 121.129, 32, "MDRRMO", "2026-09-15T05:45:00Z", "2026-09-16T07:00:00Z"),
    ]
    if db.query(Incident).count():
        return
    for title, itype, barangay, severity, status, desc, lat, lng, affected, reported_by, reported_at, updated_at in incidents:
        db.add(
            Incident(
                title=title, type=itype, barangay=barangay, severity=severity, status=status,
                description=desc, lat=lat, lng=lng, affected_households=affected,
                reported_by=reported_by,
                reported_at=datetime.fromisoformat(reported_at.replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(updated_at.replace("Z", "+00:00")),
            )
        )


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
        seed_households(db)
        seed_centers(db)
        seed_resources(db)
        seed_incidents(db)
        db.commit()
        print("Seed complete.")
        print(f"  households:  {db.query(Household).count()}")
        print(f"  centers:     {db.query(EvacuationCenter).count()}")
        print(f"  resources:   {db.query(Resource).count()}")
        print(f"  incidents:   {db.query(Incident).count()}")
        print(f"  users:       {db.query(User).count()}")
        print("\nDemo accounts: admin/admin, responder/responder, viewer/viewer")
    finally:
        db.close()


if __name__ == "__main__":
    main()