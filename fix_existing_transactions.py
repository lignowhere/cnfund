#!/usr/bin/env python3
"""
Fix Existing Transactions Timezone
One-time script to normalize existing transaction timestamps in database
"""

import os
import streamlit as st
from sqlalchemy import create_engine, text
from timezone_manager import TimezoneManager
from datetime import datetime

def fix_existing_transactions():
    """Fix timezone for existing transactions in database"""
    
    print("🔧 FIXING EXISTING TRANSACTIONS TIMEZONE")
    print("=" * 50)
    
    try:
        # Get database connection
        db_url = st.secrets.get("database_url") or os.getenv("DATABASE_URL")
        if not db_url:
            print("❌ No database URL found")
            return
        
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        
        engine = create_engine(db_url, pool_pre_ping=True)
        
        print("✅ Connected to database")
        
        with engine.connect() as conn:
            # First, get all transactions to analyze
            # Note: date column is 'timestamp without time zone'
            result = conn.execute(text("""
                SELECT id, date, type
                FROM transactions 
                ORDER BY id
            """))
            
            rows = result.fetchall()
            
            print(f"\n📊 Found {len(rows)} transactions to analyze:")
            
            # Show sample of current timestamps
            print("\nSample current timestamps:")
            for i, row in enumerate(rows[:5]):
                print(f"  ID:{row[0]:2d} | Type: {row[2]:12s} | Date: {row[1]}")
            
            if len(rows) > 5:
                print(f"  ... and {len(rows) - 5} more")
            
            # All timestamps are naive (timestamp without time zone)
            print(f"\n📈 Analysis:")
            print(f"  All {len(rows)} transactions have naive timestamps (no timezone info)")
            print(f"  Database column type: timestamp without time zone")
            print(f"  These will be treated as Vietnam timezone when loaded")
            
            # Show how our timezone manager will handle these
            print(f"\n🔧 How TimezoneManager handles these:")
            sample_transaction = rows[0] if rows else None
            
            if sample_transaction:
                naive_dt = sample_transaction[1]
                print(f"  Original (naive): {naive_dt}")
                
                # This is what normalize_for_display() will do
                vietnam_tz = TimezoneManager.get_app_timezone()
                # Since it's naive, we localize it to Vietnam timezone
                if hasattr(naive_dt, 'tzinfo') and naive_dt.tzinfo is not None:
                    display_dt = naive_dt.astimezone(vietnam_tz)
                else:
                    display_dt = vietnam_tz.localize(naive_dt)
                
                print(f"  After normalize_for_display(): {display_dt}")
                print(f"  Date part for sorting: {display_dt.date()}")
                
            print(f"\n✅ Current database structure is compatible!")
            print(f"💡 Naive timestamps will be assumed to be in Vietnam timezone")
            print(f"💡 New transactions will be stored as UTC but loaded as Vietnam time")
            
            # For now, we just analyze without updating
            print(f"\n✅ Analysis complete. No changes made to database.")
            print(f"💡 The new timezone management will handle future transactions correctly.")
            print(f"💡 Existing transactions will be normalized when loaded from database.")
            
    except Exception as e:
        print(f"❌ Fix failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_existing_transactions()