#!/usr/bin/env python3
"""
Comprehensive type safety fixes for string/integer conversion issues
This module provides robust type conversion utilities and fixes common type issues
"""

import pandas as pd
import streamlit as st
from typing import Any, Union, List, Dict, Optional
from datetime import datetime, date

def safe_int_conversion(value: Any, default: int = 0) -> int:
    """
    Safely convert any value to integer with comprehensive error handling
    
    Args:
        value: The value to convert
        default: Default value if conversion fails
        
    Returns:
        int: The converted integer value
    """
    if value is None:
        return default
    
    if isinstance(value, int):
        return value
    
    if isinstance(value, float):
        return int(value)
    
    if isinstance(value, str):
        # Handle common string representations
        value = value.strip()
        if value == '' or value.lower() in ('none', 'null', 'nan'):
            return default
        
        try:
            # Try direct conversion
            return int(value)
        except ValueError:
            try:
                # Try float first then int (handles "123.0" strings)
                return int(float(value))
            except (ValueError, OverflowError):
                print(f"Warning: Could not convert '{value}' to int, using default {default}")
                return default
    
    # Handle pandas/numpy types
    try:
        if hasattr(value, 'item'):  # numpy scalar
            return int(value.item())
        return int(value)
    except (ValueError, TypeError, OverflowError):
        print(f"Warning: Could not convert {type(value).__name__} '{value}' to int, using default {default}")
        return default

def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Safely convert any value to float with comprehensive error handling
    
    Args:
        value: The value to convert
        default: Default value if conversion fails
        
    Returns:
        float: The converted float value
    """
    if value is None:
        return default
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        value = value.strip()
        if value == '' or value.lower() in ('none', 'null', 'nan'):
            return default
        
        try:
            return float(value)
        except (ValueError, OverflowError):
            print(f"Warning: Could not convert '{value}' to float, using default {default}")
            return default
    
    # Handle pandas/numpy types
    try:
        if hasattr(value, 'item'):  # numpy scalar
            return float(value.item())
        return float(value)
    except (ValueError, TypeError, OverflowError):
        print(f"Warning: Could not convert {type(value).__name__} '{value}' to float, using default {default}")
        return default

def validate_investor_id(investor_id: Any) -> int:
    """
    Validate and convert investor ID to integer
    
    Args:
        investor_id: The investor ID to validate
        
    Returns:
        int: Valid integer investor ID
        
    Raises:
        ValueError: If investor_id cannot be converted to a valid integer
    """
    converted_id = safe_int_conversion(investor_id, -1)
    
    if converted_id < 0:
        raise ValueError(f"Invalid investor ID: {investor_id}. Must be a non-negative integer.")
    
    return converted_id

def sanitize_dataframe_types(df: pd.DataFrame, column_types: Dict[str, str]) -> pd.DataFrame:
    """
    Sanitize DataFrame column types to prevent string/integer issues
    
    Args:
        df: The DataFrame to sanitize
        column_types: Dictionary mapping column names to expected types
        
    Returns:
        pd.DataFrame: DataFrame with properly typed columns
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    for column, expected_type in column_types.items():
        if column not in df.columns:
            continue
            
        try:
            if expected_type == 'int':
                df[column] = df[column].apply(safe_int_conversion)
            elif expected_type == 'float':
                df[column] = df[column].apply(safe_float_conversion)
            elif expected_type == 'str':
                df[column] = df[column].astype(str)
            elif expected_type == 'bool':
                df[column] = df[column].astype(bool)
        except Exception as e:
            print(f"Warning: Could not convert column '{column}' to {expected_type}: {e}")
    
    return df

def fix_investor_options_type_safety(investors: List[Any]) -> Dict[str, int]:
    """
    Create investor options dictionary with guaranteed integer values
    
    Args:
        investors: List of investor objects
        
    Returns:
        Dict[str, int]: Safe investor options mapping
    """
    options = {}
    
    for investor in investors:
        try:
            # Ensure we have a proper investor object
            if not hasattr(investor, 'id') or not hasattr(investor, 'display_name'):
                continue
                
            if hasattr(investor, 'is_fund_manager') and investor.is_fund_manager:
                continue  # Skip fund manager
            
            # Safely convert ID to integer
            investor_id = safe_int_conversion(investor.id)
            if investor_id >= 0:  # Valid ID
                display_name = str(investor.display_name)
                options[display_name] = investor_id
                
        except Exception as e:
            print(f"Warning: Skipping investor due to error: {e}")
            continue
    
    return options

def fix_transaction_sorting_safety(transactions: List[Any]) -> List[Any]:
    """
    Ensure transaction IDs are integers for safe sorting
    
    Args:
        transactions: List of transaction objects
        
    Returns:
        List[Any]: Transactions with validated integer IDs
    """
    fixed_transactions = []
    
    for tx in transactions:
        try:
            # Ensure transaction has proper integer ID
            if hasattr(tx, 'id'):
                tx.id = safe_int_conversion(tx.id)
            
            # Ensure other numeric fields are properly typed
            if hasattr(tx, 'investor_id'):
                tx.investor_id = safe_int_conversion(tx.investor_id)
            if hasattr(tx, 'amount'):
                tx.amount = safe_float_conversion(tx.amount)
            if hasattr(tx, 'nav'):
                tx.nav = safe_float_conversion(tx.nav)
            if hasattr(tx, 'units_change'):
                tx.units_change = safe_float_conversion(tx.units_change)
            
            fixed_transactions.append(tx)
            
        except Exception as e:
            print(f"Warning: Skipping transaction due to error: {e}")
            continue
    
    return fixed_transactions

def safe_list_indexing(lst: List[Any], index: Any, default: Any = None) -> Any:
    """
    Safely access list elements with type conversion
    
    Args:
        lst: The list to access
        index: The index (will be converted to int)
        default: Default value if access fails
        
    Returns:
        Any: The list element or default value
    """
    try:
        int_index = safe_int_conversion(index)
        if 0 <= int_index < len(lst):
            return lst[int_index]
        return default
    except Exception:
        return default

def validate_session_state_types():
    """
    Validate and fix Streamlit session state type issues
    """
    if not hasattr(st, 'session_state'):
        return
    
    # Common session state variables that should be integers
    int_variables = [
        'selected_investor_id',
        'current_investor_id', 
        'investor_id',
        'selected_id'
    ]
    
    for var in int_variables:
        if var in st.session_state:
            try:
                st.session_state[var] = safe_int_conversion(st.session_state[var])
            except Exception as e:
                print(f"Warning: Could not fix session state variable '{var}': {e}")

# Fix common DataFrame loading issues
INVESTOR_COLUMN_TYPES = {
    'ID': 'int',
    'InvestorID': 'int', 
    'id': 'int',
    'investor_id': 'int',
    'Name': 'str',
    'Phone': 'str',
    'Address': 'str',
    'Email': 'str',
    'IsFundManager': 'bool',
    'is_fund_manager': 'bool'
}

TRANSACTION_COLUMN_TYPES = {
    'ID': 'int',
    'id': 'int',
    'InvestorID': 'int',
    'investor_id': 'int',
    'Type': 'str',
    'type': 'str',
    'Amount': 'float',
    'amount': 'float',
    'NAV': 'float',
    'nav': 'float',
    'UnitsChange': 'float',
    'units_change': 'float'
}

TRANCHE_COLUMN_TYPES = {
    'InvestorID': 'int',
    'investor_id': 'int',
    'TrancheID': 'str',
    'tranche_id': 'str',
    'EntryNAV': 'float',
    'entry_nav': 'float',
    'Units': 'float',
    'units': 'float',
    'HWM': 'float',
    'hwm': 'float',
    'OriginalEntryNAV': 'float',
    'original_entry_nav': 'float',
    'CumulativeFeesPaid': 'float',
    'cumulative_fees_paid': 'float',
    'OriginalInvestedValue': 'float',
    'original_invested_value': 'float',
    'InvestedValue': 'float',
    'invested_value': 'float'
}

FEE_RECORD_COLUMN_TYPES = {
    'ID': 'int',
    'id': 'int', 
    'InvestorID': 'int',
    'investor_id': 'int',
    'Period': 'str',
    'period': 'str',
    'FeeAmount': 'float',
    'fee_amount': 'float',
    'FeeUnits': 'float',
    'fee_units': 'float',
    'UnitsBefore': 'float',
    'units_before': 'float',
    'UnitsAfter': 'float',
    'units_after': 'float',
    'NAVPerUnit': 'float',
    'nav_per_unit': 'float',
    'Description': 'str',
    'description': 'str'
}

def apply_type_safety_fixes():
    """
    Apply all type safety fixes to the current session
    """
    print("🔧 Applying type safety fixes...")
    
    # Fix session state types
    validate_session_state_types()
    
    print("✅ Type safety fixes applied")

if __name__ == "__main__":
    # Test the functions
    print("Testing type safety functions...")
    
    # Test safe conversions
    assert safe_int_conversion("123") == 123
    assert safe_int_conversion("123.45") == 123
    assert safe_int_conversion("invalid", 999) == 999
    assert safe_int_conversion(None, 42) == 42
    
    assert safe_float_conversion("123.45") == 123.45
    assert safe_float_conversion("invalid", 999.0) == 999.0
    
    print("✅ All type safety tests passed")