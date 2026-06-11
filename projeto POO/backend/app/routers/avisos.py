from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.audit import write_audit
from backend.app.core.database import get_db
from backend.app.core.property_access import ensure_property_access
from backend.app.core.security import now_utc
from backend.app.dependencies import ROLE_MORADOR, ROLE_PROPRIETARIO, current_morador, get_current_user, require_roles
from backend.app.routers.common import apply_filters, apply_order, apply_search, get_or_404, page_response, set_fields

router = APIRouter(prefix="/avisos", tags=["Avisos"])


def _with_read_status(items: list[models.Aviso], db: Session, user: models.User) -> list[dict]:
    encoded = jsonable_encoder(items)
    if user.role != ROLE_MORADOR:
        for item in encoded:
            item["lido"] = False
        return encoded
    morador = current_morador(db, user)
    read_ids = {
        aviso_id
        for (aviso_id,) in db.query(models.AvisoLeitura.aviso_id)
        .filter(models.AvisoLeitura.morador_id == morador.id)
        .all()
    }
    for item in encoded:
        item["lido"] = item["id"] in read_ids
    return encoded


@router.get("")
def list_avisos(
    search: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    categoria: str | None = None,
    property_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = "criado_em",
    order: str = "desc",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Aviso)
    if property_id is not None:
        ensure_property_access(db, current_user, property_id)
        query = query.filter(models.Aviso.imovel_id == property_id)
    if current_user.role == ROLE_MORADOR:
        query = query.filter(models.Aviso.status == "publicado")
    query = apply_search(query, models.Aviso, search, ["titulo", "mensagem", "categoria"])
    query = apply_filters(query, models.Aviso, {"status": status_filter, "categoria": categoria})
    query = apply_order(query, models.Aviso, order_by, order)
    result = page_response(query, page, page_size)
    result["items"] = _with_read_status(query.offset((page - 1) * page_size).limit(page_size).all(), db, current_user)
    return result


@router.post("", response_model=schemas.AvisoRead, status_code=status.HTTP_201_CREATED)
def create_aviso(
    payload: schemas.AvisoCreate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO, ROLE_MORADOR)),
    db: Session = Depends(get_db),
):
    data = payload.model_dump()
    if data.get("imovel_id") is not None:
        ensure_property_access(db, current_user, data["imovel_id"])
    if current_user.role == ROLE_MORADOR:
        data["status"] = "publicado"
    if data.get("status") == "publicado":
        data["publicado_em"] = now_utc()
    item = models.Aviso(autor_id=current_user.id, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "criar", "avisos", item.id, request=request)
    return item


@router.get("/{item_id}", response_model=schemas.AvisoRead)
def get_aviso(item_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_or_404(db, models.Aviso, item_id)
    if item.imovel_id is not None:
        ensure_property_access(db, current_user, item.imovel_id)
    if current_user.role == ROLE_MORADOR and item.status != "publicado":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aviso indisponível.")
    result = jsonable_encoder(item)
    result["lido"] = False
    if current_user.role == ROLE_MORADOR:
        morador = current_morador(db, current_user)
        result["lido"] = (
            db.query(models.AvisoLeitura)
            .filter(models.AvisoLeitura.aviso_id == item.id, models.AvisoLeitura.morador_id == morador.id)
            .first()
            is not None
        )
    return result


@router.put("/{item_id}", response_model=schemas.AvisoRead)
def update_aviso(
    item_id: int,
    payload: schemas.AvisoUpdate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Aviso, item_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("imovel_id") is not None:
        ensure_property_access(db, current_user, data["imovel_id"])
    if data.get("status") == "publicado" and item.status != "publicado":
        data["publicado_em"] = now_utc()
    set_fields(item, data)
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "atualizar", "avisos", item.id, request=request)
    return item


@router.post("/{item_id}/publicar", response_model=schemas.AvisoRead)
def publicar_aviso(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Aviso, item_id)
    item.status = "publicado"
    item.publicado_em = now_utc()
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "publicar", "avisos", item.id, request=request)
    return item


@router.post("/{item_id}/arquivar", response_model=schemas.AvisoRead)
def arquivar_aviso(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Aviso, item_id)
    item.status = "arquivado"
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "arquivar", "avisos", item.id, request=request)
    return item


@router.post("/{item_id}/lido", status_code=status.HTTP_204_NO_CONTENT)
def marcar_lido(
    item_id: int,
    current_user: models.User = Depends(require_roles(ROLE_MORADOR)),
    db: Session = Depends(get_db),
):
    aviso = get_or_404(db, models.Aviso, item_id)
    if aviso.status != "publicado":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aviso indisponível.")
    morador = current_morador(db, current_user)
    exists = db.query(models.AvisoLeitura).filter_by(aviso_id=item_id, morador_id=morador.id).first()
    if not exists:
        db.add(models.AvisoLeitura(aviso_id=item_id, morador_id=morador.id))
        db.commit()
    return None


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_aviso(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Aviso, item_id)
    db.delete(item)
    db.commit()
    write_audit(db, current_user, "excluir", "avisos", item_id, request=request)
    return None
