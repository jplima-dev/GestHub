from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.audit import write_audit
from backend.app.core.database import get_db
from backend.app.core.security import hash_password
from backend.app.dependencies import ROLE_MORADOR, ROLE_PROPRIETARIO, current_morador, get_current_user, require_roles
from backend.app.routers.common import apply_filters, apply_order, apply_search, get_or_404, page_response, set_fields

router = APIRouter(prefix="/moradores", tags=["Moradores"])


@router.get("")
def list_moradores(
    search: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    unidade_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = "id",
    order: str = "desc",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Morador)
    if current_user.role == ROLE_MORADOR:
        morador = current_morador(db, current_user)
        query = query.filter(models.Morador.id == morador.id)
    query = apply_search(query, models.Morador, search, ["nome", "email", "cpf", "telefone"])
    query = apply_filters(query, models.Morador, {"status": status_filter, "unidade_id": unidade_id})
    query = apply_order(query, models.Morador, order_by, order)
    return page_response(query, page, page_size)


@router.post("", response_model=schemas.MoradorRead, status_code=status.HTTP_201_CREATED)
def create_morador(
    payload: schemas.MoradorCreate,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    user_id = None
    if payload.user:
        user = models.User(
            nome=payload.user.nome,
            email=payload.user.email.lower(),
            role="morador",
            ativo=payload.user.ativo,
            password_hash=hash_password(payload.user.password),
        )
        db.add(user)
        db.flush()
        user_id = user.id
    item = models.Morador(user_id=user_id, **payload.model_dump(exclude={"user"}))
    db.add(item)
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "criar", "moradores", item.id, request=request)
    return item


@router.get("/{item_id}", response_model=schemas.MoradorRead)
def get_morador(item_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_or_404(db, models.Morador, item_id)
    if current_user.role == ROLE_MORADOR and item.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito ao próprio perfil.")
    return item


@router.put("/{item_id}", response_model=schemas.MoradorRead)
def update_morador(
    item_id: int,
    payload: schemas.MoradorUpdate,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Morador, item_id)
    data = payload.model_dump(exclude_unset=True)
    if current_user.role == ROLE_MORADOR:
        if item.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito ao próprio perfil.")
        data = {key: data[key] for key in data.keys() & {"telefone", "ocupacao", "observacoes"}}
    set_fields(item, data)
    db.commit()
    db.refresh(item)
    write_audit(db, current_user, "atualizar", "moradores", item.id, request=request)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_morador(
    item_id: int,
    request: Request,
    current_user: models.User = Depends(require_roles(ROLE_PROPRIETARIO)),
    db: Session = Depends(get_db),
):
    item = get_or_404(db, models.Morador, item_id)
    db.delete(item)
    db.commit()
    write_audit(db, current_user, "excluir", "moradores", item_id, request=request)
    return None

@router.post("/cadastro-publico")
def cadastro_publico(
    payload: schemas.MoradorCreate,
    db: Session = Depends(get_db),
):
    email = payload.email.lower()

    usuario_existente = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if usuario_existente:
        raise HTTPException(
            status_code=400,
            detail="E-mail já cadastrado"
        )

    cpf_existente = (
        db.query(models.Morador)
        .filter(models.Morador.cpf == payload.cpf)
        .first()
    )

    if cpf_existente:
        raise HTTPException(
            status_code=400,
            detail="CPF já cadastrado"
        )

    senha = payload.user.password

    user = models.User(
        nome=payload.nome,
        email=email,
        role="morador",
        ativo=True,
        password_hash=hash_password(senha),
    )

    db.add(user)
    db.flush()

    morador = models.Morador(
        user_id=user.id,
        unidade_id=payload.unidade_id,
        nome=payload.nome,
        email=email,
        cpf=payload.cpf,
        telefone=payload.telefone,
        data_nascimento=payload.data_nascimento,
        ocupacao=payload.ocupacao,
        observacoes=payload.observacoes,
    )

    db.add(morador)
    db.commit()

    return {
        "success": True,
        "message": "Cadastro realizado com sucesso"
    }