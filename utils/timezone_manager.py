#!/usr/bin/env python3
"""
Timezone Management System
Ensures consistent timezone handling across local and cloud environments
"""

import os
import pytz
from datetime import datetime, timezone
from typing import Optional

class TimezoneManager:
    """Centralized timezone management for the application"""
    
    # Default timezone for Vietnam
    DEFAULT_TIMEZONE = 'Asia/Ho_Chi_Minh'
    
    @classmethod
    def get_app_timezone(cls) -> pytz.BaseTzInfo:
        """Get the application timezone (Vietnam timezone)"""
        try:
            tz_name = os.getenv('APP_TIMEZONE', cls.DEFAULT_TIMEZONE)
            return pytz.timezone(tz_name)
        except Exception:
            return pytz.timezone(cls.DEFAULT_TIMEZONE)
    
    @classmethod
    def now(cls) -> datetime:
        """Get current time in application timezone"""
        app_tz = cls.get_app_timezone()
        return datetime.now(app_tz)
    
    @classmethod
    def to_app_timezone(cls, dt: datetime) -> datetime:
        """Convert any datetime to application timezone"""
        app_tz = cls.get_app_timezone()
        
        if dt.tzinfo is None:
            # Naive datetime - assume it's in app timezone
            return app_tz.localize(dt)
        else:
            # Timezone-aware datetime - convert to app timezone
            return dt.astimezone(app_tz)
    
    @classmethod
    def to_utc(cls, dt: datetime) -> datetime:
        """Convert datetime to UTC"""
        if dt.tzinfo is None:
            # Naive datetime - assume it's in app timezone
            app_tz = cls.get_app_timezone()
            dt = app_tz.localize(dt)
        
        return dt.astimezone(timezone.utc)
    
    @classmethod
    def normalize_for_storage(cls, dt: datetime) -> datetime:
        """Normalize datetime for database storage (always store as UTC)"""
        return cls.to_utc(dt)
    
    @classmethod
    def normalize_for_display(cls, dt: datetime) -> datetime:
        """Normalize datetime for display (always show in app timezone)"""
        return cls.to_app_timezone(dt)
    
    @classmethod
    def create_transaction_timestamp(cls) -> datetime:
        """Create a proper timestamp for transactions"""
        # Always create timezone-aware datetime in app timezone
        app_tz = cls.get_app_timezone()
        return datetime.now(app_tz)
    
    @classmethod
    def is_cloud_environment(cls) -> bool:
        """Detect if running in cloud environment"""
        return (
            os.getenv('RAILWAY_ENVIRONMENT') is not None or
            os.getenv('VERCEL') is not None or
            '/mount/src' in os.getcwd()
        )
    
    @classmethod
    def setup_environment_timezone(cls):
        """Setup timezone for the current environment"""
        app_tz_name = cls.DEFAULT_TIMEZONE
        
        # Set TZ environment variable for consistent behavior
        os.environ['TZ'] = app_tz_name
        
        # For cloud environments, we might need additional setup
        if cls.is_cloud_environment():
            print(f"🌐 Cloud environment detected - setting timezone to {app_tz_name}")
        else:
            print(f"💻 Local environment - setting timezone to {app_tz_name}")
        
        # Import time after setting TZ to apply changes
        import time
        if hasattr(time, 'tzset'):
            time.tzset()
        
        return app_tz_name
    
    @classmethod
    def debug_timezone_info(cls):
        """Debug timezone information"""
        app_tz = cls.get_app_timezone()
        now_app = cls.now()
        now_utc = cls.to_utc(now_app)
        
        print("🕐 TIMEZONE DEBUG INFO")
        print("=" * 40)
        print(f"App Timezone: {app_tz}")
        print(f"Current App Time: {now_app}")
        print(f"Current UTC Time: {now_utc}")
        print(f"TZ Environment: {os.getenv('TZ', 'Not set')}")
        print(f"Is Cloud: {cls.is_cloud_environment()}")
        
        # Test timezone conversion
        test_naive = datetime(2025, 9, 9, 12, 0, 0)
        test_app = cls.to_app_timezone(test_naive)
        test_utc = cls.to_utc(test_naive)
        
        print(f"\nTest conversions (12:00 noon):")
        print(f"Naive: {test_naive}")
        print(f"App TZ: {test_app}")
        print(f"UTC: {test_utc}")

# Initialize timezone on import
TimezoneManager.setup_environment_timezone()
