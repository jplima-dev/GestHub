from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.audit import write_audit
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.property_access import ensure_property_access
from backend.app.dependencies import ROLE_MORADOR, ROLE_PROPRIETARIO, current_morador, get_current_user, require_roles
from backend.app.routers.common import apply_filters, apply_order, apply_search, get_or_404, page_response, set_fields

router = APIRouter(prefix="/boletos", tags=["Boletos"])


def _boleto_query_for_user(db: Session, user: models.User):
    query = db.query(models.Boleto)
    if user.role == ROLE_MORADOR:
        morador = current_morador(db, user)
        query = query.filter(models.Boleto.morador_id == morador.id)
    return query


@router.get("")
def list_boletos(
    search: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    morador_id: int | None = None,
    property_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = "vencimento",
    order: str = "desc",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _boleto_query_for_user(db, current_user)
    if property_id is not None:
        ensure_property_access(db, current_user, property_id)
        query = query.filter(models.Boleto.imovel_id == property_id)
    query = apply_search(query, models.Boleto, search, ["numero", "linha_digitavel"])
    query = apply_filters(query, models.Boleto, {"status": status_filter, "morador_id": morador_id})
    query = apply_order(query, models.Boleto, order_by, order)
    return page_response(query, page, page_size)


@router.post("", response_model=schemas.BoletoRead, status_code=status.HTTP_201_CREATED)
def create_boleto(
    payload: schemas.BoletoCreate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    ensure_property_access(db, current_user, payload.imovel_id)
    item = models.Boleto(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "criar", "boletos", item.id, request=request)
    return item


@router.get("/{item_id}", response_model=schemas.BoletoRead)
def get_boleto(item_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_or_404(db, models.Boleto, item_id)
    ensure_property_access(db, current_user, item.imovel_id)
    if current_user.role == ROLE_MORADOR and item.morador_id != current_morador(db, current_user).id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Boleto fora do seu vínculo.")
    return item


@router.put("/{item_id}", response_model=schemas.BoletoRead)
def update_boleto(
    item_id: int,
    payload: schemas.BoletoUpdate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Boleto, item_id)
    ensure_property_access(db, current_user, item.imovel_id)
    set_fields(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "atualizar", "boletos", item.id, request=request)
    return item


@router.post("/{item_id}/pagar", response_model=schemas.BoletoRead)
def pagar_boleto(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Boleto, item_id)
    ensure_property_access(db, current_user, item.imovel_id)
    if current_user.role == ROLE_MORADOR and item.morador_id != current_morador(db, current_user).id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Boleto fora do seu vínculo.")
    item.status = "pago"
    item.pago_em = date.today()
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "pagar", "boletos", item.id, request=request)
    return item


@router.post("/{item_id}/cancelar", response_model=schemas.BoletoRead)
def cancelar_boleto(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Boleto, item_id)
    ensure_property_access(db, current_user, item.imovel_id)
    item.status = "cancelado"
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "cancelar", "boletos", item.id, request=request)
    return item


@router.get("/{item_id}/pdf")
def boleto_pdf(item_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_boleto(item_id, current_user, db)
    pdf_dir = settings.upload_dir / "boletos"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"boleto-{item.numero}.pdf"
    if not pdf_path.exists():
        _generate_boleto_pdf(pdf_path, item)
        item.pdf_path = str(pdf_path)
        db.commit()
    return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_path.name)


def _generate_boleto_pdf(path: Path, boleto: models.Boleto) -> None:
    doc = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    doc.setTitle(f"Boleto {boleto.numero}")
    doc.setFont("Helvetica-Bold", 18)
    doc.drawString(48, height - 64, "CondoFlow - Boleto de Aluguel")
    doc.setFont("Helvetica", 11)
    lines = [
        f"Número: {boleto.numero}",
        f"Valor: R$ {boleto.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        f"Vencimento: {boleto.vencimento:%d/%m/%Y}",
        f"Status: {boleto.status}",
        f"Linha digitável: {boleto.linha_digitavel or 'Gerada pelo banco emissor'}",
    ]
    y = height - 110
    for line in lines:
        doc.drawString(48, y, line)
        y -= 24
    doc.line(48, y - 8, width - 48, y - 8)
    doc.drawString(48, y - 40, "Documento demonstrativo gerado pelo sistema.")
    doc.save()


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_boleto(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Boleto, item_id)
    ensure_property_access(db, current_user, item.imovel_id)
    db.delete(item)
    db.commit()
    write_audit(db, current_user, "excluir", "boletos", item_id, request=request)
    return None
