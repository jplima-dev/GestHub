from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from html import escape
from typing import Any

import jwt
from fastapi import HTTPException, status

from backend.app.core.config import settings


def now_utc() -> datetime:
    return datetime.now(UTC)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 240_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, digest = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            int(iterations),
        ).hex()
        return hmac.compare_digest(candidate, digest)
    except ValueError:
        return False


def create_access_token(user_id: int, role: str) -> str:
    issued_at = now_utc()
    expires_at = issued_at + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    if payload.get("type") != "access" or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")
    return payload


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _unb64(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}".encode("utf-8"))


def create_csrf_token() -> str:
    payload = {
        "iat": int(now_utc().timestamp()),
        "nonce": secrets.token_urlsafe(24),
    }
    body = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(settings.jwt_secret_key.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    return f"{body}.{_b64(signature)}"


def verify_csrf_token(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    body, signature = token.rsplit(".", 1)
    expected = _b64(hmac.new(settings.jwt_secret_key.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        return False
    try:
        payload = json.loads(_unb64(body))
    except (ValueError, json.JSONDecodeError):
        return False
    issued_at = datetime.fromtimestamp(int(payload.get("iat", 0)), UTC)
    return now_utc() - issued_at <= timedelta(minutes=settings.csrf_expire_minutes)


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    return escape(value.strip(), quote=True)

