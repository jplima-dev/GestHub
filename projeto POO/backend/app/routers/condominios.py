from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.audit import write_audit
from backend.app.core.database import get_db
from backend.app.dependencies import ROLE_PROPRIETARIO, get_current_user, require_roles
from backend.app.routers.common import apply_filters, apply_order, apply_search, get_or_404, page_response, set_fields

router = APIRouter(prefix="/condominios", tags=["Condomínios"])


@router.get("")
def list_condominios(
    search: str | None = None,
    ativo: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = "id",
    order: str = "desc",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Condominio)
    query = apply_search(query, models.Condominio, search, ["nome", "cnpj", "cidade", "endereco"])
    query = apply_filters(query, models.Condominio, {"ativo": ativo})
    query = apply_order(query, models.Condominio, order_by, order)
    return page_response(query, page, page_size)


@router.post("", response_model=schemas.CondominioRead, status_code=status.HTTP_201_CREATED)
def create_condominio(
    payload: schemas.CondominioCreate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = models.Condominio(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "criar", "condominios", item.id, request=request)
    return item


@router.get("/{item_id}", response_model=schemas.CondominioRead)
def get_condominio(item_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_or_404(db, models.Condominio, item_id)


@router.put("/{item_id}", response_model=schemas.CondominioRead)
def update_condominio(
    item_id: int,
    payload: schemas.CondominioUpdate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Condominio, item_id)
    set_fields(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "atualizar", "condominios", item.id, request=request)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_condominio(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Condominio, item_id)
    db.delete(item)
    db.commit()
    write_audit(db, current_user, "excluir", "condominios", item_id, request=request)
    return None


@router.post("/{condominio_id}/blocos", response_model=schemas.BlocoRead, status_code=status.HTTP_201_CREATED)
def create_bloco(
    condominio_id: int,
    payload: schemas.BlocoCreate,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    get_or_404(db, models.Condominio, condominio_id)
    item = models.Bloco(**payload.model_dump())
    item.condominio_id = condominio_id
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{condominio_id}/unidades")
def list_unidades(
    condominio_id: int,
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Unidade).filter(models.Unidade.condominio_id == condominio_id)
    query = apply_filters(query, models.Unidade, {"status": status_filter})
    query = apply_order(query, models.Unidade, "codigo", "asc")
    return page_response(query, page, page_size)


@router.post("/{condominio_id}/unidades", response_model=schemas.UnidadeRead, status_code=status.HTTP_201_CREATED)
def create_unidade(
    condominio_id: int,
    payload: schemas.UnidadeCreate,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    get_or_404(db, models.Condominio, condominio_id)
    item = models.Unidade(**payload.model_dump())
    item.condominio_id = condominio_id
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/unidades/{unidade_id}", response_model=schemas.UnidadeRead)
def update_unidade(
    unidade_id: int,
    payload: schemas.UnidadeUpdate,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Unidade, unidade_id)
    set_fields(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    return item

