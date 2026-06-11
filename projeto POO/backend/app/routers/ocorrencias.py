from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.audit import write_audit
from backend.app.core.database import get_db
from backend.app.core.property_access import ensure_property_access
from backend.app.dependencies import ROLE_MORADOR, ROLE_PROPRIETARIO, current_morador, get_current_user
from backend.app.routers.common import apply_filters, apply_order, apply_search, get_or_404, page_response, set_fields

router = APIRouter(prefix="/ocorrencias", tags=["Ocorrências"])


@router.get("")
def list_ocorrencias(
    search: str | None = None,
    tipo: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    prioridade: str | None = None,
    property_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = "criado_em",
    order: str = "desc",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Ocorrencia)
    if current_user.role == ROLE_MORADOR:
        morador = current_morador(db, current_user)
        query = query.filter(models.Ocorrencia.morador_id == morador.id)
    if property_id is not None:
        ensure_property_access(db, current_user, property_id)
        query = query.filter(models.Ocorrencia.imovel_id == property_id)
    query = apply_search(query, models.Ocorrencia, search, ["titulo", "descricao"])
    query = apply_filters(query, models.Ocorrencia, {"tipo": tipo, "status": status_filter, "prioridade": prioridade})
    query = apply_order(query, models.Ocorrencia, order_by, order)
    return page_response(query, page, page_size)


@router.post("", response_model=schemas.OcorrenciaRead, status_code=status.HTTP_201_CREATED)
def create_ocorrencia(
    payload: schemas.OcorrenciaCreate,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump()
    if current_user.role == ROLE_MORADOR:
        morador = current_morador(db, current_user)
        data["morador_id"] = morador.id
    elif not data.get("morador_id"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe o morador da ocorrência.")
    if data.get("imovel_id") is not None:
        ensure_property_access(db, current_user, data["imovel_id"])
    item = models.Ocorrencia(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "criar", "ocorrencias", item.id, request=request)
    return item


@router.get("/{item_id}", response_model=schemas.OcorrenciaRead)
def get_ocorrencia(item_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_or_404(db, models.Ocorrencia, item_id)
    if item.imovel_id is not None:
        ensure_property_access(db, current_user, item.imovel_id)
    if current_user.role == ROLE_MORADOR and item.morador_id != current_morador(db, current_user).id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ocorrência fora do seu vínculo.")
    return item


@router.put("/{item_id}", response_model=schemas.OcorrenciaRead)
def update_ocorrencia(
    item_id: int,
    payload: schemas.OcorrenciaUpdate,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Ocorrencia, item_id)
    if item.imovel_id is not None:
        ensure_property_access(db, current_user, item.imovel_id)
    data = payload.model_dump(exclude_unset=True)
    if current_user.role == ROLE_MORADOR:
        if item.morador_id != current_morador(db, current_user).id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ocorrência fora do seu vínculo.")
        data = {key: data[key] for key in data.keys() & {"titulo", "descricao", "tipo"}}
    set_fields(item, data)
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "atualizar", "ocorrencias", item.id, request=request)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ocorrencia(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Ocorrencia, item_id)
    if item.imovel_id is not None:
        ensure_property_access(db, current_user, item.imovel_id)
    if current_user.role == ROLE_MORADOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Somente proprietários excluem ocorrências.")
    db.delete(item)
    db.commit()
    write_audit(db, current_user, "excluir", "ocorrencias", item_id, request=request)
    return None
