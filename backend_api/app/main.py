from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .api.router import api_router
from .core.config import get_settings
from .core.database import Base, SessionLocal, engine
from .core.security import decode_token, get_password_hash
from .models.auth import AuditLog, User


settings = get_settings()


def _allowed_origins() -> list[str]:
    raw = settings.allowed_origins or ""
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or ["http://localhost:3000", "http://127.0.0.1:3000"]


def _allowed_origin_regex() -> str | None:
    value = (settings.allowed_origin_regex or "").strip()
    return value or None


def seed_admin_user(db: Session) -> None:
    existing = db.query(User).filter(User.username == settings.admin_username).first()
    if existing:
        return
    db.add(
        User(
            username=settings.admin_username,
            password_hash=get_password_hash(settings.admin_password),
            role=settings.admin_role,
            is_active=True,
        )
    )
    db.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_admin_user(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_origin_regex=_allowed_origin_regex(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    response = await call_next(request)

    username = "anonymous"
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
            username = str(payload.get("sub") or "anonymous")
        except ValueError:
            username = "invalid_token"

    db = SessionLocal()
    try:
        db.add(
            AuditLog(
                username=username,
                action=f"{request.method} {request.url.path}",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                details=f"query={dict(request.query_params)}",
            )
        )
        db.commit()
    finally:
        db.close()
    return response


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "time": datetime.utcnow().isoformat(),
        "env": settings.environment,
    }


app.include_router(api_router, prefix=settings.api_prefix)
