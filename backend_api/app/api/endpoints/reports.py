import unicodedata
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from ...api.deps import require_read_access
from ...schemas.common import ApiResponse
from ...schemas.reports import (
    DashboardKPIDTO,
    DashboardResponseDTO,
    InvestorFeeDetailsDTO,
    InvestorLifetimeDTO,
    InvestorProfileDTO,
    InvestorReportDTO,
    InvestorTrancheDTO,
    TopInvestorDTO,
    TransactionReportDTO,
    TransactionReportSummaryDTO,
)
from ...services.fund_runtime import runtime
from ...services.mappers import fee_record_to_dto, transaction_to_dto


router = APIRouter()


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value).encode("ascii", "ignore").decode("ascii")
    return normalized.lower().strip()


def _to_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


@router.get("/dashboard", response_model=ApiResponse[DashboardResponseDTO])
def dashboard(nav: float | None = Query(default=None, ge=0), _user=Depends(require_read_access)):
    def _read(manager):
        current_nav = nav if nav is not None else (manager.get_latest_total_nav() or 0.0)
        regular_investors = manager.get_regular_investors()
        total_units = sum(t.units for t in manager.tranches)
        total_fees_paid = sum(t.cumulative_fees_paid for t in manager.tranches)
        current_price = manager.calculate_price_per_unit(current_nav) if current_nav > 0 else 0.0

        fm = manager.get_fund_manager()
        fm_value = 0.0
        if fm:
            fm_units = manager.get_investor_units(fm.id)
            fm_value = fm_units * current_price

        top = []
        for inv in regular_investors:
            balance, profit, profit_pct = manager.get_investor_balance(inv.id, current_nav)
            top.append(
                TopInvestorDTO(
                    investor_id=inv.id,
                    investor_name=inv.name,
                    balance=balance,
                    profit=profit,
                    profit_percent=profit_pct,
                )
            )
        top.sort(key=lambda row: row.balance, reverse=True)

        total_original = sum(
            manager.get_investor_lifetime_performance(inv.id, current_nav)["original_invested"]
            for inv in regular_investors
        )
        total_current = sum(
            manager.get_investor_lifetime_performance(inv.id, current_nav)["current_value"]
            for inv in regular_investors
        )
        gross_return = ((total_current - total_original) / total_original) if total_original > 0 else 0.0

        return DashboardResponseDTO(
            kpis=DashboardKPIDTO(
                total_nav=current_nav,
                total_investors=len(regular_investors),
                total_units=total_units,
                total_fees_paid=total_fees_paid,
                fund_manager_value=fm_value,
                gross_return=gross_return,
            ),
            top_investors=top[:10],
        )

    return ApiResponse(data=runtime.read(_read))


@router.get("/investor/{investor_id}", response_model=ApiResponse[InvestorReportDTO])
def investor_report(
    investor_id: int,
    nav: float | None = Query(default=None, ge=0),
    _user=Depends(require_read_access),
):
    def _read(manager):
        investor = manager.get_investor_by_id(investor_id)
        if investor is None or investor.is_fund_manager:
            raise HTTPException(status_code=404, detail="Investor not found")

        current_nav = nav if nav is not None else (manager.get_latest_total_nav() or 0.0)
        report = manager.get_investor_individual_report(investor_id, current_nav)

        name_map = {inv.id: inv.name for inv in manager.investors}
        tx_rows = [
            transaction_to_dto(tx, name_map.get(tx.investor_id, f"Investor {tx.investor_id}"))
            for tx in sorted(
                report.get("transactions", []),
                key=lambda tx: (_to_datetime(tx.date), tx.id),
                reverse=True,
            )
        ]
        fee_rows = [
            fee_record_to_dto(row)
            for row in sorted(
                report.get("fee_history", []),
                key=lambda fee: fee.id,
                reverse=True,
            )
        ]

        tranches = [
            InvestorTrancheDTO(
                tranche_id=str(getattr(tranche, "tranche_id", "")),
                entry_date=_to_datetime(getattr(tranche, "entry_date", datetime.utcnow())),
                entry_nav=_safe_float(getattr(tranche, "entry_nav", 0.0)),
                units=_safe_float(getattr(tranche, "units", 0.0)),
                hwm=_safe_float(getattr(tranche, "hwm", 0.0)),
                invested_value=_safe_float(getattr(tranche, "invested_value", 0.0)),
                original_invested_value=_safe_float(
                    getattr(tranche, "original_invested_value", 0.0)
                ),
                cumulative_fees_paid=_safe_float(getattr(tranche, "cumulative_fees_paid", 0.0)),
            )
            for tranche in report.get("tranches", [])
        ]

        lifetime_data = report.get("lifetime_performance", {})
        fee_details_data = report.get("fee_details", {})

        return InvestorReportDTO(
            investor=InvestorProfileDTO(
                id=investor.id,
                name=investor.name,
                phone=investor.phone or "",
                email=investor.email or "",
                address=investor.address or "",
                join_date=investor.join_date,
            ),
            current_balance=_safe_float(report.get("current_balance", 0.0)),
            current_profit=_safe_float(report.get("current_profit", 0.0)),
            current_profit_perc=_safe_float(report.get("current_profit_perc", 0.0)),
            lifetime_performance=InvestorLifetimeDTO(
                original_invested=_safe_float(lifetime_data.get("original_invested", 0.0)),
                current_value=_safe_float(lifetime_data.get("current_value", 0.0)),
                total_fees_paid=_safe_float(lifetime_data.get("total_fees_paid", 0.0)),
                gross_profit=_safe_float(lifetime_data.get("gross_profit", 0.0)),
                net_profit=_safe_float(lifetime_data.get("net_profit", 0.0)),
                gross_return=_safe_float(lifetime_data.get("gross_return", 0.0)),
                net_return=_safe_float(lifetime_data.get("net_return", 0.0)),
                current_units=_safe_float(lifetime_data.get("current_units", 0.0)),
            ),
            fee_details=InvestorFeeDetailsDTO(
                total_fee=_safe_float(fee_details_data.get("total_fee", 0.0)),
                balance=_safe_float(fee_details_data.get("balance", 0.0)),
                invested_value=_safe_float(fee_details_data.get("invested_value", 0.0)),
                profit=_safe_float(fee_details_data.get("profit", 0.0)),
                profit_perc=_safe_float(fee_details_data.get("profit_perc", 0.0)),
                hurdle_value=_safe_float(fee_details_data.get("hurdle_value", 0.0)),
                hwm_value=_safe_float(fee_details_data.get("hwm_value", 0.0)),
                excess_profit=_safe_float(fee_details_data.get("excess_profit", 0.0)),
                units_before=_safe_float(fee_details_data.get("units_before", 0.0)),
                units_after=_safe_float(fee_details_data.get("units_after", 0.0)),
            ),
            tranches=tranches,
            transactions=tx_rows,
            fee_history=fee_rows,
            report_date=_to_datetime(report.get("report_date", datetime.utcnow())),
            current_nav=_safe_float(report.get("current_nav", current_nav)),
            current_price=_safe_float(report.get("current_price", 0.0)),
        )

    return ApiResponse(data=runtime.read(_read))


@router.get("/transactions", response_model=ApiResponse[TransactionReportDTO])
def transaction_report(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    investor_id: int | None = Query(default=None, ge=0),
    tx_type: str | None = Query(default=None),
    _user=Depends(require_read_access),
):
    def _read(manager):
        name_map = {inv.id: inv.name for inv in manager.investors}
        transactions = sorted(
            manager.transactions,
            key=lambda tx: (tx.date, tx.id),
            reverse=True,
        )

        filtered = transactions
        if investor_id is not None:
            filtered = [tx for tx in filtered if tx.investor_id == investor_id]
        if tx_type:
            wanted = _normalize_text(tx_type)
            filtered = [tx for tx in filtered if wanted in _normalize_text(tx.type)]

        by_type: dict[str, int] = {}
        total_volume = 0.0
        net_cash_flow = 0.0
        for tx in filtered:
            by_type[tx.type] = by_type.get(tx.type, 0) + 1
            total_volume += abs(_safe_float(tx.amount))

            normalized_type = _normalize_text(tx.type)
            if "nap" in normalized_type or "deposit" in normalized_type:
                net_cash_flow += _safe_float(tx.amount)
            if "rut" in normalized_type or "withdraw" in normalized_type:
                net_cash_flow -= _safe_float(tx.amount)

        start = (page - 1) * page_size
        end = start + page_size
        items = [
            transaction_to_dto(tx, name_map.get(tx.investor_id, f"Investor {tx.investor_id}"))
            for tx in filtered[start:end]
        ]

        earliest_date = str(filtered[-1].date) if filtered else None
        latest_date = str(filtered[0].date) if filtered else None

        return TransactionReportDTO(
            summary=TransactionReportSummaryDTO(
                total_count=len(filtered),
                total_volume=total_volume,
                net_cash_flow=net_cash_flow,
                by_type=by_type,
                earliest_date=earliest_date,
                latest_date=latest_date,
            ),
            items=items,
            total=len(filtered),
            page=page,
            page_size=page_size,
        )

    return ApiResponse(data=runtime.read(_read))
