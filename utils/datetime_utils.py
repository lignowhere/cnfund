#!/usr/bin/env python3
"""
Datetime utilities for safe timezone-aware datetime operations
"""
from datetime import datetime, date, timedelta
from .timezone_manager import TimezoneManager
from typing import Union

def safe_datetime_subtract(dt1: datetime, dt2: datetime) -> timedelta:
    """
    Safely subtract two datetime objects, handling timezone awareness
    
    Args:
        dt1: First datetime (to subtract from)
        dt2: Second datetime (to subtract)
        
    Returns:
        timedelta: The difference between the two datetimes
    """
    # Ensure both datetimes are timezone-aware and in the same timezone
    dt1_normalized = TimezoneManager.to_app_timezone(dt1)
    dt2_normalized = TimezoneManager.to_app_timezone(dt2)
    
    return dt1_normalized - dt2_normalized

def safe_days_between(dt1: datetime, dt2: datetime) -> int:
    """
    Safely calculate days between two datetime objects
    
    Args:
        dt1: First datetime (more recent)
        dt2: Second datetime (earlier)
        
    Returns:
        int: Number of days between the datetimes
    """
    diff = safe_datetime_subtract(dt1, dt2)
    return diff.days

def safe_years_between(dt1: datetime, dt2: datetime) -> float:
    """
    Safely calculate years between two datetime objects
    
    Args:
        dt1: First datetime (more recent)
        dt2: Second datetime (earlier)
        
    Returns:
        float: Number of years between the datetimes
    """
    days = safe_days_between(dt1, dt2)
    return max(0, days / 365.25)

def normalize_datetime(dt: Union[datetime, date]) -> datetime:
    """
    Normalize any datetime or date to a timezone-aware datetime
    
    Args:
        dt: datetime or date object
        
    Returns:
        datetime: Timezone-aware datetime in app timezone
    """
    if isinstance(dt, date) and not isinstance(dt, datetime):
        # Convert date to datetime at start of day
        dt = datetime.combine(dt, datetime.min.time())
    
    return TimezoneManager.to_app_timezone(dt)

def safe_total_seconds_between(dt1: datetime, dt2: datetime) -> float:
    """
    Safely calculate total seconds between two datetime objects
    
    Args:
        dt1: First datetime
        dt2: Second datetime
        
    Returns:
        float: Total seconds between the datetimes
    """
    diff = safe_datetime_subtract(dt1, dt2)
    return diff.total_seconds()