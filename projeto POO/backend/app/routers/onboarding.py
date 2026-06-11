from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.database import get_db
from backend.app.core.property_access import accessible_property_ids, add_property_membership, property_role
from backend.app.dependencies import get_current_user

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


def _property_payload(db: Session, user: models.User, imovel: models.Imovel) -> dict:
    return {
        "id": imovel.id,
        "titulo": imovel.titulo,
        "tipo": imovel.tipo,
        "endereco": imovel.endereco,
        "cidade": imovel.cidade,
        "estado": imovel.estado,
        "status": imovel.status,
        "role": property_role(db, user, imovel.id),
    }


def _owner_profile_for_property(db: Session, user: models.User) -> models.Proprietario:
    proprietario = db.query(models.Proprietario).filter(models.Proprietario.user_id == user.id).first()
    if proprietario:
        return proprietario
    proprietario = models.Proprietario(
        user_id=user.id,
        nome=user.nome,
        cpf_cnpj=f"AUTO-OWNER-{user.id:06d}",
        observacoes="Perfil técnico criado para vincular propriedade no onboarding.",
    )
    db.add(proprietario)
    db.flush()
    return proprietario


@router.get("/properties", response_model=list[schemas.PropertyAccessRead])
def my_properties(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    ids = accessible_property_ids(db, current_user)
    if not ids:
        return []
    imoveis = db.query(models.Imovel).filter(models.Imovel.id.in_(ids)).order_by(models.Imovel.titulo.asc()).all()
    return [_property_payload(db, current_user, imovel) for imovel in imoveis]


@router.get("/available-properties", response_model=list[schemas.PropertyAccessRead])
def available_properties(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    own_ids = set(accessible_property_ids(db, current_user))
    query = db.query(models.Imovel).order_by(models.Imovel.titulo.asc()).limit(50)
    imoveis = [imovel for imovel in query.all() if imovel.id not in own_ids]
    return [_property_payload(db, current_user, imovel) | {"role": "viewer"} for imovel in imoveis]


@router.post("/properties", response_model=schemas.PropertyAccessRead, status_code=status.HTTP_201_CREATED)
def create_property(
    payload: schemas.OnboardingPropertyCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proprietario = _owner_profile_for_property(db, current_user)
    imovel = models.Imovel(
        proprietario_id=proprietario.id,
        tipo=payload.tipo,
        titulo=payload.titulo,
        endereco=payload.endereco,
        cidade=payload.cidade,
        estado=payload.estado.upper(),
        valor=payload.valor,
        area_m2=payload.area_m2,
        status="disponivel",
        descricao=payload.descricao,
    )
    db.add(imovel)
    db.flush()
    role = "admin" if current_user.role == "proprietario" else "viewer"
    add_property_membership(db, current_user, imovel.id, role)
    db.commit()
    db.refresh(imovel)
    return _property_payload(db, current_user, imovel)


@router.post("/properties/{property_id}/select", response_model=schemas.PropertyAccessRead)
def select_property(
    property_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    imovel = db.get(models.Imovel, property_id)
    if not imovel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Propriedade não encontrada.")
    role = "admin" if current_user.role == "proprietario" and imovel.proprietario.user_id == current_user.id else "viewer"
    add_property_membership(db, current_user, imovel.id, role)
    db.commit()
    db.refresh(imovel)
    return _property_payload(db, current_user, imovel)

