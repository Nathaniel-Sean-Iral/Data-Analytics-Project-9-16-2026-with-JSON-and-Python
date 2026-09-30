from __future__ import annotations

from math import isfinite
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field

Role = Literal["admin", "responder", "viewer"]
IncidentType = Literal["flood", "fire", "earthquake", "landslide", "typhoon", "other"]
IncidentSeverity = Literal["low", "moderate", "high", "critical"]
IncidentStatus = Literal["reported", "assessing", "responding", "resolved"]
CenterStatus = Literal["active", "standby", "closed"]
ResourceType = Literal[
    "rice",
    "water",
    "medicine",
    "blankets",
    "hygiene",
    "canned_goods",
    "clothing",
    "mats",
    "tents",
    "other",
]


def _validate_zone_geometry(geometry: dict) -> dict:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geometry_type not in ("Polygon", "MultiPolygon"):
        raise ValueError("Incident zones must be a GeoJSON Polygon or MultiPolygon")
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError("Incident zone coordinates must not be empty")

    polygons = [coordinates] if geometry_type == "Polygon" else coordinates
    for polygon in polygons:
        if not isinstance(polygon, list) or not polygon:
            raise ValueError("Each incident zone polygon must contain at least one ring")
        for ring in polygon:
            if not isinstance(ring, list) or len(ring) < 4:
                raise ValueError("Each incident zone ring must contain at least four positions")
            for position in ring:
                if (
                    not isinstance(position, list)
                    or len(position) < 2
                    or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in position[:2])
                    or not all(isfinite(value) for value in position[:2])
                    or not -180 <= position[0] <= 180
                    or not -90 <= position[1] <= 90
                ):
                    raise ValueError("Incident zone positions must contain valid [longitude, latitude] coordinates")
            if ring[0] != ring[-1]:
                raise ValueError("Incident zone rings must be closed")
    return geometry


ZoneGeometry = Annotated[dict, AfterValidator(_validate_zone_geometry)]


class User(BaseModel):
    id: int
    username: str
    full_name: str
    role: Role
    email: str | None = None
    is_active: bool = True


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")
    full_name: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=8, max_length=128)
    role: Role = "viewer"
    email: str | None = None


class AuthResponse(TokenPair):
    user: User


class HouseholdBase(BaseModel):
    household_no: str
    head_name: str
    address: str
    barangay: str
    size: int = Field(..., ge=1)
    children_count: int = 0
    elderly_count: int = 0
    pwd_count: int = 0
    contact: str | None = None
    # Optional on input: the API falls back to the barangay centroid so a
    # household always lands somewhere on the map.
    lat: float | None = None
    lng: float | None = None
    notes: str | None = None


class Household(HouseholdBase):
    id: int
    lat: float
    lng: float


class HouseholdCreate(HouseholdBase):
    pass


class HouseholdUpdate(BaseModel):
    household_no: str | None = None
    head_name: str | None = None
    address: str | None = None
    barangay: str | None = None
    size: int | None = Field(None, ge=1)
    children_count: int | None = None
    elderly_count: int | None = None
    pwd_count: int | None = None
    contact: str | None = None
    lat: float | None = None
    lng: float | None = None
    notes: str | None = None


class CenterBase(BaseModel):
    name: str
    barangay: str
    address: str
    capacity: int = Field(..., ge=1)
    current_occupants: int = 0
    facilities: list[str] = Field(default_factory=list)
    contact: str | None = None
    lat: float
    lng: float
    status: CenterStatus = "active"


class EvacuationCenter(CenterBase):
    id: int


class CenterCreate(CenterBase):
    pass


class CenterUpdate(BaseModel):
    name: str | None = None
    barangay: str | None = None
    address: str | None = None
    capacity: int | None = Field(None, ge=1)
    current_occupants: int | None = None
    facilities: list[str] | None = None
    contact: str | None = None
    lat: float | None = None
    lng: float | None = None
    status: CenterStatus | None = None


class ResourceBase(BaseModel):
    name: str
    type: ResourceType
    unit: str
    quantity_on_hand: int = 0
    threshold: int = 0
    expiry: str | None = None
    stored_in: str | None = None
    updated_at: str | None = None


class Resource(ResourceBase):
    id: int


class ResourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: ResourceType
    unit: str = Field(min_length=1, max_length=40)
    quantity_on_hand: int = Field(default=0, ge=0)
    threshold: int = Field(default=0, ge=0)
    expiry: str | None = None
    stored_in: str | None = None


class ResourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    unit: str | None = Field(default=None, min_length=1, max_length=40)
    threshold: int | None = Field(default=None, ge=0)
    expiry: str | None = None
    stored_in: str | None = None


class ResourceAdjustment(BaseModel):
    resource_id: int
    delta: int
    reason: str | None = None
    note: str | None = None


class ResourceSummary(BaseModel):
    type: ResourceType
    label: str
    total_on_hand: int
    total_required: int
    gap: int
    low_stock_count: int


class IncidentBase(BaseModel):
    title: str
    type: IncidentType
    barangay: str
    severity: IncidentSeverity
    status: IncidentStatus = "reported"
    description: str | None = None
    lat: float | None = None
    lng: float | None = None
    zone_geojson: ZoneGeometry | None = None
    affected_households: int | None = None
    reported_by: str | None = None


class Incident(IncidentBase):
    id: int
    reported_at: str
    updated_at: str
    zone_geojson: dict | None = None


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    title: str | None = None
    type: IncidentType | None = None
    barangay: str | None = None
    severity: IncidentSeverity | None = None
    status: IncidentStatus | None = None
    description: str | None = None
    lat: float | None = None
    lng: float | None = None
    zone_geojson: ZoneGeometry | None = None


class IncidentZoneSave(BaseModel):
    incident_id: int = Field(gt=0)
    geometry: ZoneGeometry
    affected_households: int | None = None
    reported_by: str | None = None


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus


class EvacuationAssignment(BaseModel):
    id: int
    household_id: int
    household_no: str
    household_head: str
    barangay: str
    center_id: int
    center_name: str
    center_load_percent: int
    assigned_at: str


class CenterLoad(BaseModel):
    center_id: int
    center_name: str
    barangay: str
    capacity: int
    occupants: int
    load_percent: int
    status: Literal["ok", "near_capacity", "full", "overflow"]


class OverflowEntry(BaseModel):
    household_id: int
    household_no: str
    head_name: str
    barangay: str
    reason: str


class AllocationResult(BaseModel):
    request_id: str
    generated_at: str
    total_households: int
    assigned_households: int
    overflow_households: int
    assignments: list[EvacuationAssignment]
    center_loads: list[CenterLoad]
    overflow: list[OverflowEntry]
    coverage_gaps: list[str]


class ResourceNeed(BaseModel):
    resource_id: int
    name: str
    current: int
    required: int
    deficit: int
    unit: str
    status: Literal["adequate", "shortage", "critical"]


class ScenarioReport(BaseModel):
    scenario: dict
    allocation: AllocationResult
    resource_needs: list[ResourceNeed]


class DashboardStats(BaseModel):
    households: int
    vulnerable_members: int
    active_incidents: int
    critical_incidents: int
    centers: int
    available_capacity: int
    low_stock_resources: int
    assigned_households: int


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
