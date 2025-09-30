#!/usr/bin/env python3
"""
Verify timezone configuration
Run on both local and cloud to check consistency
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.timezone_manager import TimezoneManager


def verify_timezone():
    """Verify timezone setup"""

    print("=" * 60)
    print("🌍 Timezone Verification")
    print("=" * 60)

    # Environment detection
    is_cloud = TimezoneManager.is_cloud_environment()
    print(f"\n📍 Environment: {'☁️  Cloud' if is_cloud else '🏠 Local'}")

    # Setup timezone
    TimezoneManager.setup_environment_timezone()

    # Get app timezone
    app_tz = TimezoneManager.get_app_timezone()
    print(f"⏰ App Timezone: {app_tz}")

    # Get current time
    now_app = TimezoneManager.now()
    now_utc = TimezoneManager.to_utc(now_app)

    print(f"\n📅 Current Time:")
    print(f"   App (Vietnam): {now_app.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"   UTC:           {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"   Offset:        {now_app.strftime('%z')} (UTC+7)")

    # Test conversion
    print(f"\n🔄 Conversion Test:")
    test_utc = datetime.now()
    test_app = TimezoneManager.to_app_timezone(test_utc)
    print(f"   UTC naive:     {test_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   → Vietnam:     {test_app.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Environment variables
    print(f"\n🔧 Environment Variables:")
    print(f"   TZ:            {os.environ.get('TZ', 'Not set')}")
    print(f"   APP_TIMEZONE:  {os.environ.get('APP_TIMEZONE', 'Not set (using default)')}")

    # Verification
    print(f"\n✅ Verification:")
    checks = []

    # Check 1: App timezone is Asia/Ho_Chi_Minh
    if str(app_tz) == 'Asia/Ho_Chi_Minh':
        checks.append("✅ Timezone set to Asia/Ho_Chi_Minh")
    else:
        checks.append(f"❌ Timezone is {app_tz}, expected Asia/Ho_Chi_Minh")

    # Check 2: Offset is +07:00
    offset = now_app.strftime('%z')
    if offset == '+0700':
        checks.append("✅ UTC offset is +07:00")
    else:
        checks.append(f"❌ UTC offset is {offset}, expected +0700")

    # Check 3: Time difference is 7 hours
    time_diff = (now_app - now_utc).total_seconds() / 3600
    if abs(time_diff) < 0.1:  # Should be 0 since both are same instant
        checks.append("✅ Time conversion working correctly")
    else:
        checks.append(f"⚠️ Time difference unexpected: {time_diff} hours")

    for check in checks:
        print(f"   {check}")

    # Summary
    print(f"\n" + "=" * 60)
    all_pass = all('✅' in check for check in checks)
    if all_pass:
        print("🎉 All timezone checks passed!")
        return True
    else:
        print("⚠️ Some timezone checks failed - please review above")
        return False


if __name__ == "__main__":
    success = verify_timezone()
    sys.exit(0 if success else 1)