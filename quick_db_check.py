#!/usr/bin/env python3
"""
Quick Database Check for NAV Issue
"""

import os
import streamlit as st
from sqlalchemy import create_engine, text

def quick_nav_check():
    """Quick check for NAV transactions"""
    
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
            # Check all NAV transactions in detail
            result = conn.execute(text("""
                SELECT id, date, nav, type, investor_id, amount, units_change,
                       EXTRACT(EPOCH FROM date) as epoch_time
                FROM transactions 
                WHERE nav IS NOT NULL AND nav > 0
                ORDER BY date DESC, id DESC 
                LIMIT 10
            """))
            
            rows = result.fetchall()
            
            print(f"\n🔍 Found {len(rows)} NAV transactions:")
            print("=" * 80)
            
            for i, row in enumerate(rows):
                print(f"{i+1:2d}. ID:{row[0]:3d} | Date:{row[1]} | NAV:{row[2]:>15,.0f} | Type:{row[3]:12s} | Investor:{row[4]:2d}")
            
            print("=" * 80)
            
            # Check for our specific target values
            target_navs = [3857151478, 3856151478, 3858151478, 3859151478]
            
            print(f"\n🎯 Checking for target NAV values:")
            
            for nav in target_navs:
                count_result = conn.execute(text("""
                    SELECT COUNT(*) as count, MAX(id) as max_id, MAX(date) as latest_date
                    FROM transactions 
                    WHERE nav = :nav
                """), {"nav": nav})
                
                count_row = count_result.fetchone()
                if count_row and count_row[0] > 0:
                    print(f"  NAV {nav:>12,}: {count_row[0]} transactions, Latest ID:{count_row[1]}, Date:{count_row[2]}")
                else:
                    print(f"  NAV {nav:>12,}: NOT FOUND")
            
            # Check the very latest transaction
            latest_result = conn.execute(text("""
                SELECT id, date, nav, type
                FROM transactions 
                ORDER BY date DESC, id DESC 
                LIMIT 1
            """))
            
            latest_row = latest_result.fetchone()
            if latest_row:
                print(f"\n🔥 LATEST TRANSACTION:")
                print(f"    ID:{latest_row[0]}, Date:{latest_row[1]}, NAV:{latest_row[2]:,}, Type:{latest_row[3]}")
            
            # Check for NAV Update transactions specifically
            nav_update_result = conn.execute(text("""
                SELECT id, date, nav
                FROM transactions 
                WHERE type = 'NAV Update'
                ORDER BY date DESC, id DESC 
                LIMIT 5
            """))
            
            nav_update_rows = nav_update_result.fetchall()
            if nav_update_rows:
                print(f"\n📈 Latest NAV Update transactions:")
                for row in nav_update_rows:
                    print(f"    ID:{row[0]}, Date:{row[1]}, NAV:{row[2]:,}")
            else:
                print(f"\n⚠️  NO NAV Update transactions found!")
    
    except Exception as e:
        print(f"❌ Database check failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_nav_check()