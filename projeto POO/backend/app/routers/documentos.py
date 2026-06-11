from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.audit import write_audit
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.property_access import ensure_property_access
from backend.app.dependencies import ROLE_MORADOR, current_morador, get_current_user
from backend.app.routers.common import apply_filters, apply_order, apply_search, get_or_404, page_response

router = APIRouter(prefix="/documentos", tags=["Documentos"])


def _safe_filename(filename: str) -> str:
    return "".join(ch for ch in filename if ch.isalnum() or ch in {".", "-", "_"}).strip(".") or "arquivo"


def _document_query_for_user(db: Session, user: models.User):
    query = db.query(models.Documento)
    if user.role == ROLE_MORADOR:
        morador = current_morador(db, user)
        contrato_ids = [cid for (cid,) in db.query(models.Contrato.id).filter(models.Contrato.morador_id == morador.id).all()]
        query = query.filter(or_(models.Documento.owner_user_id == user.id, models.Documento.contrato_id.in_(contrato_ids)))
    return query


@router.get("")
def list_documentos(
    search: str | None = None,
    categoria: str | None = None,
    property_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = "criado_em",
    order: str = "desc",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _document_query_for_user(db, current_user)
    if property_id is not None:
        ensure_property_access(db, current_user, property_id)
        query = query.filter(models.Documento.imovel_id == property_id)
    query = apply_search(query, models.Documento, search, ["titulo", "categoria", "file_path"])
    query = apply_filters(query, models.Documento, {"categoria": categoria})
    query = apply_order(query, models.Documento, order_by, order)
    return page_response(query, page, page_size)


@router.post("", response_model=schemas.DocumentoRead, status_code=status.HTTP_201_CREATED)
def upload_documento(
    request: Request,
    titulo: str = Form(...),
    categoria: str = Form("geral"),
    contrato_id: int | None = Form(None),
    imovel_id: int | None = Form(None),
    arquivo: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if imovel_id:
        ensure_property_access(db, current_user, imovel_id)
    if current_user.role == ROLE_MORADOR:
        morador = current_morador(db, current_user)
        if contrato_id:
            contrato = db.get(models.Contrato, contrato_id)
            if not contrato or contrato.morador_id != morador.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Contrato fora do seu vínculo.")
        if imovel_id:
            vinculo = db.query(models.Contrato).filter_by(imovel_id=imovel_id, morador_id=morador.id).first()
            if not vinculo:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Imóvel fora do seu vínculo.")

    upload_dir = settings.upload_dir / "documentos"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = _safe_filename(arquivo.filename or "arquivo")
    target = upload_dir / f"{current_user.id}-{filename}"
    with target.open("wb") as buffer:
        shutil.copyfileobj(arquivo.file, buffer)

    item = models.Documento(
        owner_user_id=current_user.id,
        contrato_id=contrato_id,
        imovel_id=imovel_id,
        titulo=titulo,
        categoria=categoria,
        file_path=str(target),
        mime_type=arquivo.content_type,
        tamanho=target.stat().st_size,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "upload", "documentos", item.id, request=request)
    return item


@router.get("/{item_id}", response_model=schemas.DocumentoRead)
def get_documento(item_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_or_404(db, models.Documento, item_id)
    if current_user.role == ROLE_MORADOR:
        morador = current_morador(db, current_user)
        allowed = item.owner_user_id == current_user.id or (item.contrato and item.contrato.morador_id == morador.id)
        if not allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Documento fora do seu vínculo.")
    return item


@router.get("/{item_id}/download")
def download_documento(item_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_documento(item_id, current_user, db)
    path = Path(item.file_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado no servidor.")
    return FileResponse(path, media_type=item.mime_type or "application/octet-stream", filename=path.name)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_documento(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Documento, item_id)
    if current_user.role == ROLE_MORADOR and item.owner_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Documento fora do seu vínculo.")
    path = Path(item.file_path)
    db.delete(item)
    db.commit()
    if path.exists():
        path.unlink()
    write_audit(db, current_user, "excluir", "documentos", item_id, request=request)
    return None
