#!/usr/bin/env python3
"""
Debug timezone and timestamp issues
"""

from datetime import datetime, timezone
import pytz
import os

def debug_timezone():
    """Debug timezone settings"""
    
    print("🕐 TIMEZONE DEBUG")
    print("=" * 40)
    
    # Current times in different formats
    now_utc = datetime.now(timezone.utc)
    now_local = datetime.now()
    
    print(f"UTC Time: {now_utc}")
    print(f"Local Time: {now_local}")
    print(f"System Timezone: {now_local.astimezone().tzinfo}")
    
    # Vietnam timezone
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now_vn = datetime.now(vn_tz)
    print(f"Vietnam Time: {now_vn}")
    
    # Check environment variables
    print(f"\nTZ Environment: {os.getenv('TZ', 'Not set')}")
    
    # Check if we're in cloud environment
    cloud_indicators = [
        ('STREAMLIT_CLOUD', os.getenv('STREAMLIT_CLOUD')),
        ('HOSTNAME', os.getenv('HOSTNAME', '')),
        ('PWD', os.getcwd())
    ]
    
    print(f"\nCloud Environment Check:")
    for name, value in cloud_indicators:
        print(f"  {name}: {value}")
        
    # Time difference calculations
    utc_offset = now_local.astimezone().utcoffset().total_seconds() / 3600
    print(f"\nUTC Offset: {utc_offset} hours")
    
    # The suspicious timestamp from database
    suspicious_timestamp = datetime(2025, 9, 9, 17, 58, 20, 785794)
    print(f"\nSuspicious DB timestamp: {suspicious_timestamp}")
    print(f"Difference from now (local): {suspicious_timestamp - now_local}")
    print(f"Difference from now (UTC): {suspicious_timestamp - now_utc.replace(tzinfo=None)}")

if __name__ == "__main__":
    debug_timezone()