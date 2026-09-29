"""Emit the committed sample import files used to demo the data-entry flows.

Writes the same deterministic household dataset that ``seed_demo_data`` inserts
into the database as:

* ``sample-data/households_san_rafael.csv``  ->  POST /api/households/import
* ``sample-data/households_san_rafael.geojson`` -> POST /api/households/import/geojson
* ``sample-data/households_import_test.csv`` -> same endpoint, unique household
  numbers so the import reports rows created even on a freshly seeded database

Run from the ``backend`` directory::

    python -m scripts.generate_sample_data
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from app.services.demo_data import DATA_SEED, generate_households

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DIR = REPO_ROOT / "sample-data"

# The import endpoint skips rows whose household_no already exists, so the main
# sample file reports "0 created" against a seeded database. The test file uses
# a distinct prefix and a different RNG stream to prove the flow end to end.
IMPORT_TEST_ROWS = 30
IMPORT_TEST_PREFIX = "IMP"

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


def build_import_test(households: list[dict]) -> list[dict]:
    """Renumber a slice of the dataset so every row is new to the database."""
    records = []
    for index, record in enumerate(households[:IMPORT_TEST_ROWS], start=1):
        duplicate = dict(record)
        duplicate["household_no"] = f"{IMPORT_TEST_PREFIX}-{index:04d}"
        records.append(duplicate)
    return records


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    households = generate_households()

    csv_path = SAMPLE_DIR / "households_san_rafael.csv"
    geojson_path = SAMPLE_DIR / "households_san_rafael.geojson"
    test_csv_path = SAMPLE_DIR / "households_import_test.csv"

    write_csv(households, csv_path)
    write_geojson(households, geojson_path)
    write_csv(build_import_test(generate_households(rng=random.Random(DATA_SEED + 1))), test_csv_path)

    print(f"Wrote {len(households)} households to:")
    print(f"  {csv_path}")
    print(f"  {geojson_path}")
    print(f"Wrote {IMPORT_TEST_ROWS} import-test households to:")
    print(f"  {test_csv_path}")


if __name__ == "__main__":
    main()
