from datetime import datetime

from ..schemas.fees import FeeRecordDTO
from ..schemas.investors import InvestorCardDTO, InvestorDTO
from ..schemas.nav import NavPointDTO
from ..schemas.transactions import TransactionCardDTO, TransactionDTO


def investor_to_dto(investor) -> InvestorDTO:
    return InvestorDTO(
        id=investor.id,
        name=investor.name,
        phone=investor.phone or "",
        address=investor.address or "",
        email=investor.email or "",
        join_date=investor.join_date,
        is_fund_manager=bool(investor.is_fund_manager),
    )


def investor_to_card_dto(investor, balance: float, profit: float, profit_percent: float) -> InvestorCardDTO:
    return InvestorCardDTO(
        id=investor.id,
        display_name=f"{investor.name} (ID: {investor.id})",
        phone=investor.phone or "",
        email=investor.email or "",
        current_value=balance,
        pnl=profit,
        pnl_percent=profit_percent,
    )


def transaction_to_dto(transaction, investor_name: str) -> TransactionDTO:
    return TransactionDTO(
        id=transaction.id,
        investor_id=transaction.investor_id,
        investor_name=investor_name,
        date=_to_datetime(transaction.date),
        type=transaction.type,
        amount=transaction.amount,
        nav=transaction.nav,
        units_change=transaction.units_change,
    )


def transaction_to_card_dto(transaction, investor_name: str) -> TransactionCardDTO:
    return TransactionCardDTO(
        id=transaction.id,
        investor_name=investor_name,
        type=transaction.type,
        amount=transaction.amount,
        nav=transaction.nav,
        date=_to_datetime(transaction.date),
        units_change=transaction.units_change,
    )


def nav_point_to_dto(nav_point: dict) -> NavPointDTO:
    return NavPointDTO(
        date=str(nav_point.get("date", "")),
        nav=float(nav_point.get("nav", 0)),
        type=str(nav_point.get("type", "")),
    )


def fee_record_to_dto(record) -> FeeRecordDTO:
    return FeeRecordDTO(
        id=record.id,
        period=record.period,
        investor_id=record.investor_id,
        fee_amount=record.fee_amount,
        fee_units=record.fee_units,
        calculation_date=str(record.calculation_date),
        description=record.description or "",
    )


def _to_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))

