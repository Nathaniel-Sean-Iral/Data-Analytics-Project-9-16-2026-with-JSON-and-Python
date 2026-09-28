from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

# ------------------------------ Generic ----------------------------------


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


# ------------------------------ Auth / Users -----------------------------


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    email: str | None = None
    role: Literal["admin", "responder", "viewer"]


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ------------------------------ Households -------------------------------


class HouseholdBase(BaseModel):
    household_no: str = Field(min_length=1, max_length=40)
    head_name: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=1, max_length=255)
    barangay: str = Field(min_length=1, max_length=80)
    size: int = Field(ge=1)
    children_count: int = Field(default=0, ge=0)
    elderly_count: int = Field(default=0, ge=0)
    pwd_count: int = Field(default=0, ge=0)
    contact: str | None = Field(default=None, max_length=40)
    lat: float = Field(default=0.0, ge=-90, le=90)
    lng: float = Field(default=0.0, ge=-180, le=180)
    notes: str | None = Field(default=None, max_length=500)


class HouseholdCreate(HouseholdBase):
    pass


class HouseholdUpdate(BaseModel):
    household_no: str | None = None
    head_name: str | None = None
    address: str | None = None
    barangay: str | None = None
    size: int | None = Field(default=None, ge=1)
    children_count: int | None = Field(default=None, ge=0)
    elderly_count: int | None = Field(default=None, ge=0)
    pwd_count: int | None = Field(default=None, ge=0)
    contact: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    notes: str | None = None


class HouseholdOut(HouseholdBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ------------------------------ Centers ----------------------------------


class CenterBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    barangay: str = Field(min_length=1, max_length=80)
    address: str | None = None
    capacity: int = Field(ge=0)
    current_occupants: int = Field(ge=0)
    facilities: list[str] = Field(default_factory=list)
    contact: str | None = None
    lat: float = Field(default=0.0, ge=-90, le=90)
    lng: float = Field(default=0.0, ge=-180, le=180)
    status: Literal["active", "standby", "closed"] = "standby"


class CenterCreate(CenterBase):
    pass


class CenterUpdate(BaseModel):
    name: str | None = None
    barangay: str | None = None
    address: str | None = None
    capacity: int | None = Field(default=None, ge=0)
    current_occupants: int | None = Field(default=None, ge=0)
    facilities: list[str] | None = None
    contact: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    status: Literal["active", "standby", "closed"] | None = None


class CenterOut(CenterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ------------------------------ Resources --------------------------------


class ResourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    type: str = Field(min_length=1, max_length=40)
    unit: str = Field(default="pc", max_length=40)
    quantity_on_hand: int = Field(ge=0)
    threshold: int = Field(ge=0)
    expiry: datetime | None = None
    stored_in: str | None = None


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    unit: str | None = None
    quantity_on_hand: int | None = Field(default=None, ge=0)
    threshold: int | None = Field(default=None, ge=0)
    expiry: datetime | None = None
    stored_in: str | None = None


class ResourceThresholdUpdate(BaseModel):
    threshold: int = Field(ge=0)


class ResourceOut(ResourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime


class StockAdjustRequest(BaseModel):
    resource_id: int
    delta: int
    reason: str | None = None


class ResourceSummaryOut(BaseModel):
    type: str
    label: str
    total_on_hand: int
    total_required: int
    gap: int
    low_stock_count: int


# ------------------------------ Incidents --------------------------------


class IncidentBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    type: Literal["flood", "fire", "earthquake", "landslide", "typhoon", "other"] = "other"
    barangay: str = Field(min_length=1, max_length=80)
    severity: Literal["low", "moderate", "high", "critical"] = "moderate"
    description: str | None = Field(default=None, max_length=2000)
    lat: float | None = None
    lng: float | None = None
    affected_households: int | None = Field(default=None, ge=0)


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    title: str | None = None
    type: Literal["flood", "fire", "earthquake", "landslide", "typhoon", "other"] | None = None
    barangay: str | None = None
    severity: Literal["low", "moderate", "high", "critical"] | None = None
    status: Literal["reported", "assessing", "responding", "resolved"] | None = None
    description: str | None = None
    lat: float | None = None
    lng: float | None = None
    affected_households: int | None = Field(default=None, ge=0)


class IncidentStatusUpdate(BaseModel):
    status: Literal["reported", "assessing", "responding", "resolved"]


class IncidentOut(IncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: Literal["reported", "assessing", "responding", "resolved"]
    reported_by: str | None = None
    reported_at: datetime
    updated_at: datetime


# --------------------------- Allocation output ---------------------------


class EvacuationAssignmentOut(BaseModel):
    # `id` is the persisted `evacuation_assignments` row id. It is null for
    # assignments produced by the scenario simulator, which is a dry run and
    # never writes rows.
    id: int | None = None
    household_id: int
    household_no: str
    household_head: str
    barangay: str
    center_id: int | None
    center_name: str
    center_load_percent: int
    assigned_at: datetime


class CenterLoadOut(BaseModel):
    center_id: int
    center_name: str
    barangay: str
    capacity: int
    occupants: int
    load_percent: int
    status: Literal["ok", "near_capacity", "full", "overflow"]


class OverflowEntryOut(BaseModel):
    household_id: int
    household_no: str
    head_name: str
    barangay: str
    reason: str


class AllocationResultOut(BaseModel):
    request_id: str
    generated_at: datetime
    total_households: int
    assigned_households: int
    overflow_households: int
    assignments: list[EvacuationAssignmentOut]
    center_loads: list[CenterLoadOut]
    overflow: list[OverflowEntryOut]
    coverage_gaps: list[str]


class AllocationRequest(BaseModel):
    barangay: str | None = None


# ------------------------------- Simulator -------------------------------


class SimulatorRequest(BaseModel):
    barangay: str
    affected_households: int = Field(ge=1)


class ResourceNeedOut(BaseModel):
    resource_id: int
    name: str
    current: int
    required: int
    deficit: int
    unit: str
    status: Literal["adequate", "shortage", "critical"]


class ScenarioReportOut(BaseModel):
    scenario: dict
    allocation: AllocationResultOut
    resource_needs: list[ResourceNeedOut]


# ------------------------------- Dashboard -------------------------------


class DashboardStatsOut(BaseModel):
    households: int
    vulnerable_members: int
    active_incidents: int
    critical_incidents: int
    centers: int
    available_capacity: int
    low_stock_resources: int
    assigned_households: int