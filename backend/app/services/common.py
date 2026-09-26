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

RESOURCE_TYPE_LABELS = {
    "rice": "Rice",
    "water": "Water",
    "medicine": "Medicine",
    "blankets": "Blankets",
    "hygiene": "Hygiene Kits",
    "canned_goods": "Canned Goods",
    "clothing": "Clothing",
    "mats": "Sleeping Mats",
    "tents": "Tents",
    "other": "Other",
}

# Estimated consumption rates used by the scenario simulator (per evacuee).
PER_PERSON_RATES = {
    "rice": 0.1,          # 50kg sack
    "water": 3.0,         # gallon
    "medicine": 0.25,     # kit
    "blankets": 0.5,      # piece
    "hygiene": 0.5,       # kit
    "canned_goods": 0.5,  # can
    "mats": 0.5,          # piece
    "clothing": 0.5,      # piece
    "tents": 0.05,        # piece (1 per 20 people)
    "other": 0.05,
}

INCIDENT_STATUS_FLOW = ["reported", "assessing", "responding", "resolved"]