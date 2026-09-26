from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.household import Household
from app.schemas.schemas import (
    HouseholdCreate,
    HouseholdOut,
    HouseholdUpdate,
    Paginated,
)

router = APIRouter(prefix="/households", tags=["households"])

SORTABLE = {"household_no", "head_name", "barangay", "size"}


@router.get("", response_model=Paginated[HouseholdOut])
def list_households(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: str = Query("", max_length=200),
    sort: str = Query("household_no"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    barangay: str | None = Query(None),
    db: Session = Depends(get_db),
    _: Household = Depends(require_roles("viewer", "responder", "admin")),
):
    query = db.query(Household)
    if barangay:
        query = query.filter(Household.barangay == barangay)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Household.household_no.ilike(like),
                Household.head_name.ilike(like),
                Household.address.ilike(like),
                Household.barangay.ilike(like),
            )
        )

    total = query.count()
    col = getattr(Household, sort if sort in SORTABLE else "household_no")
    query = query.order_by(col.asc() if order == "asc" else col.desc())
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return Paginated(items=items, total=total, page=page, page_size=page_size)


@router.get("/{household_id}", response_model=HouseholdOut)
def get_household(
    household_id: int,
    db: Session = Depends(get_db),
    _: Household = Depends(require_roles("viewer", "responder", "admin")),
):
    household = db.get(Household, household_id)
    if household is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    return household


@router.post("", response_model=HouseholdOut, status_code=status.HTTP_201_CREATED)
def create_household(
    body: HouseholdCreate,
    db: Session = Depends(get_db),
    _: Household = Depends(require_roles("admin")),
):
    existing = db.query(Household).filter(Household.household_no == body.household_no).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Household number already exists")
    household = Household(**body.model_dump())
    db.add(household)
    db.commit()
    db.refresh(household)
    return household


@router.put("/{household_id}", response_model=HouseholdOut)
def update_household(
    household_id: int,
    body: HouseholdUpdate,
    db: Session = Depends(get_db),
    _: Household = Depends(require_roles("admin")),
):
    household = db.get(Household, household_id)
    if household is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    payload = body.model_dump(exclude_unset=True)
    if "household_no" in payload and payload["household_no"] != household.household_no:
        existing = db.query(Household).filter(Household.household_no == payload["household_no"]).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Household number already exists")
    for key, value in payload.items():
        setattr(household, key, value)
    db.commit()
    db.refresh(household)
    return household


@router.delete("/{household_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_household(
    household_id: int,
    db: Session = Depends(get_db),
    _: Household = Depends(require_roles("admin")),
):
    household = db.get(Household, household_id)
    if household is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    db.delete(household)
    db.commit()