from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.database import get_db
from backend.app.core.security import create_access_token, create_csrf_token, hash_password, now_utc, verify_password
from backend.app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.get("/csrf", response_model=schemas.CsrfToken)
def csrf_token() -> dict[str, str]:
    return {"csrf_token": create_csrf_token()}


@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form.username.lower()).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos.")
    if not user.ativo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário inativo.")
    user.ultimo_login = now_utc()
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user.id, user.role), "token_type": "bearer", "user": user}


@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    users_count = db.query(models.User).count()
    if users_count > 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cadastro público desativado após bootstrap.")
    user = models.User(
        nome=payload.nome,
        email=payload.email.lower(),
        role=payload.role,
        ativo=payload.ativo,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=schemas.UserRead)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("/me/profile")
def my_profile(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "proprietario":
        profile = db.query(models.Proprietario).filter(models.Proprietario.user_id == current_user.id).first()
    else:
        profile = db.query(models.Morador).filter(models.Morador.user_id == current_user.id).first()
    return {"user": current_user, "profile": profile}

