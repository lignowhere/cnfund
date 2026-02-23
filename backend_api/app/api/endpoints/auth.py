from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...api.deps import get_current_user, get_db
from ...core.config import get_settings
from ...core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from ...models.auth import InvestorAccount, RefreshToken, User
from ...schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenPair,
    UserInfo,
)
from ...schemas.common import ApiResponse


router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=ApiResponse[TokenPair])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")

    access_token = create_access_token(subject=user.username, role=user.role)
    refresh_token, jti = create_refresh_token(subject=user.username, role=user.role)

    expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    db.add(
        RefreshToken(
            user_id=user.id,
            jti=jti,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
        )
    )
    db.commit()

    return ApiResponse(
        data=TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )
    )


@router.post("/refresh", response_model=ApiResponse[TokenPair])
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token type")

    username = decoded.get("sub")
    role = decoded.get("role")
    jti = decoded.get("jti")

    token_row = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if not token_row or token_row.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Refresh token revoked")
    if token_row.token_hash != hash_token(payload.refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token mismatch")
    if token_row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User is unavailable")

    token_row.revoked_at = datetime.utcnow()

    new_access = create_access_token(subject=username, role=role)
    new_refresh, new_jti = create_refresh_token(subject=username, role=role)
    db.add(
        RefreshToken(
            user_id=user.id,
            jti=new_jti,
            token_hash=hash_token(new_refresh),
            expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    db.commit()

    return ApiResponse(
        data=TokenPair(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=settings.access_token_expire_minutes * 60,
        )
    )


@router.post("/logout", response_model=ApiResponse[dict])
def logout(payload: LogoutRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    jti = decoded.get("jti")
    token_row = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if token_row and token_row.revoked_at is None:
        token_row.revoked_at = datetime.utcnow()
        db.commit()

    return ApiResponse(message="Logged out", data={"logged_out": True})


@router.get("/me", response_model=ApiResponse[UserInfo])
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    investor_link = db.query(InvestorAccount).filter(InvestorAccount.user_id == user.id).first()
    investor_id = int(investor_link.investor_id) if investor_link else None
    return ApiResponse(
        data=UserInfo(
            username=user.username,
            role=user.role,  # type: ignore[arg-type]
            investor_id=investor_id,
            is_active=user.is_active,
            created_at=user.created_at,
        )
    )
