from fastapi import APIRouter, Depends, HTTPException, Query

from ...api.deps import require_admin_access, require_mutate_access, require_read_access
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
        ok, message = manager.add_investor(
            name=payload.name,
            phone=payload.phone,
            address=payload.address,
            email=payload.email,
        )
        if not ok:
            raise HTTPException(status_code=400, detail=message)
        created = sorted(manager.get_regular_investors(), key=lambda i: i.id)[-1]
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
            investor.phone = payload.phone.strip()
        if payload.address is not None:
            investor.address = payload.address.strip()
        if payload.email is not None:
            investor.email = payload.email.strip()
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
