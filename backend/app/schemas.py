from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Role = Literal["admin", "responder", "viewer"]
IncidentType = Literal["flood", "fire", "earthquake", "landslide", "typhoon", "other"]
IncidentSeverity = Literal["low", "moderate", "high", "critical"]
IncidentStatus = Literal["reported", "assessing", "responding", "resolved"]
CenterStatus = Literal["active", "standby", "closed"]
ResourceType = Literal["rice", "water", "medicine", "blankets", "hygiene", "canned_goods", "clothing", "mats", "tents", "other"]


class User(BaseModel):
    id: int
    username: str
    full_name: str
    role: Role
    email: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
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
    contact: str
    lat: float
    lng: float
    notes: Optional[str] = None


class Household(HouseholdBase):
    id: int


class HouseholdCreate(HouseholdBase):
    pass


class HouseholdUpdate(BaseModel):
    household_no: Optional[str] = None
    head_name: Optional[str] = None
    address: Optional[str] = None
    barangay: Optional[str] = None
    size: Optional[int] = Field(None, ge=1)
    children_count: Optional[int] = None
    elderly_count: Optional[int] = None
    pwd_count: Optional[int] = None
    contact: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    notes: Optional[str] = None


class CenterBase(BaseModel):
    name: str
    barangay: str
    address: str
    capacity: int = Field(..., ge=1)
    current_occupants: int = 0
    facilities: list[str] = Field(default_factory=list)
    contact: Optional[str] = None
    lat: float
    lng: float
    status: CenterStatus = "active"


class EvacuationCenter(CenterBase):
    id: int


class CenterCreate(CenterBase):
    pass


class CenterUpdate(BaseModel):
    name: Optional[str] = None
    barangay: Optional[str] = None
    address: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=1)
    current_occupants: Optional[int] = None
    facilities: Optional[list[str]] = None
    contact: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    status: Optional[CenterStatus] = None


class ResourceBase(BaseModel):
    name: str
    type: ResourceType
    unit: str
    quantity_on_hand: int = 0
    threshold: int = 0
    expiry: Optional[str] = None
    stored_in: Optional[str] = None
    updated_at: Optional[str] = None


class Resource(ResourceBase):
    id: int


class ResourceAdjustment(BaseModel):
    resource_id: int
    delta: int
    reason: Optional[str] = None


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
    description: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    affected_households: Optional[int] = None
    reported_by: Optional[str] = None


class Incident(IncidentBase):
    id: int
    reported_at: str
    updated_at: str


class IncidentCreate(IncidentBase):
    pass


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
