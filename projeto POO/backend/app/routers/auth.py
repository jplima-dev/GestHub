from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import create_access_token, create_csrf_token, hash_password, now_utc, verify_password
from backend.app.dependencies import ROLE_PROPRIETARIO, get_current_user, normalize_role

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
    role = normalize_role(user.role)
    if role in {"proprietario", "morador"} and user.role != role:
        user.role = role
    user.ultimo_login = now_utc()
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user.id, role), "token_type": "bearer", "user": user}


@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    role = normalize_role(payload.role)
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este e-mail já está cadastrado.")

    user = models.User(
        nome=payload.nome,
        email=email,
        role=role,
        ativo=True,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()

    if role == ROLE_PROPRIETARIO:
        db.add(
            models.Proprietario(
                user_id=user.id,
                nome=payload.nome,
                cpf_cnpj=f"AUTO-P-{user.id:06d}",
                observacoes="Perfil criado pelo cadastro público.",
            )
        )
    else:
        db.add(
            models.Morador(
                user_id=user.id,
                nome=payload.nome,
                email=email,
                cpf=f"AUTO-M-{user.id:06d}",
                status="ativo",
                observacoes="Perfil criado pelo cadastro público.",
            )
        )

    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user.id, role), "token_type": "bearer", "user": user}


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


@router.get("/account")
def account(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "proprietario":
        profile = db.query(models.Proprietario).filter(models.Proprietario.user_id == current_user.id).first()
    else:
        profile = db.query(models.Morador).filter(models.Morador.user_id == current_user.id).first()
    return {"user": current_user, "profile": profile}


@router.put("/account", response_model=schemas.UserRead)
def update_account(
    payload: schemas.AccountUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"]:
        email = data["email"].lower().strip()
        exists = db.query(models.User).filter(models.User.email == email, models.User.id != current_user.id).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este e-mail já está em uso.")
        current_user.email = email
    if "nome" in data and data["nome"]:
        current_user.nome = data["nome"].strip()
    if "password" in data and data["password"]:
        current_user.password_hash = hash_password(data["password"])

    if current_user.role == "proprietario":
        profile = db.query(models.Proprietario).filter(models.Proprietario.user_id == current_user.id).first()
        if profile and data.get("nome"):
            profile.nome = current_user.nome
    else:
        profile = db.query(models.Morador).filter(models.Morador.user_id == current_user.id).first()
        if profile:
            if data.get("nome"):
                profile.nome = current_user.nome
            if data.get("email"):
                profile.email = current_user.email

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/account/avatar", response_model=schemas.UserRead)
def upload_avatar(
    avatar: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if avatar.content_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Envie uma imagem JPG, PNG, WEBP ou GIF.")
    extension = Path(avatar.filename or "avatar.png").suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        extension = ".png"
    avatar_dir = settings.upload_dir / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    filename = f"user-{current_user.id}{extension}"
    target = avatar_dir / filename
    with target.open("wb") as buffer:
        shutil.copyfileobj(avatar.file, buffer)
    current_user.avatar_path = f"/uploads/avatars/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user
