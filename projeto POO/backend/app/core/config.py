from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "CondoFlow"
    app_version: str = "1.0.0"
    api_prefix: str = "/api"
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "troque-esta-chave-em-producao")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))
    csrf_expire_minutes: int = int(os.getenv("CSRF_EXPIRE_MINUTES", "720"))
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://127.0.0.1:8000,http://localhost:8000",
        ).split(",")
        if origin.strip()
    )

    @property
    def backend_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def project_dir(self) -> Path:
        return self.backend_dir.parent

    @property
    def frontend_dir(self) -> Path:
        return self.project_dir / "frontend"

    @property
    def upload_dir(self) -> Path:
        return self.backend_dir / "uploads"

    @property
    def database_path(self) -> Path:
        return self.backend_dir / "data" / "condoflow.db"

    @property
    def database_url(self) -> str:
        return os.getenv("DATABASE_URL", f"sqlite:///{self.database_path.as_posix()}")


settings = Settings()

