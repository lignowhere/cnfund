#!/usr/bin/env python3
"""
PostgreSQL data handler for CNFund business data.

This handler persists the same domain objects used by EnhancedFundManager:
- Investor
- Tranche
- Transaction
- FeeRecord
"""

from __future__ import annotations

import os
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
    func,
    select,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .models import FeeRecord, Investor, Transaction, Tranche
from utils.type_safety_fixes import safe_float_conversion, safe_int_conversion


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


def _as_date(value: Any, fallback: Optional[date] = None) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.notna(parsed):
            return parsed.date()
    except Exception:
        pass
    return fallback or date.today()


def _as_datetime(value: Any, fallback: Optional[datetime] = None) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.replace(tzinfo=None)
        return value
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.notna(parsed):
            as_dt = parsed.to_pydatetime()
            if as_dt.tzinfo is not None:
                return as_dt.replace(tzinfo=None)
            return as_dt
    except Exception:
        pass
    return fallback or datetime.utcnow()


def _as_bool(value: Any, fallback: bool = False) -> bool:
    if value is None:
        return fallback
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off", "", "nan", "none"}:
        return False
    return fallback


class Base(DeclarativeBase):
    pass


class InvestorRow(Base):
    __tablename__ = "fund_investors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(64), default="")
    address: Mapped[str] = mapped_column(String(255), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    join_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_fund_manager: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class TrancheRow(Base):
    __tablename__ = "fund_tranches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    investor_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    tranche_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    entry_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    entry_nav: Mapped[float] = mapped_column(Float, nullable=False)
    units: Mapped[float] = mapped_column(Float, nullable=False)
    hwm: Mapped[float] = mapped_column(Float, nullable=False)
    original_entry_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    original_entry_nav: Mapped[float] = mapped_column(Float, nullable=False)
    cumulative_fees_paid: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    original_invested_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    invested_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class TransactionRow(Base):
    __tablename__ = "fund_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investor_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    nav: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    units_change: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class FeeRecordRow(Base):
    __tablename__ = "fund_fee_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    investor_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    fee_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fee_units: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    calculation_date: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    units_before: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    units_after: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    nav_per_unit: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    description: Mapped[str] = mapped_column(String(1024), nullable=False, default="")


class PostgresDataHandler:
    """
    SQL-backed data handler compatible with EnhancedFundManager.
    """

    def __init__(self, database_url: Optional[str] = None):
        self.connected = True
        self._lock = threading.Lock()
        self._session_factory: Optional[sessionmaker] = None

        raw_url = database_url or os.getenv("API_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not raw_url:
            raise RuntimeError("Missing API_DATABASE_URL for postgres data source")

        self.database_url = _normalize_database_url(raw_url)
        self.engine = create_engine(self.database_url, future=True, pool_pre_ping=True)
        self._session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)

        try:
            Base.metadata.create_all(self.engine)
            self._bootstrap_from_csv_if_needed()
        except Exception:
            self.connected = False
            raise

    def reconnect(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.connected = True
            return True
        except Exception:
            self.connected = False
            return False

    def _session(self) -> Session:
        if self._session_factory is None:
            raise RuntimeError("Session factory is not initialized")
        return self._session_factory()

    def _is_empty(self) -> bool:
        with self._session() as session:
            checks = [
                session.scalar(select(func.count()).select_from(InvestorRow.__table__)),
                session.scalar(select(func.count()).select_from(TrancheRow.__table__)),
                session.scalar(select(func.count()).select_from(TransactionRow.__table__)),
                session.scalar(select(func.count()).select_from(FeeRecordRow.__table__)),
            ]
        return all(int(item or 0) == 0 for item in checks)

    def _bootstrap_from_csv_if_needed(self) -> None:
        should_bootstrap = os.getenv("API_POSTGRES_BOOTSTRAP_FROM_CSV", "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if not should_bootstrap or not self._is_empty():
            return

        seed_dir = os.getenv("API_POSTGRES_SEED_DIR", "").strip()
        candidate_dirs = [Path(seed_dir)] if seed_dir else []
        candidate_dirs += [Path("backend_api/data"), Path("data")]
        source_dir = next((path for path in candidate_dirs if path.exists()), None)
        if source_dir is None:
            return

        investors = self._read_investors_csv(source_dir / "investors.csv")
        tranches = self._read_tranches_csv(source_dir / "tranches.csv")
        transactions = self._read_transactions_csv(source_dir / "transactions.csv")
        fee_records = self._read_fee_records_csv(source_dir / "fee_records.csv")

        if any([investors, tranches, transactions, fee_records]):
            self.save_all_data_enhanced(investors, tranches, transactions, fee_records)

    def _read_investors_csv(self, path: Path) -> List[Investor]:
        if not path.exists():
            return []
        df = pd.read_csv(path, dtype={"phone": "str"})
        if df.empty:
            return []
        df.columns = df.columns.str.lower()
        if "join_date" not in df.columns and "joindate" in df.columns:
            df["join_date"] = df["joindate"]
        if "join_date" not in df.columns:
            df["join_date"] = date.today()
        if "is_fund_manager" not in df.columns and "isfundmanager" in df.columns:
            df["is_fund_manager"] = df["isfundmanager"]
        if "is_fund_manager" not in df.columns:
            df["is_fund_manager"] = False

        rows: List[Investor] = []
        for _, row in df.iterrows():
            try:
                rows.append(
                    Investor(
                        id=safe_int_conversion(row.get("id")),
                        name=str(row.get("name", "")).strip(),
                        phone=str(row.get("phone", "")).strip(),
                        address=str(row.get("address", "")).strip(),
                        email=str(row.get("email", "")).strip(),
                        join_date=_as_date(row.get("join_date")),
                        is_fund_manager=_as_bool(row.get("is_fund_manager", False)),
                    )
                )
            except Exception:
                continue
        return rows

    def _read_tranches_csv(self, path: Path) -> List[Tranche]:
        if not path.exists():
            return []
        df = pd.read_csv(path)
        if df.empty:
            return []
        df.columns = df.columns.str.lower()
        rows: List[Tranche] = []
        for _, row in df.iterrows():
            try:
                entry_date = _as_datetime(row.get("entry_date"))
                entry_nav = safe_float_conversion(row.get("entry_nav", 0))
                units = safe_float_conversion(row.get("units", 0))
                original_invested_value = safe_float_conversion(
                    row.get("original_invested_value", units * entry_nav)
                )
                tranche = Tranche(
                    investor_id=safe_int_conversion(row.get("investor_id")),
                    tranche_id=str(row.get("tranche_id", "")),
                    entry_date=entry_date,
                    entry_nav=entry_nav,
                    units=units,
                    hwm=safe_float_conversion(row.get("hwm", entry_nav)),
                    original_entry_date=_as_datetime(row.get("original_entry_date"), fallback=entry_date),
                    original_entry_nav=safe_float_conversion(row.get("original_entry_nav", entry_nav)),
                    cumulative_fees_paid=safe_float_conversion(row.get("cumulative_fees_paid", 0.0)),
                    original_invested_value=original_invested_value,
                )
                tranche.invested_value = safe_float_conversion(
                    row.get("invested_value", units * entry_nav)
                )
                rows.append(tranche)
            except Exception:
                continue
        return rows

    def _read_transactions_csv(self, path: Path) -> List[Transaction]:
        if not path.exists():
            return []
        df = pd.read_csv(path)
        if df.empty:
            return []
        df.columns = df.columns.str.lower()
        rows: List[Transaction] = []
        for _, row in df.iterrows():
            try:
                rows.append(
                    Transaction(
                        id=safe_int_conversion(row.get("id")),
                        investor_id=safe_int_conversion(row.get("investor_id")),
                        date=_as_datetime(row.get("date")),
                        type=str(row.get("type", "")),
                        amount=safe_float_conversion(row.get("amount", 0.0)),
                        nav=safe_float_conversion(row.get("nav", 0.0)),
                        units_change=safe_float_conversion(row.get("units_change", 0.0)),
                    )
                )
            except Exception:
                continue
        return rows

    def _read_fee_records_csv(self, path: Path) -> List[FeeRecord]:
        if not path.exists():
            return []
        df = pd.read_csv(path)
        if df.empty:
            return []
        df.columns = df.columns.str.lower()
        rows: List[FeeRecord] = []
        for _, row in df.iterrows():
            try:
                rows.append(
                    FeeRecord(
                        id=safe_int_conversion(row.get("id")),
                        period=str(row.get("period", "")),
                        investor_id=safe_int_conversion(row.get("investor_id")),
                        fee_amount=safe_float_conversion(row.get("fee_amount", 0.0)),
                        fee_units=safe_float_conversion(row.get("fee_units", 0.0)),
                        calculation_date=_as_datetime(row.get("calculation_date")),
                        units_before=safe_float_conversion(row.get("units_before", 0.0)),
                        units_after=safe_float_conversion(row.get("units_after", 0.0)),
                        nav_per_unit=safe_float_conversion(row.get("nav_per_unit", 0.0)),
                        description=str(row.get("description", "")),
                    )
                )
            except Exception:
                continue
        return rows

    # Load methods
    def load_investors(self) -> List[Investor]:
        with self._session() as session:
            rows = session.execute(select(InvestorRow).order_by(InvestorRow.id.asc())).scalars().all()
        return [
            Investor(
                id=row.id,
                name=row.name,
                phone=row.phone or "",
                address=row.address or "",
                email=row.email or "",
                join_date=row.join_date,
                is_fund_manager=bool(row.is_fund_manager),
            )
            for row in rows
        ]

    def load_tranches(self) -> List[Tranche]:
        with self._session() as session:
            rows = session.execute(
                select(TrancheRow).order_by(TrancheRow.entry_date.asc(), TrancheRow.id.asc())
            ).scalars().all()
        result: List[Tranche] = []
        for row in rows:
            tranche = Tranche(
                investor_id=row.investor_id,
                tranche_id=row.tranche_id,
                entry_date=row.entry_date,
                entry_nav=row.entry_nav,
                units=row.units,
                hwm=row.hwm,
                original_entry_date=row.original_entry_date,
                original_entry_nav=row.original_entry_nav,
                cumulative_fees_paid=row.cumulative_fees_paid,
                original_invested_value=row.original_invested_value,
            )
            tranche.invested_value = row.invested_value
            result.append(tranche)
        return result

    def load_transactions(self) -> List[Transaction]:
        with self._session() as session:
            rows = session.execute(
                select(TransactionRow).order_by(TransactionRow.date.asc(), TransactionRow.id.asc())
            ).scalars().all()
        return [
            Transaction(
                id=row.id,
                investor_id=row.investor_id,
                date=row.date,
                type=row.type,
                amount=row.amount,
                nav=row.nav,
                units_change=row.units_change,
            )
            for row in rows
        ]

    def load_fee_records(self) -> List[FeeRecord]:
        with self._session() as session:
            rows = session.execute(
                select(FeeRecordRow).order_by(FeeRecordRow.id.asc())
            ).scalars().all()
        return [
            FeeRecord(
                id=row.id,
                period=row.period,
                investor_id=row.investor_id,
                fee_amount=row.fee_amount,
                fee_units=row.fee_units,
                calculation_date=row.calculation_date,
                units_before=row.units_before,
                units_after=row.units_after,
                nav_per_unit=row.nav_per_unit,
                description=row.description or "",
            )
            for row in rows
        ]

    # Save methods
    def save_all_data_enhanced(
        self,
        investors: List[Investor],
        tranches: List[Tranche],
        transactions: List[Transaction],
        fee_records: List[FeeRecord],
    ) -> bool:
        try:
            with self._lock:
                with self.engine.begin() as conn:
                    conn.execute(text("DELETE FROM fund_fee_records"))
                    conn.execute(text("DELETE FROM fund_transactions"))
                    conn.execute(text("DELETE FROM fund_tranches"))
                    conn.execute(text("DELETE FROM fund_investors"))

                    if investors:
                        conn.execute(
                            InvestorRow.__table__.insert(),
                            [
                                {
                                    "id": safe_int_conversion(inv.id),
                                    "name": str(inv.name).strip(),
                                    "phone": str(getattr(inv, "phone", "") or "").strip(),
                                    "address": str(getattr(inv, "address", "") or "").strip(),
                                    "email": str(getattr(inv, "email", "") or "").strip(),
                                    "join_date": _as_date(getattr(inv, "join_date", None)),
                                    "is_fund_manager": bool(getattr(inv, "is_fund_manager", False)),
                                }
                                for inv in investors
                            ],
                        )

                    if tranches:
                        conn.execute(
                            TrancheRow.__table__.insert(),
                            [
                                {
                                    "investor_id": safe_int_conversion(t.investor_id),
                                    "tranche_id": str(t.tranche_id),
                                    "entry_date": _as_datetime(t.entry_date),
                                    "entry_nav": safe_float_conversion(t.entry_nav),
                                    "units": safe_float_conversion(t.units),
                                    "hwm": safe_float_conversion(getattr(t, "hwm", t.entry_nav)),
                                    "original_entry_date": _as_datetime(
                                        getattr(t, "original_entry_date", t.entry_date)
                                    ),
                                    "original_entry_nav": safe_float_conversion(
                                        getattr(t, "original_entry_nav", t.entry_nav)
                                    ),
                                    "cumulative_fees_paid": safe_float_conversion(
                                        getattr(t, "cumulative_fees_paid", 0.0)
                                    ),
                                    "original_invested_value": safe_float_conversion(
                                        getattr(
                                            t,
                                            "original_invested_value",
                                            safe_float_conversion(t.units)
                                            * safe_float_conversion(t.entry_nav),
                                        )
                                    ),
                                    "invested_value": safe_float_conversion(
                                        getattr(
                                            t,
                                            "invested_value",
                                            safe_float_conversion(t.units)
                                            * safe_float_conversion(t.entry_nav),
                                        )
                                    ),
                                }
                                for t in tranches
                            ],
                        )

                    if transactions:
                        conn.execute(
                            TransactionRow.__table__.insert(),
                            [
                                {
                                    "id": safe_int_conversion(tx.id),
                                    "investor_id": safe_int_conversion(tx.investor_id),
                                    "date": _as_datetime(tx.date),
                                    "type": str(tx.type),
                                    "amount": safe_float_conversion(tx.amount),
                                    "nav": safe_float_conversion(tx.nav),
                                    "units_change": safe_float_conversion(tx.units_change),
                                }
                                for tx in transactions
                            ],
                        )

                    if fee_records:
                        conn.execute(
                            FeeRecordRow.__table__.insert(),
                            [
                                {
                                    "id": safe_int_conversion(fr.id),
                                    "period": str(fr.period),
                                    "investor_id": safe_int_conversion(fr.investor_id),
                                    "fee_amount": safe_float_conversion(fr.fee_amount),
                                    "fee_units": safe_float_conversion(fr.fee_units),
                                    "calculation_date": _as_datetime(fr.calculation_date),
                                    "units_before": safe_float_conversion(fr.units_before),
                                    "units_after": safe_float_conversion(fr.units_after),
                                    "nav_per_unit": safe_float_conversion(fr.nav_per_unit),
                                    "description": str(getattr(fr, "description", "") or ""),
                                }
                                for fr in fee_records
                            ],
                        )

            self.connected = True
            return True
        except Exception:
            self.connected = False
            return False

    def create_backup(self) -> Optional[str]:
        # Backups are handled by backup service (xlsx export + volume/DB backup).
        return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    def get_database_stats(self) -> Dict[str, Any]:
        try:
            investors = self.load_investors()
            tranches = self.load_tranches()
            transactions = self.load_transactions()
            fee_records = self.load_fee_records()
            nav_transactions = [t for t in transactions if t.nav and t.nav > 0]
            latest_nav = None
            latest_nav_date = None
            if nav_transactions:
                latest = max(nav_transactions, key=lambda t: (t.date, t.id))
                latest_nav = latest.nav
                latest_nav_date = latest.date.isoformat()
            return {
                "connected": self.connected,
                "storage_type": "PostgreSQL",
                "table_counts": {
                    "investors": len(investors),
                    "tranches": len(tranches),
                    "transactions": len(transactions),
                    "fee_records": len(fee_records),
                },
                "latest_nav": latest_nav,
                "latest_nav_date": latest_nav_date,
            }
        except Exception as exc:
            return {"connected": False, "error": str(exc)}

    def health_check(self) -> Dict[str, Any]:
        return self.get_database_stats()
