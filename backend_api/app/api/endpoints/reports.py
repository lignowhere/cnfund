import unicodedata
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response

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
from ...services.export_service import build_transactions_csv, build_transactions_pdf
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


def _parse_iso_date(value: str | None, field_name: str) -> date | None:
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} must be in YYYY-MM-DD format",
        ) from exc


def _normalize_date_range(start_date: str | None, end_date: str | None) -> tuple[date | None, date | None]:
    parsed_start = _parse_iso_date(start_date, "start_date")
    parsed_end = _parse_iso_date(end_date, "end_date")
    if parsed_start and parsed_end and parsed_start > parsed_end:
        parsed_start, parsed_end = parsed_end, parsed_start
    return parsed_start, parsed_end


def _is_deposit_type(tx_type: str) -> bool:
    normalized_type = _normalize_text(tx_type)
    return "nap" in normalized_type or "deposit" in normalized_type


def _is_withdraw_type(tx_type: str) -> bool:
    normalized_type = _normalize_text(tx_type)
    return (
        "rut" in normalized_type
        or "withdraw" in normalized_type
        or "rat" in normalized_type
    )


def _sort_transaction_key(tx) -> tuple[datetime, int]:
    return _to_datetime(tx.date), int(getattr(tx, "id", 0))


def _is_fee_type(tx_type: str) -> bool:
    normalized_type = _normalize_text(tx_type)
    return "phi" in normalized_type or "fee" in normalized_type


def _match_tx_type(tx, tx_type: str | None) -> bool:
    if not tx_type:
        return True
    wanted = _normalize_text(tx_type)
    return wanted in _normalize_text(tx.type)


def _match_base_filters(
    tx,
    investor_id: int | None,
    start_date: date | None,
    end_date: date | None,
) -> bool:
    tx_date = _to_datetime(tx.date).date()
    if investor_id is not None and tx.investor_id != investor_id:
        return False
    if start_date and tx_date < start_date:
        return False
    if end_date and tx_date > end_date:
        return False
    return True


def _resolve_period_bounds(
    transactions_asc,
    start_date: date | None,
    end_date: date | None,
) -> tuple[date | None, date | None]:
    if not transactions_asc:
        return start_date, end_date

    global_start = _to_datetime(transactions_asc[0].date).date()
    global_end = _to_datetime(transactions_asc[-1].date).date()
    period_start = start_date or global_start
    period_end = end_date or global_end
    return period_start, period_end


def _snapshot_units_and_nav(
    transactions_asc,
    investor_id: int | None,
    boundary_date: date,
    include_boundary: bool,
) -> tuple[float, float, float | None]:
    total_units = 0.0
    investor_units = 0.0
    latest_nav: float | None = None

    for tx in transactions_asc:
        tx_date = _to_datetime(tx.date).date()
        if include_boundary:
            if tx_date > boundary_date:
                break
        elif tx_date >= boundary_date:
            break

        units_delta = _safe_float(getattr(tx, "units_change", 0.0))
        total_units += units_delta
        if investor_id is None:
            investor_units = total_units
        elif tx.investor_id == investor_id:
            investor_units += units_delta

        latest_nav = _safe_float(getattr(tx, "nav", 0.0))

    return investor_units, total_units, latest_nav


def _compute_value(investor_units: float, total_units: float, nav_value: float | None) -> float:
    if nav_value is None or total_units <= 0:
        return 0.0
    unit_price = nav_value / total_units
    return investor_units * unit_price


def _first_non_zero_value_in_period(
    transactions_asc,
    investor_id: int | None,
    period_start: date,
    period_end: date,
) -> float:
    total_units = 0.0
    investor_units = 0.0
    latest_nav: float | None = None

    for tx in transactions_asc:
        tx_date = _to_datetime(tx.date).date()
        if tx_date > period_end:
            break

        units_delta = _safe_float(getattr(tx, "units_change", 0.0))
        total_units += units_delta
        if investor_id is None:
            investor_units = total_units
        elif tx.investor_id == investor_id:
            investor_units += units_delta
        latest_nav = _safe_float(getattr(tx, "nav", 0.0))

        if tx_date < period_start:
            continue

        current_value = _compute_value(investor_units, total_units, latest_nav)
        if current_value > 0:
            return current_value

    return 0.0


def _estimate_market_performance(
    transactions_asc,
    investor_id: int | None,
    period_start: date | None,
    period_end: date | None,
    net_cash_flow: float,
    fees_in_period: float,
) -> tuple[float, float]:
    if not period_start or not period_end or period_start > period_end:
        return 0.0, 0.0

    (
        start_investor_units,
        start_total_units,
        start_nav,
    ) = _snapshot_units_and_nav(
        transactions_asc=transactions_asc,
        investor_id=investor_id,
        boundary_date=period_start,
        include_boundary=False,
    )
    end_investor_units, end_total_units, end_nav = _snapshot_units_and_nav(
        transactions_asc=transactions_asc,
        investor_id=investor_id,
        boundary_date=period_end,
        include_boundary=True,
    )

    start_value = _compute_value(start_investor_units, start_total_units, start_nav)
    end_value = _compute_value(end_investor_units, end_total_units, end_nav)

    gross_profit_loss = (end_value - start_value) - net_cash_flow + fees_in_period
    percent_base = start_value
    if percent_base <= 0:
        percent_base = _first_non_zero_value_in_period(
            transactions_asc=transactions_asc,
            investor_id=investor_id,
            period_start=period_start,
            period_end=period_end,
        )

    gross_profit_loss_percent = (gross_profit_loss / percent_base) if percent_base > 0 else 0.0
    return gross_profit_loss, gross_profit_loss_percent


def _build_transaction_summary(
    transactions,
    transactions_asc,
    investor_id: int | None,
    period_start: date | None,
    period_end: date | None,
) -> TransactionReportSummaryDTO:
    by_type: dict[str, int] = {}
    total_volume = 0.0
    total_deposits = 0.0
    total_withdrawals = 0.0
    fees_in_period = 0.0

    for tx in transactions:
        by_type[tx.type] = by_type.get(tx.type, 0) + 1
        amount = _safe_float(tx.amount)
        total_volume += abs(amount)
        if _is_deposit_type(tx.type):
            total_deposits += abs(amount)
        elif _is_withdraw_type(tx.type):
            total_withdrawals += abs(amount)
        elif _is_fee_type(tx.type) and amount < 0:
            fees_in_period += abs(amount)

    net_cash_flow = total_deposits - total_withdrawals
    gross_profit_loss, gross_profit_loss_percent = _estimate_market_performance(
        transactions_asc=transactions_asc,
        investor_id=investor_id,
        period_start=period_start,
        period_end=period_end,
        net_cash_flow=net_cash_flow,
        fees_in_period=fees_in_period,
    )
    earliest_date = str(transactions[-1].date) if transactions else None
    latest_date = str(transactions[0].date) if transactions else None

    return TransactionReportSummaryDTO(
        total_count=len(transactions),
        total_volume=total_volume,
        net_cash_flow=net_cash_flow,
        total_deposits=total_deposits,
        total_withdrawals=total_withdrawals,
        gross_profit_loss=gross_profit_loss,
        gross_profit_loss_percent=gross_profit_loss_percent,
        by_type=by_type,
        earliest_date=earliest_date,
        latest_date=latest_date,
    )


def _prepare_transactions_data(
    manager,
    investor_id: int | None,
    tx_type: str | None,
    start_date: date | None,
    end_date: date | None,
):
    name_map = {inv.id: inv.name for inv in manager.investors}
    transactions_asc = sorted(manager.transactions, key=_sort_transaction_key)
    transactions_desc = sorted(transactions_asc, key=_sort_transaction_key, reverse=True)
    period_start, period_end = _resolve_period_bounds(
        transactions_asc=transactions_asc,
        start_date=start_date,
        end_date=end_date,
    )

    kpi_filtered = [
        tx
        for tx in transactions_desc
        if _match_base_filters(tx, investor_id=investor_id, start_date=start_date, end_date=end_date)
    ]
    filtered = [tx for tx in kpi_filtered if _match_tx_type(tx, tx_type)]

    summary = _build_transaction_summary(
        transactions=kpi_filtered,
        transactions_asc=transactions_asc,
        investor_id=investor_id,
        period_start=period_start,
        period_end=period_end,
    )
    return name_map, filtered, summary


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
                province_code=getattr(investor, "province_code", "") or "",
                province_name=getattr(investor, "province_name", "") or "",
                ward_code=getattr(investor, "ward_code", "") or "",
                ward_name=getattr(investor, "ward_name", "") or "",
                address_line=getattr(investor, "address_line", "") or "",
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
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    _user=Depends(require_read_access),
):
    normalized_start_date, normalized_end_date = _normalize_date_range(start_date, end_date)

    def _read(manager):
        name_map, filtered, summary = _prepare_transactions_data(
            manager=manager,
            investor_id=investor_id,
            tx_type=tx_type,
            start_date=normalized_start_date,
            end_date=normalized_end_date,
        )

        start = (page - 1) * page_size
        end = start + page_size
        items = [
            transaction_to_dto(tx, name_map.get(tx.investor_id, f"Investor {tx.investor_id}"))
            for tx in filtered[start:end]
        ]

        return TransactionReportDTO(
            summary=summary,
            items=items,
            total=len(filtered),
            page=page,
            page_size=page_size,
        )

    return ApiResponse(data=runtime.read(_read))


@router.get("/transactions/export")
def export_transactions(
    investor_id: int | None = Query(default=None, ge=0),
    tx_type: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    format: str = Query(default="csv"),
    _user=Depends(require_read_access),
):
    export_format = format.strip().lower()
    if export_format not in {"csv", "pdf"}:
        raise HTTPException(status_code=422, detail="format must be either csv or pdf")

    normalized_start_date, normalized_end_date = _normalize_date_range(start_date, end_date)

    def _read(manager):
        name_map, filtered, summary = _prepare_transactions_data(
            manager=manager,
            investor_id=investor_id,
            tx_type=tx_type,
            start_date=normalized_start_date,
            end_date=normalized_end_date,
        )
        generated_at = datetime.utcnow()

        if export_format == "pdf":
            content = build_transactions_pdf(
                transactions=filtered,
                name_map=name_map,
                summary=summary,
                start_date=normalized_start_date,
                end_date=normalized_end_date,
                generated_at=generated_at,
            )
            media_type = "application/pdf"
            extension = "pdf"
        else:
            content = build_transactions_csv(
                transactions=filtered,
                name_map=name_map,
                summary=summary,
                start_date=normalized_start_date,
                end_date=normalized_end_date,
            )
            media_type = "text/csv; charset=utf-8"
            extension = "csv"

        return {
            "content": content,
            "media_type": media_type,
            "extension": extension,
            "generated_at": generated_at,
        }

    payload = runtime.read(_read)
    filename_date = payload["generated_at"].strftime("%Y-%m-%d")
    filename = f"cnfund-transactions-{filename_date}.{payload['extension']}"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(
        content=payload["content"],
        media_type=payload["media_type"],
        headers=headers,
    )
