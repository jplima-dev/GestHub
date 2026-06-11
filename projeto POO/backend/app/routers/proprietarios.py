from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.audit import write_audit
from backend.app.core.database import get_db
from backend.app.core.security import hash_password
from backend.app.dependencies import ROLE_PROPRIETARIO, require_roles
from backend.app.routers.common import apply_filters, apply_order, apply_search, get_or_404, page_response, set_fields

router = APIRouter(prefix="/proprietarios", tags=["Proprietários"])


@router.get("")
def list_proprietarios(
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = "id",
    order: str = "desc",
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    query = db.query(models.Proprietario)
    query = apply_search(query, models.Proprietario, search, ["nome", "cpf_cnpj", "telefone"])
    query = apply_order(query, models.Proprietario, order_by, order)
    return page_response(query, page, page_size)


@router.post("", response_model=schemas.ProprietarioRead, status_code=status.HTTP_201_CREATED)
def create_proprietario(
    payload: schemas.ProprietarioCreate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    user_data = payload.user or schemas.UserCreate(
        nome=payload.nome,
        email=f"proprietario.{payload.cpf_cnpj}@local",
        role="proprietario",
        password="Senha@123",
    )
    user = models.User(
        nome=user_data.nome,
        email=user_data.email.lower(),
        role="proprietario",
        ativo=user_data.ativo,
        password_hash=hash_password(user_data.password),
    )
    db.add(user)
    db.flush()
    item = models.Proprietario(user_id=user.id, **payload.model_dump(exclude={"user"}))
    db.add(item)
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "criar", "proprietarios", item.id, request=request)
    return item


@router.get("/{item_id}", response_model=schemas.ProprietarioRead)
def get_proprietario(
    item_id: int,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    return get_or_404(db, models.Proprietario, item_id)


@router.put("/{item_id}", response_model=schemas.ProprietarioRead)
def update_proprietario(
    item_id: int,
    payload: schemas.ProprietarioUpdate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Proprietario, item_id)
    set_fields(item, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "atualizar", "proprietarios", item.id, request=request)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proprietario(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Proprietario, item_id)
    db.delete(item)
    db.commit()
    write_audit(db, current_user, "excluir", "proprietarios", item_id, request=request)
    return None

