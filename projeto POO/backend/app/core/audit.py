from __future__ import annotations

import json
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from backend.app import models


def write_audit(
    db: Session,
    user: models.User | None,
    acao: str,
    recurso: str,
    recurso_id: int | None = None,
    detalhes: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    ip = request.client.host if request and request.client else None
    log = models.AuditLog(
        user_id=user.id if user else None,
        acao=acao,
        recurso=recurso,
        recurso_id=recurso_id,
        ip=ip,
        detalhes=json.dumps(detalhes or {}, ensure_ascii=False),
    )
    db.add(log)
    db.commit()

