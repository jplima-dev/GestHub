from __future__ import annotations

import csv
from io import BytesIO, StringIO
from pathlib import Path
from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from backend.app import models
from backend.app.core.database import get_db
from backend.app.dependencies import ROLE_PROPRIETARIO, require_roles

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])

REPORTS = {
    "moradores": (models.Morador, ["id", "nome", "email", "cpf", "telefone", "status"]),
    "boletos": (models.Boleto, ["id", "numero", "valor", "vencimento", "status", "pago_em"]),
    "financeiro": (models.LancamentoFinanceiro, ["id", "tipo", "categoria", "descricao", "valor", "data", "status"]),
    "contratos": (models.Contrato, ["id", "imovel_id", "morador_id", "inicio", "fim", "valor_aluguel", "status"]),
    "ocorrencias": (models.Ocorrencia, ["id", "titulo", "tipo", "status", "prioridade", "criado_em"]),
}


@router.get("/{tipo}")
def export_report(
    tipo: str,
    formato: str = Query("csv", pattern="^(csv|xlsx|pdf)$"),
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    if tipo not in REPORTS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relatório não disponível.")
    model, fields = REPORTS[tipo]
    rows = db.query(model).all()
    data = [[str(getattr(row, field) or "") for field in fields] for row in rows]
    if formato == "csv":
        return _csv_response(tipo, fields, data)
    if formato == "xlsx":
        return _xlsx_response(tipo, fields, data)
    return _pdf_response(tipo, fields, data)


def _csv_response(tipo: str, fields: list[str], rows: list[list[str]]) -> Response:
    stream = StringIO()
    writer = csv.writer(stream, delimiter=";")
    writer.writerow(fields)
    writer.writerows(rows)
    return Response(
        stream.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{tipo}.csv"'},
    )


def _xlsx_response(tipo: str, fields: list[str], rows: list[list[str]]) -> Response:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = tipo[:31]
    sheet.append(fields)
    for row in rows:
        sheet.append(row)
    stream = BytesIO()
    workbook.save(stream)
    return Response(
        stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{tipo}.xlsx"'},
    )


def _pdf_response(tipo: str, fields: list[str], rows: list[list[str]]) -> Response:
    stream = BytesIO()
    doc = canvas.Canvas(stream, pagesize=A4)
    width, height = A4
    doc.setFont("Helvetica-Bold", 16)
    doc.drawString(40, height - 46, f"Relatório: {tipo}")
    y = height - 82
    doc.setFont("Helvetica-Bold", 8)
    doc.drawString(40, y, " | ".join(fields))
    doc.setFont("Helvetica", 8)
    y -= 18
    for row in rows:
        if y < 42:
            doc.showPage()
            y = height - 46
            doc.setFont("Helvetica", 8)
        line = " | ".join(row)
        doc.drawString(40, y, line[:150])
        y -= 14
    doc.save()
    return Response(
        stream.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{tipo}.pdf"'},
    )

