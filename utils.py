import pandas as pd
import numpy as np
from config import CURRENCY_SYMBOL, EPSILON

def format_currency(amount) -> str:
    """Format currency"""
    if pd.isna(amount) or amount is None:
        return f"0{CURRENCY_SYMBOL}"
    try:
        return f"{float(amount):,.0f}{CURRENCY_SYMBOL}"
    except (ValueError, TypeError):
        return f"0{CURRENCY_SYMBOL}"

def parse_currency(s) -> float:
    """Parse currency string"""
    if isinstance(s, (int, float)):
        return float(s) if not pd.isna(s) else 0.0
    if not isinstance(s, str):
        return 0.0
    try:
        cleaned = s.replace(CURRENCY_SYMBOL, '').replace(',', '').strip()
        return float(cleaned) if cleaned and cleaned != 'N/A' else 0.0
    except (ValueError, AttributeError):
        return 0.0

def format_percentage(value, decimal_places: int = 2) -> str:
    """Format percentage"""
    if pd.isna(value) or value is None:
        return "N/A"
    try:
        return f"{float(value) * 100:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return "N/A"

def format_phone(phone) -> str:
    """Format phone"""
    if pd.isna(phone) or phone == "" or phone == "None":
        return ""
    return str(phone).zfill(10) if str(phone).isdigit() else str(phone)

def highlight_profit_loss(val):
    """CSS styling cho profit/loss"""
    try:
        if isinstance(val, str):
            num_val = parse_currency(val)
        else:
            num_val = float(val)
        
        if num_val > EPSILON:
            return 'color: green; font-weight: bold'
        elif num_val < -EPSILON:
            return 'color: red; font-weight: bold'
        else:
            return 'color: black'
    except:
        return ''

def validate_email(email: str) -> bool:
    """Validate email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) if email else True

def validate_phone(phone: str) -> bool:
    """Validate phone"""
    if not phone:
        return True
    return phone.startswith('0') and phone.isdigit() and len(phone) in [10, 11]
