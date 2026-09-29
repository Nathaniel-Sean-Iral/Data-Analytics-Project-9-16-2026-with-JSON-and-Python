from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import require_roles
from app.schemas import CenterCreate, CenterUpdate, EvacuationCenter
from app.services.pagination import PageParams
from app.services.store import create_center, delete_center, get_center, get_centers, update_center

router = APIRouter(tags=["centers"])


@router.get("/centers")
def list_centers(
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=200),
    sort: str | None = Query(default=None),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    search: str | None = Query(default=None),
    _user=Depends(require_roles("admin", "responder", "viewer")),
):
    """Returns a plain list unless any pagination or sort parameter is supplied,
    in which case a paginated envelope is returned.
    """
    if page is None and page_size is None and sort is None and search is None:
        return get_centers()
    params = PageParams(page=page or 1, page_size=page_size or 25, sort=sort, order=order, search=search)
    return get_centers(params)


@router.get("/centers/{center_id}")
def get_center_by_id(center_id: int, _user=Depends(require_roles("admin", "responder", "viewer"))):
    center = get_center(center_id)
    if center is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Center not found")
    return center


@router.post("/centers", response_model=EvacuationCenter)
def create_new_center(payload: CenterCreate, _user=Depends(require_roles("admin", "responder"))):
    return create_center(payload.model_dump())


@router.put("/centers/{center_id}", response_model=EvacuationCenter)
def update_existing_center(
    center_id: int,
    payload: CenterUpdate,
    _user=Depends(require_roles("admin", "responder")),
):
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    center = update_center(center_id, updates)
    if center is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Center not found")
    return center


@router.delete("/centers/{center_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_center(center_id: int, _user=Depends(require_roles("admin"))):
    try:
        deleted = delete_center(center_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Center not found")
    return None
