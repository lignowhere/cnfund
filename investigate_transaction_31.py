#!/usr/bin/env python3
"""
Investigate Transaction ID:31
Who created this transaction that's overriding our NAV updates?
"""

import os
import streamlit as st
from sqlalchemy import create_engine, text

def investigate_transaction_31():
    """Investigate the mysterious transaction ID:31"""
    
    try:
        # Get database connection
        db_url = st.secrets.get("database_url") or os.getenv("DATABASE_URL")
        if not db_url:
            print("❌ No database URL found")
            return
        
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        
        engine = create_engine(db_url, pool_pre_ping=True)
        
        print("🔍 INVESTIGATING TRANSACTION ID:31")
        print("=" * 50)
        
        with engine.connect() as conn:
            # Get full details of transaction 31
            result = conn.execute(text("""
                SELECT id, investor_id, date, type, amount, nav, units_change,
                       EXTRACT(EPOCH FROM date) as epoch_time,
                       date AT TIME ZONE 'UTC' as utc_date,
                       date AT TIME ZONE 'Asia/Ho_Chi_Minh' as local_date
                FROM transactions 
                WHERE id = 31
            """))
            
            row = result.fetchone()
            if row:
                print(f"Transaction ID: {row[0]}")
                print(f"Investor ID: {row[1]}")
                print(f"Date: {row[2]}")
                print(f"UTC Date: {row[8]}")
                print(f"Local Date: {row[9]}")
                print(f"Type: {row[3]}")
                print(f"Amount: {row[4]}")
                print(f"NAV: {row[5]:,.0f}")
                print(f"Units Change: {row[6]}")
                print(f"Epoch Time: {row[7]}")
            else:
                print("❌ Transaction ID:31 not found!")
                return
            
            print("\n" + "=" * 50)
            
            # Check surrounding transactions
            print("\n🔍 TRANSACTIONS AROUND ID:31 (by ID order):")
            surrounding = conn.execute(text("""
                SELECT id, date, type, nav, investor_id
                FROM transactions 
                WHERE id BETWEEN 28 AND 34
                ORDER BY id
            """))
            
            for row in surrounding.fetchall():
                marker = " <<<< TARGET" if row[0] == 31 else ""
                print(f"ID:{row[0]:2d} | Date:{row[1]} | Type:{row[2]:12s} | NAV:{row[3] or 0:>15,.0f} | Investor:{row[4]}{marker}")
            
            print("\n🔍 TRANSACTIONS AROUND TIME 17:58:20 (by time order):")
            time_surrounding = conn.execute(text("""
                SELECT id, date, type, nav, investor_id
                FROM transactions 
                WHERE date BETWEEN '2025-09-09 17:55:00' AND '2025-09-09 18:05:00'
                ORDER BY date, id
            """))
            
            time_rows = time_surrounding.fetchall()
            if time_rows:
                for row in time_rows:
                    marker = " <<<< TARGET" if row[0] == 31 else ""
                    print(f"ID:{row[0]:2d} | Date:{row[1]} | Type:{row[2]:12s} | NAV:{row[3] or 0:>15,.0f} | Investor:{row[4]}{marker}")
            else:
                print("No transactions found in that time window")
            
            # Check if there are any patterns
            print(f"\n🔍 CHECKING PATTERNS:")
            
            # Check if transaction 31 was created by some automated process
            nav_3856 = conn.execute(text("""
                SELECT id, date, type, investor_id
                FROM transactions 
                WHERE nav = 3856151478
                ORDER BY date DESC
            """))
            
            nav_3856_rows = nav_3856.fetchall()
            print(f"\nTransactions with NAV 3,856,151,478:")
            for row in nav_3856_rows:
                print(f"  ID:{row[0]}, Date:{row[1]}, Type:{row[2]}, Investor:{row[3]}")
            
            # Check the maximum ID to see if there are newer transactions
            max_id = conn.execute(text("SELECT MAX(id) FROM transactions")).fetchone()[0]
            print(f"\n📊 Maximum transaction ID in database: {max_id}")
            
            if max_id > 44:
                print(f"⚠️  There are {max_id - 44} transactions newer than our target transaction (ID:44)")
                
                # Show all transactions after ID:44
                newer_txs = conn.execute(text("""
                    SELECT id, date, type, nav, investor_id
                    FROM transactions 
                    WHERE id > 44
                    ORDER BY id
                """))
                
                print(f"\nTransactions created after ID:44:")
                for row in newer_txs.fetchall():
                    print(f"  ID:{row[0]:2d} | Date:{row[1]} | Type:{row[2]:12s} | NAV:{row[3] or 0:>15,.0f} | Investor:{row[4]}")
    
    except Exception as e:
        print(f"❌ Investigation failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_transaction_31()