from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.audit import write_audit
from backend.app.core.database import get_db
from backend.app.core.property_access import ensure_property_access
from backend.app.dependencies import ROLE_MORADOR, ROLE_PROPRIETARIO, current_morador, get_current_user, require_roles
from backend.app.routers.common import apply_filters, apply_order, get_or_404, page_response, set_fields

router = APIRouter(prefix="/alugueis", tags=["Aluguel"])


@router.get("")
def list_alugueis(
    status_filter: str | None = Query(None, alias="status"),
    contrato_id: int | None = None,
    property_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = "vencimento",
    order: str = "desc",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Aluguel)
    if current_user.role == ROLE_MORADOR:
        morador = current_morador(db, current_user)
        query = query.join(models.Contrato).filter(models.Contrato.morador_id == morador.id)
    if property_id is not None:
        ensure_property_access(db, current_user, property_id)
        if current_user.role == ROLE_MORADOR:
            query = query.filter(models.Contrato.imovel_id == property_id)
        else:
            query = query.join(models.Contrato).filter(models.Contrato.imovel_id == property_id)
    query = apply_filters(query, models.Aluguel, {"status": status_filter, "contrato_id": contrato_id})
    query = apply_order(query, models.Aluguel, order_by, order)
    return page_response(query, page, page_size)


@router.post("", response_model=schemas.AluguelRead, status_code=status.HTTP_201_CREATED)
def create_aluguel(
    payload: schemas.AluguelCreate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    contrato = get_or_404(db, models.Contrato, payload.contrato_id)
    ensure_property_access(db, current_user, contrato.imovel_id)
    item = models.Aluguel(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "criar", "alugueis", item.id, request=request)
    return item


@router.get("/{item_id}", response_model=schemas.AluguelRead)
def get_aluguel(item_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_or_404(db, models.Aluguel, item_id)
    ensure_property_access(db, current_user, item.contrato.imovel_id)
    if current_user.role == ROLE_MORADOR and item.contrato.morador_id != current_morador(db, current_user).id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aluguel fora do seu vínculo.")
    return item


@router.put("/{item_id}", response_model=schemas.AluguelRead)
def update_aluguel(
    item_id: int,
    payload: schemas.AluguelUpdate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Aluguel, item_id)
    ensure_property_access(db, current_user, item.contrato.imovel_id)
    set_fields(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "atualizar", "alugueis", item.id, request=request)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_aluguel(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Aluguel, item_id)
    ensure_property_access(db, current_user, item.contrato.imovel_id)
    db.delete(item)
    db.commit()
    write_audit(db, current_user, "excluir", "alugueis", item_id, request=request)
    return None
