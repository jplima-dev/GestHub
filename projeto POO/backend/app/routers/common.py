from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_
from sqlalchemy.orm import Query as SAQuery, Session


def pagination_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> tuple[int, int]:
    return page, page_size


def apply_search(query: SAQuery, model: type, search: str | None, fields: list[str]) -> SAQuery:
    if not search:
        return query
    clauses = []
    for field_name in fields:
        field = getattr(model, field_name, None)
        if field is not None:
            clauses.append(field.ilike(f"%{search}%"))
    return query.filter(or_(*clauses)) if clauses else query


def apply_filters(query: SAQuery, model: type, filters: dict[str, Any]) -> SAQuery:
    for field_name, value in filters.items():
        if value is None or value == "":
            continue
        field = getattr(model, field_name, None)
        if field is not None:
            query = query.filter(field == value)
    return query


def apply_order(query: SAQuery, model: type, order_by: str | None, order: str | None) -> SAQuery:
    field = getattr(model, order_by or "id", None)
    if field is None:
        field = getattr(model, "id")
    return query.order_by(field.asc() if order == "asc" else field.desc())


def page_response(query: SAQuery, page: int, page_size: int) -> dict[str, Any]:
    total = query.order_by(None).count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return jsonable_encoder({"items": items, "total": total, "page": page, "page_size": page_size})


def get_or_404(db: Session, model: type, item_id: int, message: str = "Registro não encontrado."):
    item = db.get(model, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    return item


def set_fields(instance: Any, data: dict[str, Any]) -> Any:
    for field, value in data.items():
        setattr(instance, field, value)
    return instance

