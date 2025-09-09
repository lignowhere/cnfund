#!/usr/bin/env python3
"""
Test Timezone Fix
Verify timezone management works correctly
"""

from datetime import datetime, date
from timezone_manager import TimezoneManager
from models import Transaction

def test_timezone_fix():
    """Test timezone management"""
    
    print("🧪 TESTING TIMEZONE FIX")
    print("=" * 50)
    
    # Debug timezone info
    TimezoneManager.debug_timezone_info()
    
    print("\n🔬 TESTING TRANSACTION CREATION")
    print("-" * 30)
    
    # Test 1: Create transaction with current time
    current_time = TimezoneManager.now()
    print(f"Current app time: {current_time}")
    
    # Test 2: Create transaction like the app does
    user_date = date(2025, 9, 9)  # User selects date
    current_time_only = current_time.time()  # Current time
    trans_datetime = datetime.combine(user_date, current_time_only)
    
    print(f"Combined datetime (naive): {trans_datetime}")
    
    # Normalize to app timezone (like we do in transaction_page.py)
    app_timezone_dt = TimezoneManager.to_app_timezone(trans_datetime)
    print(f"App timezone datetime: {app_timezone_dt}")
    
    # Normalize for storage (like we do in services_enhanced.py)
    storage_dt = TimezoneManager.normalize_for_storage(app_timezone_dt)
    print(f"Storage datetime (UTC): {storage_dt}")
    
    # Simulate loading from database and display
    display_dt = TimezoneManager.normalize_for_display(storage_dt)
    print(f"Display datetime: {display_dt}")
    
    print(f"\n🎯 FINAL VERIFICATION:")
    print(f"Original: {app_timezone_dt}")
    print(f"Round-trip: {display_dt}")
    
    # Check if they're equivalent (should be same moment in time)
    if app_timezone_dt.astimezone() == display_dt.astimezone():
        print("✅ Timezone round-trip successful!")
    else:
        print("❌ Timezone round-trip failed!")
        print(f"Difference: {app_timezone_dt - display_dt}")
    
    print(f"\n🔍 TESTING TRANSACTION SORTING")
    print("-" * 30)
    
    # Create test transactions with different timezones
    test_transactions = []
    
    # Transaction 1: Created with UTC (like old system)
    utc_dt = datetime(2025, 9, 9, 10, 30, 0)  # 10:30 UTC
    utc_dt = utc_dt.replace(tzinfo=TimezoneManager.get_app_timezone().zone == 'UTC' and TimezoneManager.get_app_timezone() or None)
    
    # Transaction 2: Created with app timezone (new system)
    app_dt = TimezoneManager.get_app_timezone().localize(datetime(2025, 9, 9, 17, 30, 0))  # 17:30 Vietnam time
    
    print(f"UTC transaction: {utc_dt}")
    print(f"App TZ transaction: {app_dt}")
    
    # Test smart sorting (date only)
    utc_date = utc_dt.date() if hasattr(utc_dt, 'date') else utc_dt
    app_date = app_dt.date() if hasattr(app_dt, 'date') else app_dt
    
    print(f"UTC date: {utc_date}")
    print(f"App TZ date: {app_date}")
    
    if utc_date == app_date:
        print("✅ Same date - smart sorting will work correctly!")
    else:
        print("❌ Different dates - could cause sorting issues")
    
    print(f"\n🌐 ENVIRONMENT CHECK:")
    print(f"Is cloud: {TimezoneManager.is_cloud_environment()}")
    print(f"App timezone: {TimezoneManager.get_app_timezone()}")

if __name__ == "__main__":
    test_timezone_fix()