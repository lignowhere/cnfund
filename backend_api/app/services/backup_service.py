from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from core.models import FeeRecord, Investor, Transaction, Tranche
from utils.type_safety_fixes import safe_float_conversion, safe_int_conversion

EXPORT_DIR = Path("exports")


def _as_date(value: Any):
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.notna(parsed):
        return parsed.date()
    return datetime.utcnow().date()


def _as_datetime(value: Any):
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.notna(parsed):
        as_dt = parsed.to_pydatetime()
        if as_dt.tzinfo is not None:
            return as_dt.replace(tzinfo=None)
        return as_dt
    return datetime.utcnow()


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


def list_local_backups(days: int = 30) -> list[dict[str, Any]]:
    EXPORT_DIR.mkdir(exist_ok=True)
    cutoff = datetime.now() - timedelta(days=days)
    items: list[dict[str, Any]] = []
    for path in EXPORT_DIR.glob("Fund_Export_*.xlsx"):
        stat = path.stat()
        modified = datetime.fromtimestamp(stat.st_mtime)
        if modified < cutoff:
            continue
        filename = path.name
        if "auto_" in filename:
            backup_type = "auto"
        elif "manual" in filename:
            backup_type = "manual"
        else:
            backup_type = "unknown"
        items.append(
            {
                "backup_id": filename,
                "backup_type": backup_type,
                "created_at": modified.isoformat(),
                "size_kb": round(stat.st_size / 1024, 1),
                "path": str(path),
            }
        )
    items.sort(key=lambda row: row["created_at"], reverse=True)
    return items


def trigger_manual_backup(fund_manager, description: str = "api_manual") -> dict[str, Any]:
    try:
        from integrations.auto_backup_personal import manual_backup

        success = manual_backup(fund_manager, description)
        if not success:
            raise RuntimeError("manual backup failed")
    except Exception as exc:
        raise RuntimeError(f"manual backup failed: {exc}") from exc

    backups = list_local_backups(days=365)
    if not backups:
        raise RuntimeError("backup completed but no local backup file found")
    return backups[0]


def restore_from_local_backup(
    fund_manager,
    backup_id: str,
    *,
    create_safety_backup: bool = True,
) -> dict[str, Any]:
    target = EXPORT_DIR / backup_id
    if not target.exists():
        raise FileNotFoundError(f"backup file not found: {backup_id}")

    if create_safety_backup:
        try:
            trigger_manual_backup(fund_manager, description="pre_restore_safety")
        except Exception:
            # Non-blocking: restore can still continue.
            pass

    excel_data = pd.read_excel(target, sheet_name=None)

    restored_sheets: list[str] = []

    investors: list[Investor] = []
    if "Investors" in excel_data:
        df = excel_data["Investors"].copy()
        df.columns = [str(col).strip().lower() for col in df.columns]
        for _, row in df.iterrows():
            try:
                investors.append(
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
        restored_sheets.append("Investors")

    tranches: list[Tranche] = []
    if "Tranches" in excel_data:
        df = excel_data["Tranches"].copy()
        df.columns = [str(col).strip().lower() for col in df.columns]
        for _, row in df.iterrows():
            try:
                entry_date = _as_datetime(row.get("entry_date"))
                entry_nav = safe_float_conversion(row.get("entry_nav", 0.0))
                units = safe_float_conversion(row.get("units", 0.0))
                original_entry_raw = row.get("original_entry_date")
                original_entry_date = (
                    _as_datetime(original_entry_raw)
                    if pd.notna(original_entry_raw)
                    else entry_date
                )
                tranche = Tranche(
                    investor_id=safe_int_conversion(row.get("investor_id")),
                    tranche_id=str(row.get("tranche_id", "")),
                    entry_date=entry_date,
                    entry_nav=entry_nav,
                    units=units,
                    hwm=safe_float_conversion(row.get("hwm", entry_nav)),
                    original_entry_date=original_entry_date,
                    original_entry_nav=safe_float_conversion(row.get("original_entry_nav", entry_nav)),
                    cumulative_fees_paid=safe_float_conversion(row.get("cumulative_fees_paid", 0.0)),
                    original_invested_value=safe_float_conversion(
                        row.get("original_invested_value", units * entry_nav)
                    ),
                )
                tranche.invested_value = safe_float_conversion(
                    row.get("invested_value", units * entry_nav)
                )
                tranches.append(tranche)
            except Exception:
                continue
        restored_sheets.append("Tranches")

    transactions: list[Transaction] = []
    if "Transactions" in excel_data:
        df = excel_data["Transactions"].copy()
        df.columns = [str(col).strip().lower() for col in df.columns]
        for _, row in df.iterrows():
            try:
                transactions.append(
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
        restored_sheets.append("Transactions")

    fee_records: list[FeeRecord] = []
    if "Fee_Records" in excel_data:
        df = excel_data["Fee_Records"].copy()
        df.columns = [str(col).strip().lower() for col in df.columns]
        for _, row in df.iterrows():
            try:
                fee_records.append(
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
        restored_sheets.append("Fee_Records")

    fund_manager.investors = investors
    fund_manager.tranches = tranches
    fund_manager.transactions = transactions
    fund_manager.fee_records = fee_records
    fund_manager._ensure_fund_manager_exists()

    if not fund_manager.save_data():
        raise RuntimeError("restore save_data failed")

    fund_manager.load_data()
    fund_manager._ensure_fund_manager_exists()

    return {
        "restored": True,
        "backup_id": backup_id,
        "restored_sheets": restored_sheets,
    }
