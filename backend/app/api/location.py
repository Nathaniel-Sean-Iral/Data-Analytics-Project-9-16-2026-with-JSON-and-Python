from fastapi import APIRouter

from app.core.barangays import SAN_RAFAEL_BARANGAYS
from app.core.location import (
    BARANGAY_CENTROIDS,
    MUNICIPALITY,
    MUNICIPALITY_BOUNDS,
    MUNICIPALITY_CENTER,
    PROVINCE,
    PSGC_CODE,
    REGION,
    ZIP_CODE,
    location_label,
)

router = APIRouter(tags=["location"])


@router.get("/location")
def get_location():
    return {
        "municipality": MUNICIPALITY,
        "province": PROVINCE,
        "region": REGION,
        "psgc_code": PSGC_CODE,
        "zip_code": ZIP_CODE,
        "label": location_label(),
        "center": {"lat": MUNICIPALITY_CENTER[0], "lng": MUNICIPALITY_CENTER[1]},
        "bounds": MUNICIPALITY_BOUNDS,
        "barangays": list(SAN_RAFAEL_BARANGAYS),
        "barangay_centroids": {
            name: {"lat": coords[0], "lng": coords[1]}
            for name, coords in BARANGAY_CENTROIDS.items()
        },
    }
