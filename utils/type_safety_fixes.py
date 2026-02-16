#!/usr/bin/env python3
"""
Type safety utilities used by backend and data handlers.
"""

from typing import Any, Dict, List

import pandas as pd


def safe_int_conversion(value: Any, default: int = 0) -> int:
    """Safely convert any value to int."""
    if value is None:
        return default

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        value = value.strip()
        if value == "" or value.lower() in ("none", "null", "nan"):
            return default
        try:
            return int(value)
        except ValueError:
            try:
                return int(float(value))
            except (ValueError, OverflowError):
                print(f"Warning: Could not convert '{value}' to int, using default {default}")
                return default

    try:
        if hasattr(value, "item"):
            return int(value.item())
        return int(value)
    except (ValueError, TypeError, OverflowError):
        print(
            f"Warning: Could not convert {type(value).__name__} '{value}' to int, using default {default}"
        )
        return default


def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """Safely convert any value to float."""
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        value = value.strip()
        if value == "" or value.lower() in ("none", "null", "nan"):
            return default
        try:
            return float(value)
        except (ValueError, OverflowError):
            print(f"Warning: Could not convert '{value}' to float, using default {default}")
            return default

    try:
        if hasattr(value, "item"):
            return float(value.item())
        return float(value)
    except (ValueError, TypeError, OverflowError):
        print(
            f"Warning: Could not convert {type(value).__name__} '{value}' to float, using default {default}"
        )
        return default


def validate_investor_id(investor_id: Any) -> int:
    """Validate and convert investor ID to a non-negative integer."""
    converted_id = safe_int_conversion(investor_id, -1)
    if converted_id < 0:
        raise ValueError(f"Invalid investor ID: {investor_id}. Must be a non-negative integer.")
    return converted_id


def sanitize_dataframe_types(df: pd.DataFrame, column_types: Dict[str, str]) -> pd.DataFrame:
    """Sanitize DataFrame column types."""
    if df.empty:
        return df

    normalized = df.copy()
    for column, expected_type in column_types.items():
        if column not in normalized.columns:
            continue
        try:
            if expected_type == "int":
                normalized[column] = normalized[column].apply(safe_int_conversion)
            elif expected_type == "float":
                normalized[column] = normalized[column].apply(safe_float_conversion)
            elif expected_type == "str":
                normalized[column] = normalized[column].astype(str)
            elif expected_type == "bool":
                normalized[column] = normalized[column].astype(bool)
        except Exception as exc:
            print(f"Warning: Could not convert column '{column}' to {expected_type}: {exc}")

    return normalized


def fix_investor_options_type_safety(investors: List[Any]) -> Dict[str, int]:
    """Create investor options dictionary with guaranteed integer values."""
    options: Dict[str, int] = {}
    for investor in investors:
        try:
            if not hasattr(investor, "id") or not hasattr(investor, "display_name"):
                continue
            if hasattr(investor, "is_fund_manager") and investor.is_fund_manager:
                continue
            investor_id = safe_int_conversion(investor.id)
            if investor_id >= 0:
                options[str(investor.display_name)] = investor_id
        except Exception as exc:
            print(f"Warning: Skipping investor due to error: {exc}")
    return options


def fix_transaction_sorting_safety(transactions: List[Any]) -> List[Any]:
    """Ensure transaction numeric fields are safe for sorting/math."""
    fixed_transactions: List[Any] = []
    for tx in transactions:
        try:
            if hasattr(tx, "id"):
                tx.id = safe_int_conversion(tx.id)
            if hasattr(tx, "investor_id"):
                tx.investor_id = safe_int_conversion(tx.investor_id)
            if hasattr(tx, "amount"):
                tx.amount = safe_float_conversion(tx.amount)
            if hasattr(tx, "nav"):
                tx.nav = safe_float_conversion(tx.nav)
            if hasattr(tx, "units_change"):
                tx.units_change = safe_float_conversion(tx.units_change)
            fixed_transactions.append(tx)
        except Exception as exc:
            print(f"Warning: Skipping transaction due to error: {exc}")
    return fixed_transactions


def safe_list_indexing(lst: List[Any], index: Any, default: Any = None) -> Any:
    """Safely access list elements with type conversion."""
    try:
        int_index = safe_int_conversion(index)
        if 0 <= int_index < len(lst):
            return lst[int_index]
        return default
    except Exception:
        return default


def validate_session_state_types() -> None:
    """Legacy compatibility no-op after Streamlit removal."""
    return None


INVESTOR_COLUMN_TYPES = {
    "ID": "int",
    "InvestorID": "int",
    "id": "int",
    "investor_id": "int",
    "Name": "str",
    "Phone": "str",
    "Address": "str",
    "Email": "str",
    "IsFundManager": "bool",
    "is_fund_manager": "bool",
}

TRANSACTION_COLUMN_TYPES = {
    "ID": "int",
    "id": "int",
    "InvestorID": "int",
    "investor_id": "int",
    "Type": "str",
    "type": "str",
    "Amount": "float",
    "amount": "float",
    "NAV": "float",
    "nav": "float",
    "UnitsChange": "float",
    "units_change": "float",
}

TRANCHE_COLUMN_TYPES = {
    "InvestorID": "int",
    "investor_id": "int",
    "TrancheID": "str",
    "tranche_id": "str",
    "EntryNAV": "float",
    "entry_nav": "float",
    "Units": "float",
    "units": "float",
    "HWM": "float",
    "hwm": "float",
    "OriginalEntryNAV": "float",
    "original_entry_nav": "float",
    "CumulativeFeesPaid": "float",
    "cumulative_fees_paid": "float",
    "OriginalInvestedValue": "float",
    "original_invested_value": "float",
    "InvestedValue": "float",
    "invested_value": "float",
}

FEE_RECORD_COLUMN_TYPES = {
    "ID": "int",
    "id": "int",
    "InvestorID": "int",
    "investor_id": "int",
    "Period": "str",
    "period": "str",
    "FeeAmount": "float",
    "fee_amount": "float",
    "FeeUnits": "float",
    "fee_units": "float",
    "UnitsBefore": "float",
    "units_before": "float",
    "UnitsAfter": "float",
    "units_after": "float",
    "NAVPerUnit": "float",
    "nav_per_unit": "float",
    "Description": "str",
    "description": "str",
}


def apply_type_safety_fixes() -> None:
    """Entry-point kept for backward compatibility."""
    print("Applying type safety fixes...")
    validate_session_state_types()
    print("Type safety fixes applied")


if __name__ == "__main__":
    print("Testing type safety functions...")
    assert safe_int_conversion("123") == 123
    assert safe_int_conversion("123.45") == 123
    assert safe_int_conversion("invalid", 999) == 999
    assert safe_int_conversion(None, 42) == 42

    assert safe_float_conversion("123.45") == 123.45
    assert safe_float_conversion("invalid", 999.0) == 999.0

    print("All type safety tests passed")
