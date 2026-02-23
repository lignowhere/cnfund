from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...api.deps import get_db, require_admin_access
from ...core.security import get_password_hash
from ...models.auth import InvestorAccount, User
from ...schemas.accounts import (
    InvestorAccountAdminDTO,
    InvestorAccountCreateRequest,
    InvestorAccountResetPasswordRequest,
    InvestorAccountUpdateRequest,
)
from ...schemas.common import ApiResponse
from ...services.fund_runtime import runtime


router = APIRouter()


def _load_regular_investors() -> dict[int, str]:
    def _read(manager):
        return {int(inv.id): str(inv.name) for inv in manager.get_regular_investors()}

    return runtime.read(_read)


def _build_row(investor_id: int, investor_name: str, link: InvestorAccount | None) -> InvestorAccountAdminDTO:
    if link is None or link.user is None:
        return InvestorAccountAdminDTO(
            investor_id=investor_id,
            investor_name=investor_name,
            has_account=False,
        )

    return InvestorAccountAdminDTO(
        investor_id=investor_id,
        investor_name=investor_name,
        has_account=True,
        username=link.user.username,
        is_active=bool(link.user.is_active),
        created_at=link.created_at,
    )


@router.get("/investors", response_model=ApiResponse[list[InvestorAccountAdminDTO]])
def list_investor_accounts(
    _user=Depends(require_admin_access),
    db: Session = Depends(get_db),
):
    investors = _load_regular_investors()
    links = db.query(InvestorAccount).all()
    link_map = {int(link.investor_id): link for link in links}
    rows = [
        _build_row(investor_id, investor_name, link_map.get(investor_id))
        for investor_id, investor_name in sorted(investors.items(), key=lambda item: item[0])
    ]
    return ApiResponse(data=rows)


@router.post("/investors", response_model=ApiResponse[InvestorAccountAdminDTO])
def create_investor_account(
    payload: InvestorAccountCreateRequest,
    _user=Depends(require_admin_access),
    db: Session = Depends(get_db),
):
    investors = _load_regular_investors()
    investor_name = investors.get(int(payload.investor_id))
    if investor_name is None:
        raise HTTPException(status_code=404, detail="Investor not found")

    normalized_username = payload.username.strip()
    if len(normalized_username) < 3:
        raise HTTPException(status_code=422, detail="username must be at least 3 non-space characters")

    existing_link = db.query(InvestorAccount).filter(InvestorAccount.investor_id == payload.investor_id).first()
    if existing_link is not None:
        raise HTTPException(status_code=409, detail="Investor account already exists")

    existing_user = db.query(User).filter(User.username == normalized_username).first()
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="Username already exists")

    user = User(
        username=normalized_username,
        password_hash=get_password_hash(payload.password),
        role="investor",
        is_active=True,
    )
    db.add(user)
    db.flush()

    link = InvestorAccount(user_id=user.id, investor_id=int(payload.investor_id))
    db.add(link)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Investor account already exists") from exc

    db.refresh(link)
    db.refresh(user)
    link.user = user
    return ApiResponse(message="Investor account created", data=_build_row(int(payload.investor_id), investor_name, link))


@router.patch("/investors/{investor_id}", response_model=ApiResponse[InvestorAccountAdminDTO])
def update_investor_account(
    investor_id: int,
    payload: InvestorAccountUpdateRequest,
    _user=Depends(require_admin_access),
    db: Session = Depends(get_db),
):
    if payload.username is None and payload.is_active is None:
        raise HTTPException(status_code=400, detail="No updates provided")

    investors = _load_regular_investors()
    investor_name = investors.get(int(investor_id))
    if investor_name is None:
        raise HTTPException(status_code=404, detail="Investor not found")

    link = db.query(InvestorAccount).filter(InvestorAccount.investor_id == investor_id).first()
    if link is None or link.user is None:
        raise HTTPException(status_code=404, detail="Investor account not found")

    if payload.username is not None:
        next_username = payload.username.strip()
        if len(next_username) < 3:
            raise HTTPException(status_code=422, detail="username must be at least 3 non-space characters")
        existing = db.query(User).filter(User.username == next_username, User.id != link.user_id).first()
        if existing is not None:
            raise HTTPException(status_code=409, detail="Username already exists")
        link.user.username = next_username

    if payload.is_active is not None:
        link.user.is_active = bool(payload.is_active)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Account update conflict") from exc

    db.refresh(link)
    db.refresh(link.user)
    return ApiResponse(message="Investor account updated", data=_build_row(int(investor_id), investor_name, link))


@router.post("/investors/{investor_id}/reset-password", response_model=ApiResponse[dict])
def reset_investor_account_password(
    investor_id: int,
    payload: InvestorAccountResetPasswordRequest,
    _user=Depends(require_admin_access),
    db: Session = Depends(get_db),
):
    link = db.query(InvestorAccount).filter(InvestorAccount.investor_id == investor_id).first()
    if link is None or link.user is None:
        raise HTTPException(status_code=404, detail="Investor account not found")

    link.user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return ApiResponse(message="Password reset successfully", data={"reset": True})
