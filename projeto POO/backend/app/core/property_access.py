from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app import models
from backend.app.dependencies import is_admin


def accessible_property_ids(db: Session, user: models.User) -> list[int]:
    if is_admin(user):
        return [
            imovel_id
            for (imovel_id,) in db.query(models.Imovel.id).order_by(models.Imovel.id.asc()).all()
        ]

    ids: set[int] = {
        imovel_id
        for (imovel_id,) in db.query(models.PropriedadeUsuario.imovel_id)
        .filter(
            models.PropriedadeUsuario.user_id == user.id,
            models.PropriedadeUsuario.ativo.is_(True),
        )
        .all()
    }

    proprietario = db.query(models.Proprietario).filter(models.Proprietario.user_id == user.id).first()
    if proprietario:
        ids.update(
            imovel_id
            for (imovel_id,) in db.query(models.Imovel.id).filter(models.Imovel.proprietario_id == proprietario.id).all()
        )

    morador = db.query(models.Morador).filter(models.Morador.user_id == user.id).first()
    if morador:
        ids.update(
            imovel_id
            for (imovel_id,) in db.query(models.Contrato.imovel_id).filter(models.Contrato.morador_id == morador.id).all()
        )

    return sorted(ids)


def ensure_property_access(db: Session, user: models.User, property_id: int | None) -> int | None:
    if property_id is None:
        return None
    if is_admin(user):
        return property_id
    if property_id not in accessible_property_ids(db, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Propriedade fora do seu acesso.")
    return property_id


def property_role(db: Session, user: models.User, property_id: int) -> str:
    membership = (
        db.query(models.PropriedadeUsuario)
        .filter(
            models.PropriedadeUsuario.user_id == user.id,
            models.PropriedadeUsuario.imovel_id == property_id,
            models.PropriedadeUsuario.ativo.is_(True),
        )
        .first()
    )
    if membership:
        return membership.role
    if is_admin(user):
        return "admin"
    return "viewer"


def add_property_membership(db: Session, user: models.User, property_id: int, role: str) -> models.PropriedadeUsuario:
    membership = (
        db.query(models.PropriedadeUsuario)
        .filter(models.PropriedadeUsuario.user_id == user.id, models.PropriedadeUsuario.imovel_id == property_id)
        .first()
    )
    if membership:
        membership.role = role
        membership.ativo = True
        return membership
    membership = models.PropriedadeUsuario(user_id=user.id, imovel_id=property_id, role=role, ativo=True)
    db.add(membership)
    return membership
