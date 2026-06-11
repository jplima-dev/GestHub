from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.audit import write_audit
from backend.app.core.database import get_db
from backend.app.core.property_access import accessible_property_ids, add_property_membership, ensure_property_access
from backend.app.dependencies import ROLE_MORADOR, ROLE_PROPRIETARIO, current_morador, get_current_user, require_roles
from backend.app.routers.common import apply_filters, apply_order, apply_search, get_or_404, page_response, set_fields

router = APIRouter(prefix="/imoveis", tags=["Imóveis"])


@router.get("")
def list_imoveis(
    search: str | None = None,
    tipo: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    property_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = "id",
    order: str = "desc",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Imovel)
    ids = accessible_property_ids(db, current_user)
    if property_id is not None:
        ids = [ensure_property_access(db, current_user, property_id)]
    query = query.filter(models.Imovel.id.in_(ids)) if ids else query.filter(models.Imovel.id == 0)
    query = apply_search(query, models.Imovel, search, ["titulo", "endereco", "cidade", "descricao"])
    query = apply_filters(query, models.Imovel, {"tipo": tipo, "status": status_filter})
    query = apply_order(query, models.Imovel, order_by, order)
    return page_response(query, page, page_size)


@router.post("", response_model=schemas.ImovelRead, status_code=status.HTTP_201_CREATED)
def create_imovel(
    payload: schemas.ImovelCreate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = models.Imovel(**payload.model_dump())
    db.add(item)
    db.flush()
    add_property_membership(db, current_user, item.id, "admin")
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "criar", "imoveis", item.id, request=request)
    return item


@router.get("/{item_id}", response_model=schemas.ImovelRead)
def get_imovel(item_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_or_404(db, models.Imovel, item_id)
    ensure_property_access(db, current_user, item.id)
    return item


@router.put("/{item_id}", response_model=schemas.ImovelRead)
def update_imovel(
    item_id: int,
    payload: schemas.ImovelUpdate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Imovel, item_id)
    ensure_property_access(db, current_user, item.id)
    set_fields(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "atualizar", "imoveis", item.id, request=request)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_imovel(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Imovel, item_id)
    ensure_property_access(db, current_user, item.id)
    db.delete(item)
    db.commit()
    write_audit(db, current_user, "excluir", "imoveis", item_id, request=request)
    return None
