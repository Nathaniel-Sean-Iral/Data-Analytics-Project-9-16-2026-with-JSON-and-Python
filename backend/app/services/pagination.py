from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 200


class PageParams(BaseModel):
    """Query-string parameters shared by every list endpoint."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
    sort: str | None = None
    order: str = Field(default="asc", pattern="^(asc|desc)$")
    search: str | None = Field(default=None, max_length=120)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def resolve_sort(sort: str | None, sortable: Sequence[str]) -> str:
    """Return the sort column actually used, falling back to the primary key."""
    return sort if sort in sortable else "id"


def apply_sort_and_search(
    query,
    model,
    params: PageParams,
    searchable: Sequence[str],
    sortable: Sequence[str],
):
    """Apply search, sort, and ordering to a SQLAlchemy query.

    An unrecognised ``sort`` falls back to the primary key rather than raising, so a
    stale bookmark can never 500 the endpoint.
    """
    if params.search:
        from sqlalchemy import or_

        term = f"%{params.search.strip()}%"
        clauses = [getattr(model, column).ilike(term) for column in searchable if hasattr(model, column)]
        if clauses:
            query = query.filter(or_(*clauses))

    order_column = getattr(model, resolve_sort(params.sort, sortable), model.id)
    return query.order_by(order_column.desc() if params.order == "desc" else order_column.asc())


def build_page(items: list[Any], total: int, params: PageParams, sortable: Sequence[str] = ()) -> dict[str, Any]:
    pages = -(-total // params.page_size) if params.page_size else 0
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "pages": pages,
        "sort": resolve_sort(params.sort, sortable),
        "order": params.order,
    }
