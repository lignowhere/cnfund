from collections.abc import Generator
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..core.rbac import ADMIN_ONLY_ROLES, MUTATE_ROLES, READ_ROLES, has_role
from ..core.security import decode_token
from ..models.auth import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except ValueError:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    username = payload.get("sub")
    if not username:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_read_access(user: User = Depends(get_current_user)) -> User:
    if not has_role(user.role, READ_ROLES):
        raise HTTPException(status_code=403, detail="Read permission denied")
    return user


def require_mutate_access(user: User = Depends(get_current_user)) -> User:
    if not has_role(user.role, MUTATE_ROLES):
        raise HTTPException(status_code=403, detail="Write permission denied")
    return user


def require_admin_access(user: User = Depends(get_current_user)) -> User:
    if not has_role(user.role, ADMIN_ONLY_ROLES):
        raise HTTPException(status_code=403, detail="Admin permission required")
    return user

