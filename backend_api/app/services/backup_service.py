import base64
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
import re
from typing import Any

import pandas as pd

from config import HURDLE_RATE_ANNUAL, PERFORMANCE_FEE_RATE
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


def _normalize_phone_value(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return ""

    # Excel often serializes phone numbers as floats like 912345678.0.
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            if float(value).is_integer():
                text = str(int(value))
        except Exception:
            pass
    elif text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]

    digits = re.sub(r"\D+", "", text)
    if not digits:
        return ""
    if len(digits) == 9:
        return f"0{digits}"
    if len(digits) == 10 and digits.startswith("0"):
        return digits
    return digits


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
                "province_code": getattr(inv, "province_code", ""),
                "province_name": getattr(inv, "province_name", ""),
                "ward_code": getattr(inv, "ward_code", ""),
                "ward_name": getattr(inv, "ward_name", ""),
                "address_line": getattr(inv, "address_line", ""),
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
    fee_global_config = getattr(fund_manager, "fee_global_config", {}) or {}
    fee_overrides = getattr(fund_manager, "fee_investor_overrides", {}) or {}
    fee_global_df = pd.DataFrame(
        [
            {
                "id": 1,
                "performance_fee_rate": safe_float_conversion(
                    fee_global_config.get("performance_fee_rate", PERFORMANCE_FEE_RATE)
                ),
                "hurdle_rate_annual": safe_float_conversion(
                    fee_global_config.get("hurdle_rate_annual", HURDLE_RATE_ANNUAL)
                ),
                "updated_at": fee_global_config.get("updated_at"),
            }
        ]
    )
    fee_overrides_df = pd.DataFrame(
        [
            {
                "investor_id": safe_int_conversion(investor_id),
                "performance_fee_rate": (
                    _as_number(payload.get("performance_fee_rate"))
                    if payload.get("performance_fee_rate") is not None
                    else None
                ),
                "hurdle_rate_annual": (
                    _as_number(payload.get("hurdle_rate_annual"))
                    if payload.get("hurdle_rate_annual") is not None
                    else None
                ),
                "updated_at": payload.get("updated_at"),
            }
            for investor_id, payload in sorted(fee_overrides.items(), key=lambda item: int(item[0]))
        ]
    )

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        investors_df.to_excel(writer, sheet_name="Investors", index=False)
        tranches_df.to_excel(writer, sheet_name="Tranches", index=False)
        transactions_df.to_excel(writer, sheet_name="Transactions", index=False)
        fees_df.to_excel(writer, sheet_name="Fee Records", index=False)
        fee_global_df.to_excel(writer, sheet_name="Fee Config Global", index=False)
        fee_overrides_df.to_excel(writer, sheet_name="Fee Config Overrides", index=False)

    return output_path


def _normalize_drive_folder_id(raw_value: str | None) -> str | None:
    if not raw_value:
        return None
    value = raw_value.strip()
    if not value:
        return None

    match = re.search(r"/folders/([a-zA-Z0-9_-]+)", value)
    if match:
        return match.group(1)

    match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", value)
    if match:
        return match.group(1)

    return value


def _load_google_credentials():
    token_b64 = (
        os.getenv("GOOGLE_OAUTH_TOKEN_BASE64")
        or os.getenv("OAUTH_TOKEN_BASE64")
        or os.getenv("oauth_token_base64")
    )
    token_file = Path("token.pickle")
    token_encoded_file = Path("token_encoded.txt")

    creds = None
    if token_b64:
        try:
            creds = pickle.loads(base64.b64decode(token_b64.strip()))
        except Exception:
            creds = None
    elif token_file.exists():
        try:
            with token_file.open("rb") as f:
                creds = pickle.load(f)
        except Exception:
            creds = None
    elif token_encoded_file.exists():
        try:
            encoded = token_encoded_file.read_text(encoding="utf-8").strip()
            creds = pickle.loads(base64.b64decode(encoded))
        except Exception:
            creds = None

    if creds is None:
        return None, "missing_oauth_token"

    try:
        from google.auth.transport.requests import Request

        if getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
            creds.refresh(Request())
    except Exception as exc:
        return None, f"refresh_failed:{exc}"

    if not getattr(creds, "valid", False):
        return None, "invalid_oauth_token"

    return creds, None


def _upload_backup_to_google_drive(local_path: Path) -> dict[str, Any]:
    folder_id = _normalize_drive_folder_id(
        os.getenv("GOOGLE_DRIVE_FOLDER_ID") or os.getenv("DRIVE_FOLDER_ID")
    )
    if not folder_id:
        return {
            "uploaded": False,
            "reason": "missing_drive_folder_id",
            "file_id": None,
            "web_view_link": None,
        }

    creds, error = _load_google_credentials()
    if creds is None:
        return {
            "uploaded": False,
            "reason": error or "missing_credentials",
            "file_id": None,
            "web_view_link": None,
        }

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        service = build("drive", "v3", credentials=creds, cache_discovery=False)
        media = MediaFileUpload(
            str(local_path),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            resumable=False,
        )
        metadata = {"name": local_path.name, "parents": [folder_id]}
        uploaded = (
            service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id,name,webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
        return {
            "uploaded": True,
            "reason": None,
            "file_id": uploaded.get("id"),
            "web_view_link": uploaded.get("webViewLink"),
        }
    except Exception as exc:
        return {
            "uploaded": False,
            "reason": f"upload_failed:{exc}",
            "file_id": None,
            "web_view_link": None,
        }


def trigger_auto_backup_after_transaction(
    fund_manager, transaction_type: str = "transaction"
) -> dict[str, Any]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_type = re.sub(r"[^a-zA-Z0-9_-]+", "_", transaction_type).strip("_") or "transaction"
    filename = f"Fund_Export_{timestamp}_auto_{safe_type}.xlsx"

    local_path = _write_backup_excel(fund_manager, filename)
    drive_result = _upload_backup_to_google_drive(local_path)

    return {
        "backup_id": local_path.name,
        "created_at": datetime.now().isoformat(),
        "local_backup": True,
        "google_drive_uploaded": bool(drive_result.get("uploaded")),
        "google_drive_file_id": drive_result.get("file_id"),
        "google_drive_link": drive_result.get("web_view_link"),
        "google_drive_reason": drive_result.get("reason"),
    }


def trigger_manual_backup(fund_manager, description: str = "api_manual") -> dict[str, Any]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "_", description).strip("_")
    suffix = f"_{sanitized}" if sanitized else ""
    filename = f"Fund_Export_{timestamp}_manual{suffix}.xlsx"

    local_path = _write_backup_excel(fund_manager, filename)
    drive_result = _upload_backup_to_google_drive(local_path)

    return {
        "backup_id": local_path.name,
        "backup_type": "manual",
        "created_at": datetime.now().isoformat(),
        "local_backup": True,
        "google_drive_uploaded": bool(drive_result.get("uploaded")),
        "google_drive_file_id": drive_result.get("file_id"),
        "google_drive_link": drive_result.get("web_view_link"),
        "google_drive_reason": drive_result.get("reason"),
    }


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
                address_value = str(_row_pick(row, "address") or "").strip()
                address_line_value = str(_row_pick(row, "address_line") or "").strip() or address_value
                investors.append(
                    Investor(
                        id=safe_int_conversion(_row_pick(row, "id")),
                        name=str(_row_pick(row, "name") or "").strip(),
                        phone=_normalize_phone_value(_row_pick(row, "phone")),
                        address=address_value,
                        province_code=str(_row_pick(row, "province_code") or "").strip(),
                        province_name=str(_row_pick(row, "province_name") or "").strip(),
                        ward_code=str(_row_pick(row, "ward_code") or "").strip(),
                        ward_name=str(_row_pick(row, "ward_name") or "").strip(),
                        address_line=address_line_value,
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

    fee_global_config = {
        "performance_fee_rate": float(PERFORMANCE_FEE_RATE),
        "hurdle_rate_annual": float(HURDLE_RATE_ANNUAL),
        "updated_at": None,
    }
    fee_global_sheet = _pick_sheet(excel_data, ["Fee Config Global", "Fee_Config_Global"])
    if fee_global_sheet is not None and not fee_global_sheet.empty:
        df = _normalize_columns(fee_global_sheet)
        first_row = df.iloc[0]
        perf_rate = _as_number(_row_pick(first_row, "performance_fee_rate"), PERFORMANCE_FEE_RATE)
        hurdle_rate = _as_number(_row_pick(first_row, "hurdle_rate_annual"), HURDLE_RATE_ANNUAL)
        if 0 <= perf_rate <= 1:
            fee_global_config["performance_fee_rate"] = perf_rate
        if 0 <= hurdle_rate <= 1:
            fee_global_config["hurdle_rate_annual"] = hurdle_rate
        fee_global_config["updated_at"] = _row_pick(first_row, "updated_at")
        restored_sheets.append("Fee Config Global")

    fee_investor_overrides: dict[int, dict[str, Any]] = {}
    fee_overrides_sheet = _pick_sheet(excel_data, ["Fee Config Overrides", "Fee_Config_Overrides"])
    if fee_overrides_sheet is not None and not fee_overrides_sheet.empty:
        df = _normalize_columns(fee_overrides_sheet)
        for _, row in df.iterrows():
            investor_id_raw = _row_pick(row, "investor_id")
            if investor_id_raw is None:
                continue
            investor_id = safe_int_conversion(investor_id_raw)
            perf_rate_raw = _row_pick(row, "performance_fee_rate")
            hurdle_rate_raw = _row_pick(row, "hurdle_rate_annual")
            perf_rate = _as_number(perf_rate_raw) if perf_rate_raw is not None else None
            hurdle_rate = _as_number(hurdle_rate_raw) if hurdle_rate_raw is not None else None
            if perf_rate is not None and not (0 <= perf_rate <= 1):
                perf_rate = None
            if hurdle_rate is not None and not (0 <= hurdle_rate <= 1):
                hurdle_rate = None
            fee_investor_overrides[investor_id] = {
                "performance_fee_rate": perf_rate,
                "hurdle_rate_annual": hurdle_rate,
                "updated_at": _row_pick(row, "updated_at"),
            }
        restored_sheets.append("Fee Config Overrides")

    fund_manager.investors = investors
    fund_manager.tranches = tranches
    fund_manager.transactions = transactions
    fund_manager.fee_records = fee_records
    fund_manager.fee_global_config = fee_global_config
    fund_manager.fee_investor_overrides = fee_investor_overrides
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
