from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.database import get_db
from backend.app.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=schemas.DashboardSummary)
def dashboard(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    today = date.today()
    month_prefix = today.strftime("%Y-%m")

    moradores_query = db.query(models.Morador)
    boletos_query = db.query(models.Boleto)
    contratos_query = db.query(models.Contrato)
    avisos_query = db.query(models.Aviso)
    ocorrencias_query = db.query(models.Ocorrencia)
    lancamentos_query = db.query(models.LancamentoFinanceiro)

    if current_user.role == "morador":
        morador = db.query(models.Morador).filter(models.Morador.user_id == current_user.id).first()
        morador_id = morador.id if morador else 0
        moradores_query = moradores_query.filter(models.Morador.id == morador_id)
        boletos_query = boletos_query.filter(models.Boleto.morador_id == morador_id)
        contratos_query = contratos_query.filter(models.Contrato.morador_id == morador_id)
        avisos_query = avisos_query.filter(models.Aviso.status == "publicado")
        ocorrencias_query = ocorrencias_query.filter(models.Ocorrencia.morador_id == morador_id)
        lancamentos_query = lancamentos_query.filter(models.LancamentoFinanceiro.id == 0)

    receitas_mes = (
        lancamentos_query.filter(models.LancamentoFinanceiro.tipo == "receita")
        .filter(func.strftime("%Y-%m", models.LancamentoFinanceiro.data) == month_prefix)
        .with_entities(func.coalesce(func.sum(models.LancamentoFinanceiro.valor), 0))
        .scalar()
        or 0
    )
    despesas_mes = (
        lancamentos_query.filter(models.LancamentoFinanceiro.tipo == "despesa")
        .filter(func.strftime("%Y-%m", models.LancamentoFinanceiro.data) == month_prefix)
        .with_entities(func.coalesce(func.sum(models.LancamentoFinanceiro.valor), 0))
        .scalar()
        or 0
    )

    financeiro_por_mes = []
    for row in (
        lancamentos_query.with_entities(
            func.strftime("%Y-%m", models.LancamentoFinanceiro.data).label("mes"),
            models.LancamentoFinanceiro.tipo,
            func.coalesce(func.sum(models.LancamentoFinanceiro.valor), 0).label("total"),
        )
        .group_by("mes", models.LancamentoFinanceiro.tipo)
        .order_by("mes")
        .all()
    ):
        financeiro_por_mes.append({"mes": row.mes, "tipo": row.tipo, "total": float(row.total or 0)})

    boletos_por_status = [
        {"status": status, "total": total}
        for status, total in boletos_query.with_entities(models.Boleto.status, func.count(models.Boleto.id))
        .group_by(models.Boleto.status)
        .all()
    ]

    avisos = avisos_query.order_by(models.Aviso.criado_em.desc()).limit(5).all()
    return {
        "moradores": moradores_query.count(),
        "imoveis": db.query(models.Imovel).count() if current_user.role == "proprietario" else contratos_query.count(),
        "boletos_pendentes": boletos_query.filter(models.Boleto.status == "pendente").count(),
        "boletos_pagos": boletos_query.filter(models.Boleto.status == "pago").count(),
        "alugueis_ativos": contratos_query.filter(models.Contrato.status == "ativo").count(),
        "avisos_recentes": avisos_query.count(),
        "ocorrencias_abertas": ocorrencias_query.filter(models.Ocorrencia.status == "aberta").count(),
        "receitas_mes": float(receitas_mes),
        "despesas_mes": float(despesas_mes),
        "saldo_mes": float(receitas_mes - despesas_mes),
        "financeiro_por_mes": financeiro_por_mes,
        "boletos_por_status": boletos_por_status,
        "avisos": avisos,
    }
