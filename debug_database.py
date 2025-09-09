#!/usr/bin/env python3
"""
Deep Database Analysis Tool
Direct database investigation to find NAV update issues
"""

import streamlit as st
import os
from sqlalchemy import create_engine, text
from datetime import datetime

def deep_database_analysis():
    """Perform deep analysis of database state"""
    
    st.title("🔍 Deep Database Analysis")
    
    try:
        # Get database connection
        db_url = st.secrets.get("database_url") or os.getenv("DATABASE_URL")
        if not db_url:
            st.error("No database URL found")
            return
        
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        
        engine = create_engine(db_url, pool_pre_ping=True)
        
        st.success("✅ Connected to database")
        
        with engine.connect() as conn:
            # 1. Check all transactions
            st.subheader("📊 All Transactions Analysis")
            
            result = conn.execute(text("""
                SELECT id, investor_id, date, type, amount, nav, units_change, 
                       EXTRACT(EPOCH FROM date) as epoch_time
                FROM transactions 
                ORDER BY date DESC, id DESC 
                LIMIT 20
            """))
            
            rows = result.fetchall()
            
            if rows:
                import pandas as pd
                df = pd.DataFrame(rows, columns=['ID', 'Investor_ID', 'Date', 'Type', 'Amount', 'NAV', 'Units_Change', 'Epoch_Time'])
                st.dataframe(df)
                
                # Show NAV transactions specifically
                st.subheader("🎯 NAV Update Transactions Only")
                nav_result = conn.execute(text("""
                    SELECT id, date, nav, 
                           EXTRACT(EPOCH FROM date) as epoch_time,
                           NOW() as current_time
                    FROM transactions 
                    WHERE type = 'NAV Update'
                    ORDER BY date DESC, id DESC
                    LIMIT 10
                """))
                
                nav_rows = nav_result.fetchall()
                if nav_rows:
                    nav_df = pd.DataFrame(nav_rows, columns=['ID', 'Date', 'NAV', 'Epoch_Time', 'Current_Time'])
                    st.dataframe(nav_df)
                    
                    # Check for the specific NAV values we're looking for
                    target_navs = [3858151478, 3859151478, 3856151478]
                    st.subheader("🔍 Target NAV Values Check")
                    
                    for target_nav in target_navs:
                        check_result = conn.execute(text("""
                            SELECT COUNT(*) as count, MAX(id) as max_id, MAX(date) as latest_date
                            FROM transactions 
                            WHERE nav = :target_nav
                        """), {"target_nav": target_nav})
                        
                        count_row = check_result.fetchone()
                        if count_row and count_row[0] > 0:
                            st.info(f"NAV {target_nav:,}: Found {count_row[0]} transactions, Latest ID: {count_row[1]}, Date: {count_row[2]}")
                        else:
                            st.warning(f"NAV {target_nav:,}: Not found in database")
                
                # 2. Check database constraints and indexes
                st.subheader("🏗️ Database Structure Analysis")
                
                # Check for indexes on transactions table
                index_result = conn.execute(text("""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = 'transactions'
                """))
                
                index_rows = index_result.fetchall()
                if index_rows:
                    st.write("**Indexes on transactions table:**")
                    for row in index_rows:
                        st.code(f"{row[0]}: {row[1]}")
                
                # Check for triggers
                trigger_result = conn.execute(text("""
                    SELECT trigger_name, event_manipulation, action_statement
                    FROM information_schema.triggers 
                    WHERE event_object_table = 'transactions'
                """))
                
                trigger_rows = trigger_result.fetchall()
                if trigger_rows:
                    st.write("**Triggers on transactions table:**")
                    for row in trigger_rows:
                        st.code(f"{row[0]} ({row[1]}): {row[2]}")
                else:
                    st.info("No triggers found on transactions table")
                
                # 3. Test direct insert
                st.subheader("🧪 Test Direct Database Insert")
                
                if st.button("🔬 Test Direct NAV Insert"):
                    test_nav = 9999999999  # Unique test value
                    test_id = 99999
                    
                    try:
                        # Insert test transaction
                        conn.execute(text("""
                            INSERT INTO transactions (id, investor_id, date, type, amount, nav, units_change)
                            VALUES (:id, 0, NOW(), 'NAV Update', 0, :nav, 0)
                        """), {"id": test_id, "nav": test_nav})
                        
                        conn.commit()
                        st.success(f"✅ Test insert successful: NAV {test_nav}")
                        
                        # Immediately read it back
                        read_result = conn.execute(text("""
                            SELECT id, nav FROM transactions WHERE id = :id
                        """), {"id": test_id})
                        
                        read_row = read_result.fetchone()
                        if read_row:
                            st.info(f"✅ Read back: ID {read_row[0]}, NAV {read_row[1]}")
                            if read_row[1] == test_nav:
                                st.success("✅ Values match perfectly")
                            else:
                                st.error(f"❌ Value mismatch! Expected {test_nav}, got {read_row[1]}")
                        else:
                            st.error("❌ Could not read back test transaction")
                        
                        # Clean up test data
                        conn.execute(text("DELETE FROM transactions WHERE id = :id"), {"id": test_id})
                        conn.commit()
                        st.info("🧹 Test data cleaned up")
                        
                    except Exception as e:
                        st.error(f"❌ Test insert failed: {str(e)}")
            
            else:
                st.warning("No transactions found in database")
    
    except Exception as e:
        st.error(f"Database analysis failed: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    deep_database_analysis()