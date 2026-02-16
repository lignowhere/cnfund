from fastapi import APIRouter, Depends, HTTPException, Query

from helpers import validate_email, validate_phone

from ...api.deps import require_admin_access, require_read_access
from ...schemas.common import ApiResponse, PaginatedResponse
from ...schemas.investors import (
    InvestorCardDTO,
    InvestorCreateRequest,
    InvestorDTO,
    InvestorSummaryDTO,
    InvestorUpdateRequest,
)
from ...services.fund_runtime import runtime
from ...services.mappers import investor_to_card_dto, investor_to_dto


router = APIRouter()


def _clean_text(value: str | None) -> str:
    return str(value or "").strip()


def _validate_phone_or_raise(phone: str) -> str:
    cleaned = _clean_text(phone)
    if cleaned and not validate_phone(cleaned):
        raise HTTPException(status_code=400, detail="Số điện thoại phải có định dạng 0xxxxxxxxx.")
    return cleaned


def _validate_email_or_raise(email: str) -> str:
    cleaned = _clean_text(email)
    if cleaned and not validate_email(cleaned):
        raise HTTPException(status_code=400, detail="Email không hợp lệ.")
    return cleaned


def _validate_location_pair_or_raise(province_code: str, ward_code: str) -> None:
    if bool(province_code) != bool(ward_code):
        raise HTTPException(
            status_code=400,
            detail="Tỉnh/Thành và Phường/Xã phải được chọn đồng thời.",
        )


def _compose_full_address(address_line: str, ward_name: str, province_name: str) -> str:
    parts = [part for part in [address_line, ward_name, province_name] if part]
    return ", ".join(parts)


@router.get("", response_model=ApiResponse[list[InvestorDTO]])
def list_investors(_user=Depends(require_read_access)):
    def _read(manager):
        return [investor_to_dto(inv) for inv in manager.get_regular_investors()]

    return ApiResponse(data=runtime.read(_read))


@router.get("/cards", response_model=ApiResponse[list[InvestorCardDTO]])
def list_investor_cards(
    nav: float | None = Query(default=None, ge=0),
    _user=Depends(require_read_access),
):
    def _read(manager):
        current_nav = nav if nav is not None else (manager.get_latest_total_nav() or 0)
        cards: list[InvestorCardDTO] = []
        for inv in manager.get_regular_investors():
            balance, profit, profit_percent = manager.get_investor_balance(inv.id, current_nav)
            cards.append(investor_to_card_dto(inv, balance, profit, profit_percent))
        return cards

    return ApiResponse(data=runtime.read(_read))


@router.get("/cards/paginated", response_model=ApiResponse[PaginatedResponse[InvestorCardDTO]])
def list_investor_cards_paginated(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    nav: float | None = Query(default=None, ge=0),
    _user=Depends(require_read_access),
):
    def _read(manager):
        current_nav = nav if nav is not None else (manager.get_latest_total_nav() or 0)
        cards: list[InvestorCardDTO] = []
        for inv in manager.get_regular_investors():
            balance, profit, profit_percent = manager.get_investor_balance(inv.id, current_nav)
            cards.append(investor_to_card_dto(inv, balance, profit, profit_percent))

        cards.sort(key=lambda item: item.current_value, reverse=True)
        start = (page - 1) * page_size
        end = start + page_size
        return PaginatedResponse(
            items=cards[start:end],
            total=len(cards),
            page=page,
            page_size=page_size,
        )

    return ApiResponse(data=runtime.read(_read))


@router.post("", response_model=ApiResponse[InvestorDTO])
def create_investor(payload: InvestorCreateRequest, _user=Depends(require_admin_access)):
    def _write(manager):
        phone = _validate_phone_or_raise(payload.phone)
        email = _validate_email_or_raise(payload.email)
        province_code = _clean_text(payload.province_code)
        province_name = _clean_text(payload.province_name)
        ward_code = _clean_text(payload.ward_code)
        ward_name = _clean_text(payload.ward_name)
        address_line = _clean_text(payload.address_line)
        legacy_address = _clean_text(payload.address)
        _validate_location_pair_or_raise(province_code, ward_code)
        full_address = _compose_full_address(address_line, ward_name, province_name) or legacy_address

        ok, message = manager.add_investor(
            name=payload.name,
            phone=phone,
            address=full_address,
            email=email,
        )
        if not ok:
            raise HTTPException(status_code=400, detail=message)
        created = sorted(manager.get_regular_investors(), key=lambda i: i.id)[-1]
        created.join_date = payload.join_date or created.join_date
        created.province_code = province_code
        created.province_name = province_name
        created.ward_code = ward_code
        created.ward_name = ward_name
        created.address_line = address_line or legacy_address
        created.address = full_address
        return investor_to_dto(created)

    return ApiResponse(message="Investor created", data=runtime.mutate(_write))


@router.put("/{investor_id}", response_model=ApiResponse[InvestorDTO])
def update_investor(
    investor_id: int,
    payload: InvestorUpdateRequest,
    _user=Depends(require_admin_access),
):
    def _write(manager):
        investor = manager.get_investor_by_id(investor_id)
        if investor is None or investor.is_fund_manager:
            raise HTTPException(status_code=404, detail="Investor not found")

        if payload.name is not None:
            investor.name = payload.name.strip()

        if payload.phone is not None:
            investor.phone = _validate_phone_or_raise(payload.phone)

        if payload.email is not None:
            investor.email = _validate_email_or_raise(payload.email)

        if payload.join_date is not None:
            investor.join_date = payload.join_date

        structured_fields_touched = any(
            value is not None
            for value in [
                payload.province_code,
                payload.province_name,
                payload.ward_code,
                payload.ward_name,
                payload.address_line,
            ]
        )

        if structured_fields_touched:
            next_province_code = (
                _clean_text(payload.province_code)
                if payload.province_code is not None
                else _clean_text(getattr(investor, "province_code", ""))
            )
            next_province_name = (
                _clean_text(payload.province_name)
                if payload.province_name is not None
                else _clean_text(getattr(investor, "province_name", ""))
            )
            next_ward_code = (
                _clean_text(payload.ward_code)
                if payload.ward_code is not None
                else _clean_text(getattr(investor, "ward_code", ""))
            )
            next_ward_name = (
                _clean_text(payload.ward_name)
                if payload.ward_name is not None
                else _clean_text(getattr(investor, "ward_name", ""))
            )
            next_address_line = (
                _clean_text(payload.address_line)
                if payload.address_line is not None
                else _clean_text(getattr(investor, "address_line", ""))
            )

            _validate_location_pair_or_raise(next_province_code, next_ward_code)

            investor.province_code = next_province_code
            investor.province_name = next_province_name
            investor.ward_code = next_ward_code
            investor.ward_name = next_ward_name
            investor.address_line = next_address_line
            composed = _compose_full_address(next_address_line, next_ward_name, next_province_name)
            if composed:
                investor.address = composed

        if payload.address is not None and not structured_fields_touched:
            legacy_address = _clean_text(payload.address)
            investor.address = legacy_address
            investor.address_line = legacy_address
            investor.province_code = ""
            investor.province_name = ""
            investor.ward_code = ""
            investor.ward_name = ""

        return investor_to_dto(investor)

    return ApiResponse(message="Investor updated", data=runtime.mutate(_write))


@router.get("/{investor_id}/summary", response_model=ApiResponse[InvestorSummaryDTO])
def get_investor_summary(
    investor_id: int,
    nav: float | None = Query(default=None, ge=0),
    _user=Depends(require_read_access),
):
    def _read(manager):
        investor = manager.get_investor_by_id(investor_id)
        if investor is None or investor.is_fund_manager:
            raise HTTPException(status_code=404, detail="Investor not found")

        current_nav = nav if nav is not None else (manager.get_latest_total_nav() or 0)
        balance, profit, profit_percent = manager.get_investor_balance(investor_id, current_nav)
        lifetime = manager.get_investor_lifetime_performance(investor_id, current_nav)

        return InvestorSummaryDTO(
            investor_id=investor.id,
            investor_name=investor.name,
            nav_used=current_nav,
            units=manager.get_investor_units(investor_id),
            balance=balance,
            profit=profit,
            profit_percent=profit_percent,
            lifetime=lifetime,
        )

    return ApiResponse(data=runtime.read(_read))

