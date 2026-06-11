from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.audit import write_audit
from backend.app.core.database import get_db
from backend.app.core.property_access import ensure_property_access
from backend.app.dependencies import ROLE_MORADOR, ROLE_PROPRIETARIO, current_morador, get_current_user, require_roles
from backend.app.routers.common import apply_filters, apply_order, get_or_404, page_response, set_fields

router = APIRouter(prefix="/contratos", tags=["Contratos"])


def _contrato_query_for_user(db: Session, user: models.User):
    query = db.query(models.Contrato)
    if user.role == ROLE_MORADOR:
        morador = current_morador(db, user)
        query = query.filter(models.Contrato.morador_id == morador.id)
    return query


@router.get("")
def list_contratos(
    status_filter: str | None = Query(None, alias="status"),
    morador_id: int | None = None,
    imovel_id: int | None = None,
    property_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = "id",
    order: str = "desc",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _contrato_query_for_user(db, current_user)
    if property_id is not None:
        ensure_property_access(db, current_user, property_id)
        query = query.filter(models.Contrato.imovel_id == property_id)
    query = apply_filters(query, models.Contrato, {"status": status_filter, "morador_id": morador_id, "imovel_id": imovel_id})
    query = apply_order(query, models.Contrato, order_by, order)
    return page_response(query, page, page_size)


@router.post("", response_model=schemas.ContratoRead, status_code=status.HTTP_201_CREATED)
def create_contrato(
    payload: schemas.ContratoCreate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    ensure_property_access(db, current_user, payload.imovel_id)
    item = models.Contrato(**payload.model_dump())
    db.add(item)
    imovel = db.get(models.Imovel, payload.imovel_id)
    if imovel:
        imovel.status = "alugado"
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "criar", "contratos", item.id, request=request)
    return item


@router.get("/{item_id}", response_model=schemas.ContratoRead)
def get_contrato(item_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_or_404(db, models.Contrato, item_id)
    ensure_property_access(db, current_user, item.imovel_id)
    if current_user.role == ROLE_MORADOR and item.morador_id != current_morador(db, current_user).id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Contrato fora do seu vínculo.")
    return item


@router.put("/{item_id}", response_model=schemas.ContratoRead)
def update_contrato(
    item_id: int,
    payload: schemas.ContratoUpdate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Contrato, item_id)
    ensure_property_access(db, current_user, item.imovel_id)
    set_fields(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "atualizar", "contratos", item.id, request=request)
    return item


@router.post("/{item_id}/renovar", response_model=schemas.ContratoRead)
def renovar_contrato(
    item_id: int,
    fim: date,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Contrato, item_id)
    ensure_property_access(db, current_user, item.imovel_id)
    if fim <= item.fim:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nova vigência deve ser posterior à atual.")
    item.fim = fim
    item.status = "ativo"
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "renovar", "contratos", item.id, {"fim": str(fim)}, request=request)
    return item


@router.post("/{item_id}/encerrar", response_model=schemas.ContratoRead)
def encerrar_contrato(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Contrato, item_id)
    ensure_property_access(db, current_user, item.imovel_id)
    item.status = "encerrado"
    item.encerrado_em = date.today()
    if item.imovel:
        item.imovel.status = "disponivel"
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "encerrar", "contratos", item.id, request=request)
    return item


@router.post("/{item_id}/reajustar", response_model=schemas.ContratoRead)
def reajustar_contrato(
    item_id: int,
    percentual: float,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Contrato, item_id)
    ensure_property_access(db, current_user, item.imovel_id)
    item.valor_aluguel = round(item.valor_aluguel * (1 + percentual / 100), 2)
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "reajustar", "contratos", item.id, {"percentual": percentual}, request=request)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contrato(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Contrato, item_id)
    ensure_property_access(db, current_user, item.imovel_id)
    db.delete(item)
    db.commit()
    write_audit(db, current_user, "excluir", "contratos", item_id, request=request)
    return None
