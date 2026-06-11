from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.audit import write_audit
from backend.app.core.database import get_db
from backend.app.dependencies import ROLE_PROPRIETARIO, require_roles
from backend.app.routers.common import apply_filters, apply_order, apply_search, get_or_404, page_response, set_fields

router = APIRouter(prefix="/financeiro", tags=["Gestão Financeira"])


@router.get("/lancamentos")
def list_lancamentos(
    search: str | None = None,
    tipo: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = "data",
    order: str = "desc",
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    query = db.query(models.LancamentoFinanceiro)
    query = apply_search(query, models.LancamentoFinanceiro, search, ["categoria", "descricao"])
    query = apply_filters(query, models.LancamentoFinanceiro, {"tipo": tipo, "status": status_filter})
    query = apply_order(query, models.LancamentoFinanceiro, order_by, order)
    return page_response(query, page, page_size)


@router.post("/lancamentos", response_model=schemas.LancamentoRead, status_code=status.HTTP_201_CREATED)
def create_lancamento(
    payload: schemas.LancamentoCreate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = models.LancamentoFinanceiro(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "criar", "financeiro", item.id, request=request)
    return item


@router.put("/lancamentos/{item_id}", response_model=schemas.LancamentoRead)
def update_lancamento(
    item_id: int,
    payload: schemas.LancamentoUpdate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.LancamentoFinanceiro, item_id)
    set_fields(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "atualizar", "financeiro", item.id, request=request)
    return item


@router.delete("/lancamentos/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lancamento(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.LancamentoFinanceiro, item_id)
    db.delete(item)
    db.commit()
    write_audit(db, current_user, "excluir", "financeiro", item_id, request=request)
    return None


@router.get("/resumo")
def resumo_financeiro(
    inicio: date | None = None,
    fim: date | None = None,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    query = db.query(models.LancamentoFinanceiro)
    if inicio:
        query = query.filter(models.LancamentoFinanceiro.data >= inicio)
    if fim:
        query = query.filter(models.LancamentoFinanceiro.data <= fim)
    receitas = (
        query.filter(models.LancamentoFinanceiro.tipo == "receita")
        .with_entities(func.coalesce(func.sum(models.LancamentoFinanceiro.valor), 0))
        .scalar()
        or 0
    )
    despesas = (
        query.filter(models.LancamentoFinanceiro.tipo == "despesa")
        .with_entities(func.coalesce(func.sum(models.LancamentoFinanceiro.valor), 0))
        .scalar()
        or 0
    )
    por_categoria = [
        {"categoria": categoria, "tipo": tipo, "total": float(total or 0)}
        for categoria, tipo, total in db.query(
            models.LancamentoFinanceiro.categoria,
            models.LancamentoFinanceiro.tipo,
            func.coalesce(func.sum(models.LancamentoFinanceiro.valor), 0),
        )
        .group_by(models.LancamentoFinanceiro.categoria, models.LancamentoFinanceiro.tipo)
        .all()
    ]
    return {
        "receitas": float(receitas),
        "despesas": float(despesas),
        "saldo": float(receitas - despesas),
        "por_categoria": por_categoria,
    }


@router.get("/fluxo-caixa")
def fluxo_caixa(
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            func.strftime("%Y-%m", models.LancamentoFinanceiro.data).label("mes"),
            models.LancamentoFinanceiro.tipo,
            func.coalesce(func.sum(models.LancamentoFinanceiro.valor), 0).label("total"),
        )
        .group_by("mes", models.LancamentoFinanceiro.tipo)
        .order_by("mes")
        .all()
    )
    return [{"mes": row.mes, "tipo": row.tipo, "total": float(row.total or 0)} for row in rows]


@router.get("/balancete")
def balancete(
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    receitas = db.query(func.coalesce(func.sum(models.LancamentoFinanceiro.valor), 0)).filter_by(tipo="receita").scalar() or 0
    despesas = db.query(func.coalesce(func.sum(models.LancamentoFinanceiro.valor), 0)).filter_by(tipo="despesa").scalar() or 0
    boletos_pendentes = db.query(func.coalesce(func.sum(models.Boleto.valor), 0)).filter(models.Boleto.status == "pendente").scalar() or 0
    return {
        "receitas_realizadas": float(receitas),
        "despesas_realizadas": float(despesas),
        "saldo_realizado": float(receitas - despesas),
        "boletos_a_receber": float(boletos_pendentes),
    }

