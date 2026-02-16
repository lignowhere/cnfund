from datetime import datetime, timedelta
from pathlib import Path
import re
from typing import Any

import pandas as pd

from core.models import FeeRecord, Investor, Transaction, Tranche
from helpers import parse_currency
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


def _canonical_name(name: Any) -> str:
    text = str(name or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [_canonical_name(col) for col in normalized.columns]
    return normalized


def _pick_sheet(excel_data: dict[str, pd.DataFrame], aliases: list[str]) -> pd.DataFrame | None:
    sheet_map = {_canonical_name(name): name for name in excel_data.keys()}
    for alias in aliases:
        key = _canonical_name(alias)
        if key in sheet_map:
            return excel_data[sheet_map[key]].copy()
    return None


def _as_number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return default

    try:
        direct = float(text)
        return direct
    except Exception:
        pass

    lowered = text.lower().replace("vnd", "").replace("đ", "").replace("₫", "").strip()
    is_percent = lowered.endswith("%")
    if is_percent:
        lowered = lowered[:-1].strip()

    lowered = lowered.replace(" ", "")
    if "," in lowered and "." in lowered:
        if lowered.rfind(",") > lowered.rfind("."):
            lowered = lowered.replace(".", "").replace(",", ".")
        else:
            lowered = lowered.replace(",", "")
    elif "," in lowered:
        parts = lowered.split(",")
        if len(parts) > 1 and all(part.lstrip("-").isdigit() for part in parts):
            if len(parts[-1]) == 3:
                lowered = "".join(parts)
            else:
                lowered = ".".join(parts)
        else:
            lowered = lowered.replace(",", "")

    lowered = re.sub(r"[^0-9\.\-]", "", lowered)
    if lowered in {"", "-", ".", "-."}:
        parsed = parse_currency(text)
    else:
        try:
            parsed = float(lowered)
        except Exception:
            parsed = parse_currency(text)

    if is_percent:
        return parsed / 100.0
    return parsed


def _row_pick(row: pd.Series, *keys: str) -> Any:
    for key in keys:
        canonical = _canonical_name(key)
        if canonical in row and pd.notna(row[canonical]):
            return row[canonical]
    return None


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


def _write_backup_excel(fund_manager, filename: str) -> Path:
    EXPORT_DIR.mkdir(exist_ok=True)
    output_path = EXPORT_DIR / filename

    investors_df = pd.DataFrame(
        [
            {
                "id": inv.id,
                "name": inv.name,
                "phone": inv.phone,
                "address": inv.address,
                "email": inv.email,
                "join_date": inv.join_date,
                "is_fund_manager": bool(inv.is_fund_manager),
            }
            for inv in getattr(fund_manager, "investors", [])
        ]
    )
    tranches_df = pd.DataFrame(
        [
            {
                "investor_id": t.investor_id,
                "tranche_id": t.tranche_id,
                "entry_date": t.entry_date,
                "entry_nav": t.entry_nav,
                "units": t.units,
                "hwm": getattr(t, "hwm", t.entry_nav),
                "original_entry_date": getattr(t, "original_entry_date", t.entry_date),
                "original_entry_nav": getattr(t, "original_entry_nav", t.entry_nav),
                "cumulative_fees_paid": getattr(t, "cumulative_fees_paid", 0.0),
                "original_invested_value": getattr(
                    t, "original_invested_value", float(t.units) * float(t.entry_nav)
                ),
                "invested_value": getattr(
                    t, "invested_value", float(t.units) * float(t.entry_nav)
                ),
            }
            for t in getattr(fund_manager, "tranches", [])
        ]
    )
    transactions_df = pd.DataFrame(
        [
            {
                "id": tx.id,
                "investor_id": tx.investor_id,
                "date": tx.date,
                "type": tx.type,
                "amount": tx.amount,
                "nav": tx.nav,
                "units_change": tx.units_change,
            }
            for tx in getattr(fund_manager, "transactions", [])
        ]
    )
    fees_df = pd.DataFrame(
        [
            {
                "id": fr.id,
                "period": fr.period,
                "investor_id": fr.investor_id,
                "fee_amount": fr.fee_amount,
                "fee_units": fr.fee_units,
                "calculation_date": fr.calculation_date,
                "units_before": fr.units_before,
                "units_after": fr.units_after,
                "nav_per_unit": fr.nav_per_unit,
                "description": fr.description,
            }
            for fr in getattr(fund_manager, "fee_records", [])
        ]
    )

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        investors_df.to_excel(writer, sheet_name="Investors", index=False)
        tranches_df.to_excel(writer, sheet_name="Tranches", index=False)
        transactions_df.to_excel(writer, sheet_name="Transactions", index=False)
        fees_df.to_excel(writer, sheet_name="Fee Records", index=False)

    return output_path


def trigger_manual_backup(fund_manager, description: str = "api_manual") -> dict[str, Any]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "_", description).strip("_")
    suffix = f"_{sanitized}" if sanitized else ""
    fallback_filename = f"Fund_Export_{timestamp}_manual{suffix}.xlsx"

    try:
        from integrations.auto_backup_personal import manual_backup

        success = manual_backup(fund_manager, description)
        if not success:
            _write_backup_excel(fund_manager, fallback_filename)
    except Exception:
        _write_backup_excel(fund_manager, fallback_filename)

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
    investors_sheet = _pick_sheet(excel_data, ["Investors", "Nha Dau Tu", "Nhà Đầu Tư"])
    if investors_sheet is not None:
        df = _normalize_columns(investors_sheet)
        for _, row in df.iterrows():
            try:
                investors.append(
                    Investor(
                        id=safe_int_conversion(_row_pick(row, "id")),
                        name=str(_row_pick(row, "name") or "").strip(),
                        phone=str(_row_pick(row, "phone") or "").strip(),
                        address=str(_row_pick(row, "address") or "").strip(),
                        email=str(_row_pick(row, "email") or "").strip(),
                        join_date=_as_date(_row_pick(row, "join_date")),
                        is_fund_manager=_as_bool(
                            _row_pick(row, "is_fund_manager", "is_fund_manager")
                        ),
                    )
                )
            except Exception:
                continue
        restored_sheets.append("Investors")

    tranches: list[Tranche] = []
    tranches_sheet = _pick_sheet(excel_data, ["Tranches", "Dot Goi Von", "Đợt Gọi Vốn"])
    if tranches_sheet is not None:
        df = _normalize_columns(tranches_sheet)
        for _, row in df.iterrows():
            try:
                entry_date = _as_datetime(_row_pick(row, "entry_date"))
                entry_nav = _as_number(_row_pick(row, "entry_nav"), 0.0)
                units = _as_number(_row_pick(row, "units"), 0.0)
                original_entry_raw = _row_pick(row, "original_entry_date")
                original_entry_date = (
                    _as_datetime(original_entry_raw)
                    if pd.notna(original_entry_raw)
                    else entry_date
                )
                tranche = Tranche(
                    investor_id=safe_int_conversion(_row_pick(row, "investor_id")),
                    tranche_id=str(_row_pick(row, "tranche_id") or ""),
                    entry_date=entry_date,
                    entry_nav=entry_nav,
                    units=units,
                    hwm=_as_number(_row_pick(row, "hwm"), entry_nav),
                    original_entry_date=original_entry_date,
                    original_entry_nav=_as_number(
                        _row_pick(row, "original_entry_nav"), entry_nav
                    ),
                    cumulative_fees_paid=_as_number(
                        _row_pick(row, "cumulative_fees_paid"), 0.0
                    ),
                    original_invested_value=_as_number(
                        _row_pick(row, "original_invested_value"), units * entry_nav
                    ),
                )
                tranche.invested_value = _as_number(
                    _row_pick(row, "invested_value"), units * entry_nav
                )
                tranches.append(tranche)
            except Exception:
                continue
        restored_sheets.append("Tranches")

    transactions: list[Transaction] = []
    transactions_sheet = _pick_sheet(excel_data, ["Transactions", "Giao Dich", "Giao Dịch"])
    if transactions_sheet is not None:
        df = _normalize_columns(transactions_sheet)
        for _, row in df.iterrows():
            try:
                transactions.append(
                    Transaction(
                        id=safe_int_conversion(_row_pick(row, "id")),
                        investor_id=safe_int_conversion(_row_pick(row, "investor_id")),
                        date=_as_datetime(_row_pick(row, "date", "transaction_date")),
                        type=str(_row_pick(row, "type", "transaction_type") or ""),
                        amount=_as_number(_row_pick(row, "amount", "net_amount"), 0.0),
                        nav=_as_number(_row_pick(row, "nav"), 0.0),
                        units_change=_as_number(_row_pick(row, "units_change", "units"), 0.0),
                    )
                )
            except Exception:
                continue
        restored_sheets.append("Transactions")

    fee_records: list[FeeRecord] = []
    fees_sheet = _pick_sheet(
        excel_data,
        ["Fee_Records", "Fee Records", "Phi Quan Ly", "Phí Quản Lý"],
    )
    if fees_sheet is not None:
        df = _normalize_columns(fees_sheet)
        for _, row in df.iterrows():
            try:
                fee_records.append(
                    FeeRecord(
                        id=safe_int_conversion(_row_pick(row, "id")),
                        period=str(_row_pick(row, "period", "fee_type") or ""),
                        investor_id=safe_int_conversion(_row_pick(row, "investor_id")),
                        fee_amount=_as_number(_row_pick(row, "fee_amount"), 0.0),
                        fee_units=_as_number(_row_pick(row, "fee_units"), 0.0),
                        calculation_date=_as_datetime(
                            _row_pick(row, "calculation_date", "fee_date")
                        ),
                        units_before=_as_number(_row_pick(row, "units_before"), 0.0),
                        units_after=_as_number(_row_pick(row, "units_after"), 0.0),
                        nav_per_unit=_as_number(_row_pick(row, "nav_per_unit", "nav_at_fee"), 0.0),
                        description=str(_row_pick(row, "description") or ""),
                    )
                )
            except Exception:
                continue
        restored_sheets.append("Fee Records")

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
