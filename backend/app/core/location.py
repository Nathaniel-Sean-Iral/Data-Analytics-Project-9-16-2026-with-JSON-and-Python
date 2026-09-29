"""Geographic reference data for the Municipality of San Rafael, Bulacan.

Every coordinate in this project is inside San Rafael, Bulacan. Keeping the
reference values in one module stops seed data, map defaults, and validation
from drifting apart.

Source: OpenStreetMap contributors (ODbL 1.0), via the Nominatim and Photon
geocoders, queried for the Municipality of San Rafael (OSM relation 8404894) and
each of its 34 barangays. The municipality centroid and bounds come from the
San Rafael boundary relation; the bounds are padded by roughly 500 m so points
jittered around a barangay centroid near the town edge are not rejected.

BARANGAY_CENTROIDS holds the OSM centroid of each barangay boundary relation
(or, for Dagat-dagatan, the mapped village point). They are reference centroids
for placing synthetic demo records, not surveyed boundary points.

When updating these values, mirror them in frontend/src/lib/location.ts and
frontend/src/api/mock.ts; backend/tests/test_location.py enforces that.
"""

from __future__ import annotations

from app.core.barangays import SAN_RAFAEL_BARANGAYS

MUNICIPALITY = "San Rafael"
PROVINCE = "Bulacan"
REGION = "Central Luzon (Region III)"
PSGC_CODE = "031422000"
ZIP_CODE = "3008"

# OSM centroid of the San Rafael boundary relation (8404894), Poblacion area.
MUNICIPALITY_CENTER: tuple[float, float] = (14.9581, 120.9637)

# Extent of the municipality per OSM, padded by ~0.005 degrees (~500 m) on each
# side. Used to bound the map viewport and to reject coordinates that fall
# outside the locality the system serves.
MUNICIPALITY_BOUNDS = {
    "min_lat": 14.9440,
    "max_lat": 15.0461,
    "min_lng": 120.8881,
    "max_lng": 121.0646,
}

# OSM centroids, (lat, lng), of each barangay.
BARANGAY_CENTROIDS: dict[str, tuple[float, float]] = {
    "BMA-Balagtas": (14.96896, 120.96719),
    "Banca-banca": (15.02420, 120.92146),
    "Caingin": (14.97175, 120.94344),
    "Coral na Bato": (14.99425, 120.97917),
    "Cruz na Daan": (15.02956, 120.93478),
    "Dagat-dagatan": (15.03384, 120.91450),
    "Diliman I": (15.02433, 120.94924),
    "Diliman II": (15.03318, 120.95317),
    "Capihan": (14.99886, 120.93026),
    "Libis": (14.95701, 120.96948),
    "Lico": (14.96104, 120.95632),
    "Maasim": (15.03523, 120.93637),
    "Mabalas-balas": (15.02530, 120.94267),
    "Maguinao": (15.02276, 120.93356),
    "Maronquillo": (14.96739, 121.00140),
    "Paco": (14.99586, 120.90566),
    "Pansumaloc": (15.01738, 120.89682),
    "Pantubig": (14.96550, 120.95296),
    "Pasong Bangkal": (15.00584, 121.00997),
    "Pasong Callos": (15.00053, 121.00035),
    "Pasong Intsik": (15.01094, 120.96884),
    "Pinacpinacan": (14.99773, 120.91330),
    "Poblacion": (14.95532, 120.96388),
    "Pulo": (14.96192, 121.01451),
    "Pulong Bayabas": (15.01220, 120.90463),
    "Salapongan": (15.01957, 120.96386),
    "Sampaloc": (14.98183, 120.92646),
    "San Agustin": (15.03042, 120.92718),
    "San Roque": (15.00880, 120.93264),
    "Talacsan": (14.96003, 120.97918),
    "Tambubong": (14.96867, 120.92642),
    "Tukod": (14.99451, 121.04935),
    "Ulingao": (14.97155, 120.91310),
    "Sapang Pahalang": (14.99746, 121.03880),
}

FALLBACK_COORDINATES: tuple[float, float] = MUNICIPALITY_CENTER


def is_within_municipality(lat: float, lng: float) -> bool:
    return (
        MUNICIPALITY_BOUNDS["min_lat"] <= lat <= MUNICIPALITY_BOUNDS["max_lat"]
        and MUNICIPALITY_BOUNDS["min_lng"] <= lng <= MUNICIPALITY_BOUNDS["max_lng"]
    )


def coordinates_for(barangay: str) -> tuple[float, float]:
    """Return the centroid for a barangay, falling back to the town center."""
    return BARANGAY_CENTROIDS.get(barangay, FALLBACK_COORDINATES)


def location_label() -> str:
    return f"{MUNICIPALITY}, {PROVINCE}"


__all__ = [
    "BARANGAY_CENTROIDS",
    "FALLBACK_COORDINATES",
    "MUNICIPALITY",
    "MUNICIPALITY_BOUNDS",
    "MUNICIPALITY_CENTER",
    "PROVINCE",
    "PSGC_CODE",
    "REGION",
    "SAN_RAFAEL_BARANGAYS",
    "ZIP_CODE",
    "coordinates_for",
    "is_within_municipality",
    "location_label",
]
