"""Geographic reference data for the Municipality of San Rafael, Bulacan.

Every coordinate in this project is inside San Rafael, Bulacan. Keeping the
reference values in one module stops seed data, map defaults, and validation
from drifting apart.

Coordinates marked "centroid" are approximate barangay centroids used to give
the demo dataset a plausible geographic spread. They are not surveyed boundary
points. MUNICIPALITY_CENTER is the published coordinate for Poblacion, the
barangay where the municipal hall sits.
"""

from __future__ import annotations

from app.core.barangays import SAN_RAFAEL_BARANGAYS

MUNICIPALITY = "San Rafael"
PROVINCE = "Bulacan"
REGION = "Central Luzon (Region III)"
PSGC_CODE = "031422000"
ZIP_CODE = "3008"

# Poblacion, San Rafael, Bulacan (municipal hall).
MUNICIPALITY_CENTER: tuple[float, float] = (14.9571, 120.9629)

# Approximate extent of the municipality, used to bound the map viewport and to
# reject coordinates that fall outside the locality the system serves.
MUNICIPALITY_BOUNDS = {
    "min_lat": 14.9000,
    "max_lat": 15.0200,
    "min_lng": 120.9000,
    "max_lng": 121.0200,
}

# Approximate centroids, (lat, lng), spread around MUNICIPALITY_CENTER.
BARANGAY_CENTROIDS: dict[str, tuple[float, float]] = {
    "BMA-Balagtas": (14.9568, 120.9519),
    "Banca-banca": (14.9800, 120.9740),
    "Caingin": (14.9322, 120.9540),
    "Coral na Bato": (14.9250, 120.9920),
    "Cruz na Daan": (14.9905, 120.9480),
    "Dagat-dagatan": (14.9440, 120.9320),
    "Diliman I": (14.9700, 120.9880),
    "Diliman II": (14.9760, 120.9960),
    "Capihan": (14.9610, 120.9420),
    "Libis": (14.9605, 120.9555),
    "Lico": (14.9530, 120.9690),
    "Maasim": (14.9960, 120.9880),
    "Mabalas-balas": (14.9085, 120.9700),
    "Maguinao": (14.9355, 120.9845),
    "Maronquillo": (14.9900, 120.9620),
    "Paco": (14.9200, 120.9600),
    "Pansumaloc": (14.9130, 120.9450),
    "Pantubig": (14.9680, 120.9350),
    "Pasong Bangkal": (14.9810, 120.9540),
    "Pasong Callos": (14.9660, 120.9700),
    "Pasong Intsik": (14.9645, 120.9665),
    "Pinacpinacan": (14.9505, 120.9740),
    "Poblacion": (14.9571, 120.9629),
    "Pulo": (14.9400, 120.9680),
    "Pulong Bayabas": (14.9250, 120.9780),
    "Salapongan": (14.9510, 120.9800),
    "Sampaloc": (14.9640, 120.9590),
    "San Agustin": (14.9420, 120.9900),
    "San Roque": (14.9700, 120.9780),
    "Talacsan": (14.9855, 120.9400),
    "Tambubong": (14.9370, 120.9520),
    "Tukod": (14.9480, 120.9400),
    "Ulingao": (14.9880, 120.9720),
    "Sapang Pahalang": (14.9150, 120.9880),
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
