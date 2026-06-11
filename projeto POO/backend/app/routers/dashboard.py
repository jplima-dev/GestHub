from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.database import get_db
from backend.app.core.property_access import accessible_property_ids, ensure_property_access
from backend.app.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=schemas.DashboardSummary)
def dashboard(
    property_id: int | None = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    month_prefix = today.strftime("%Y-%m")

    moradores_query = db.query(models.Morador)
    imoveis_query = db.query(models.Imovel)
    boletos_query = db.query(models.Boleto)
    contratos_query = db.query(models.Contrato)
    avisos_query = db.query(models.Aviso)
    ocorrencias_query = db.query(models.Ocorrencia)
    lancamentos_query = db.query(models.LancamentoFinanceiro)

    accessible_ids = accessible_property_ids(db, current_user)
    if property_id is not None:
        property_ids = [ensure_property_access(db, current_user, property_id)]
    else:
        property_ids = accessible_ids

    if property_ids:
        contrato_ids = [
            contrato_id
            for (contrato_id,) in db.query(models.Contrato.id).filter(models.Contrato.imovel_id.in_(property_ids)).all()
        ]
        imoveis_query = imoveis_query.filter(models.Imovel.id.in_(property_ids))
        moradores_query = moradores_query.join(models.Contrato).filter(models.Contrato.imovel_id.in_(property_ids)).distinct()
        boletos_query = boletos_query.filter(models.Boleto.imovel_id.in_(property_ids))
        contratos_query = contratos_query.filter(models.Contrato.imovel_id.in_(property_ids))
        avisos_query = avisos_query.filter(models.Aviso.imovel_id.in_(property_ids))
        ocorrencias_query = ocorrencias_query.filter(models.Ocorrencia.imovel_id.in_(property_ids))
        if contrato_ids:
            lancamentos_query = lancamentos_query.filter(models.LancamentoFinanceiro.contrato_id.in_(contrato_ids))
        else:
            lancamentos_query = lancamentos_query.filter(models.LancamentoFinanceiro.id == 0)
    else:
        imoveis_query = imoveis_query.filter(models.Imovel.id == 0)
        moradores_query = moradores_query.filter(models.Morador.id == 0)
        boletos_query = boletos_query.filter(models.Boleto.id == 0)
        contratos_query = contratos_query.filter(models.Contrato.id == 0)
        avisos_query = avisos_query.filter(models.Aviso.id == 0)
        ocorrencias_query = ocorrencias_query.filter(models.Ocorrencia.id == 0)
        lancamentos_query = lancamentos_query.filter(models.LancamentoFinanceiro.id == 0)

    if current_user.role == "morador":
        morador = db.query(models.Morador).filter(models.Morador.user_id == current_user.id).first()
        morador_id = morador.id if morador else 0
        if not property_ids:
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
        "imoveis": imoveis_query.count(),
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
