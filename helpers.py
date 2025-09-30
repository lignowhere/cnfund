"""
Helper functions for formatting and parsing
Replaces deleted utils.py
"""
import re

def validate_phone(phone):
    """Validate phone number"""
    if not phone:
        return True  # Optional field
    phone = str(phone).strip()
    # Vietnamese phone format: 10 digits starting with 0
    pattern = r'^0\d{9}$'
    return bool(re.match(pattern, phone))

def validate_email(email):
    """Validate email address"""
    if not email:
        return True  # Optional field
    email = str(email).strip()
    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def format_currency(value):
    """Format value as VND currency"""
    if value is None:
        return "0 đ"
    try:
        return f"{float(value):,.0f} đ"
    except (ValueError, TypeError):
        return "0 đ"

def format_phone(phone):
    """Format phone number"""
    if not phone:
        return ""
    phone = str(phone).strip()
    # Remove country code if present
    if phone.startswith('+84'):
        phone = '0' + phone[3:]
    elif phone.startswith('84'):
        phone = '0' + phone[2:]
    return phone

def format_percentage(value):
    """Format value as percentage"""
    if value is None:
        return "0%"
    try:
        return f"{float(value) * 100:.2f}%"
    except (ValueError, TypeError):
        return "0%"

def parse_currency(value_str):
    """Parse currency string to float"""
    if not value_str:
        return 0.0
    try:
        # Remove currency symbols and spaces
        cleaned = str(value_str).replace('đ', '').replace(',', '').replace('.', '').strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0

def highlight_profit_loss(value):
    """Return color for profit/loss highlighting"""
    if value is None:
        return "gray"
    try:
        val = float(value)
        if val > 0:
            return "green"
        elif val < 0:
            return "red"
        else:
            return "gray"
    except (ValueError, TypeError):
        return "gray"