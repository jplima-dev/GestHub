from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app import models
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token

ROLE_PROPRIETARIO = "proprietario"
ROLE_MORADOR = "morador"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    payload = decode_access_token(token)
    user = db.get(models.User, int(payload["sub"]))
    if not user or not user.ativo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo ou inexistente.")
    return user


def require_roles(*roles: str) -> Callable[..., models.User]:
    def checker(current_user: models.User = Depends(get_current_user)) -> models.User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente.")
        return current_user

    return checker


def current_morador(db: Session, user: models.User) -> models.Morador:
    morador = db.query(models.Morador).filter(models.Morador.user_id == user.id).first()
    if not morador:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de morador não encontrado.")
    return morador


def current_proprietario(db: Session, user: models.User) -> models.Proprietario:
    proprietario = db.query(models.Proprietario).filter(models.Proprietario.user_id == user.id).first()
    if not proprietario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de proprietário não encontrado.")
    return proprietario

