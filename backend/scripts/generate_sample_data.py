"""Emit the committed sample import files used to demo the data-entry flows.

Writes the same deterministic household dataset that ``seed_demo_data`` inserts
into the database as:

* ``sample-data/households_san_rafael.csv``  ->  POST /api/households/import
* ``sample-data/households_san_rafael.geojson`` -> POST /api/households/import/geojson

Run from the ``backend`` directory::

    python -m scripts.generate_sample_data
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from app.services.demo_data import generate_households

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DIR = REPO_ROOT / "sample-data"

CSV_COLUMNS = [
    "household_no",
    "head_name",
    "address",
    "barangay",
    "size",
    "children_count",
    "elderly_count",
    "pwd_count",
    "contact",
    "lat",
    "lng",
    "notes",
]


def write_csv(households: list[dict], destination: Path) -> None:
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in households:
            writer.writerow({column: record.get(column) for column in CSV_COLUMNS})


def write_geojson(households: list[dict], destination: Path) -> None:
    features = []
    for record in households:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [record["lng"], record["lat"]]},
                "properties": {
                    "household_no": record["household_no"],
                    "head_name": record["head_name"],
                    "address": record["address"],
                    "barangay": record["barangay"],
                    "size": record["size"],
                    "children_count": record["children_count"],
                    "elderly_count": record["elderly_count"],
                    "pwd_count": record["pwd_count"],
                    "contact": record["contact"],
                    "notes": record["notes"],
                },
            }
        )
    collection = {"type": "FeatureCollection", "features": features}
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(collection, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    households = generate_households()

    csv_path = SAMPLE_DIR / "households_san_rafael.csv"
    geojson_path = SAMPLE_DIR / "households_san_rafael.geojson"

    write_csv(households, csv_path)
    write_geojson(households, geojson_path)

    print(f"Wrote {len(households)} households to:")
    print(f"  {csv_path}")
    print(f"  {geojson_path}")


if __name__ == "__main__":
    main()
