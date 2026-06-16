from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, init_db
from backend.app.core.security import verify_csrf_token
from backend.app.routers import (
    alugueis,
    auth,
    avisos,
    boletos,
    condominios,
    contratos,
    dashboard,
    documentos,
    financeiro,
    imoveis,
    moradores,
    ocorrencias,
    proprietarios,
    relatorios,
)
from backend.app.seed import seed_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("condoflow")

app = FastAPI(
    title="CondoFlow API",
    version=settings.app_version,
    description="API REST para gestão profissional de condomínios, imóveis e aluguéis.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSRF_EXEMPT_PREFIXES = (
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/csrf",
    "/docs",
    "/redoc",
    "/openapi.json",
)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if (
        request.method not in {"GET", "HEAD", "OPTIONS"}
        and request.url.path.startswith(settings.api_prefix)
        and not request.url.path.startswith(CSRF_EXEMPT_PREFIXES)
    ):
        token = request.headers.get("x-csrf-token")

        if not verify_csrf_token(token):
            return JSONResponse(
                status_code=403,
                content={"detail": "Token CSRF ausente ou inválido."},
            )

    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=(), camera=()"
    )

    response.headers[
        "Content-Security-Policy"
    ] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "connect-src 'self'"
    )

    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Dados inválidos.",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(
    request: Request,
    exc: IntegrityError,
):
    logger.warning("Database integrity error: %s", exc)

    return JSONResponse(
        status_code=409,
        content={
            "detail": "Registro duplicado ou relacionamento inválido."
        },
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
):
    logger.exception("Database error")

    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno no banco de dados."},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.on_event("startup")
def on_startup() -> None:
    init_db()

    db = SessionLocal()

    try:
        seed_database(db)
    finally:
        db.close()


# ==========================
# ROTAS DA API
# ==========================

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(proprietarios.router, prefix=settings.api_prefix)
app.include_router(moradores.router, prefix=settings.api_prefix)
app.include_router(condominios.router, prefix=settings.api_prefix)
app.include_router(imoveis.router, prefix=settings.api_prefix)
app.include_router(avisos.router, prefix=settings.api_prefix)
app.include_router(boletos.router, prefix=settings.api_prefix)
app.include_router(contratos.router, prefix=settings.api_prefix)
app.include_router(alugueis.router, prefix=settings.api_prefix)
app.include_router(financeiro.router, prefix=settings.api_prefix)
app.include_router(ocorrencias.router, prefix=settings.api_prefix)
app.include_router(documentos.router, prefix=settings.api_prefix)
app.include_router(relatorios.router, prefix=settings.api_prefix)

# ==========================
# ARQUIVOS FRONTEND
# ==========================

if settings.frontend_dir.exists():
    app.mount(
        "/static",
        StaticFiles(directory=settings.frontend_dir),
        name="static",
    )


@app.get("/")
def index():
    index_path = settings.frontend_dir / "index.html"

    if not index_path.exists():
        return {"message": "Frontend ainda não foi criado."}

    return FileResponse(index_path)


@app.get("/cadastro")
def cadastro():
    cadastro_path = settings.frontend_dir / "cadastro.html"

    if not cadastro_path.exists():
        return {"message": "Página de cadastro não encontrada."}

    return FileResponse(cadastro_path)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }