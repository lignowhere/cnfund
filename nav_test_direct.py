#!/usr/bin/env python3
"""
Direct NAV Update Test
Test NAV update process step by step without any caching
"""

import streamlit as st
from datetime import datetime
from services_enhanced import EnhancedFundManager
from supabase_data_handler import SupabaseDataHandler
from utils import format_currency

def test_nav_update_direct():
    """Test NAV update process step by step"""
    
    st.title("🧪 Direct NAV Update Test")
    
    try:
        # Create fresh instances - no caching
        data_handler = SupabaseDataHandler()
        if not data_handler.connected:
            st.error("❌ Could not connect to database")
            return
            
        fund_manager = EnhancedFundManager(data_handler)
        
        st.success("✅ Fresh instances created")
        
        # Step 1: Load current data
        st.subheader("Step 1: Load Current Data")
        fund_manager.load_data()
        
        current_nav = fund_manager.get_latest_total_nav()
        current_tx_count = len(fund_manager.transactions)
        
        st.info(f"Current NAV: {format_currency(current_nav) if current_nav else 'None'}")
        st.info(f"Current transaction count: {current_tx_count}")
        
        # Step 2: Manual NAV input
        st.subheader("Step 2: Test NAV Update")
        
        test_nav = st.number_input("Test NAV Value", value=4000000000, step=1000000)
        
        if st.button("🚀 Test NAV Update"):
            st.write("**Testing NAV Update Process:**")
            
            # Show before state
            st.write(f"BEFORE: NAV = {format_currency(current_nav) if current_nav else 'None'}")
            st.write(f"BEFORE: Transactions = {current_tx_count}")
            
            # Perform NAV update
            trans_date = datetime.now()
            success, message = fund_manager.process_nav_update(test_nav, trans_date)
            
            if success:
                st.success(f"✅ NAV Update: {message}")
                
                # Check immediately after update (before any reload)
                immediate_nav = fund_manager.get_latest_total_nav()
                immediate_tx_count = len(fund_manager.transactions)
                
                st.write(f"IMMEDIATE AFTER: NAV = {format_currency(immediate_nav) if immediate_nav else 'None'}")
                st.write(f"IMMEDIATE AFTER: Transactions = {immediate_tx_count}")
                
                # Check if immediate values are correct
                if immediate_nav == test_nav:
                    st.success("✅ Immediate check: NAV matches input")
                else:
                    st.error(f"❌ Immediate check: NAV mismatch! Expected {test_nav}, got {immediate_nav}")
                
                # Force reload from database
                st.write("**Reloading from database...**")
                fund_manager.load_data()
                
                reloaded_nav = fund_manager.get_latest_total_nav()
                reloaded_tx_count = len(fund_manager.transactions)
                
                st.write(f"AFTER RELOAD: NAV = {format_currency(reloaded_nav) if reloaded_nav else 'None'}")
                st.write(f"AFTER RELOAD: Transactions = {reloaded_tx_count}")
                
                # Final verification
                if reloaded_nav == test_nav:
                    st.success("✅ Final check: NAV persisted correctly")
                else:
                    st.error(f"❌ Final check: NAV not persisted! Expected {test_nav}, got {reloaded_nav}")
                
                # Show transaction details
                if reloaded_tx_count > current_tx_count:
                    st.success(f"✅ Transaction count increased by {reloaded_tx_count - current_tx_count}")
                    
                    # Show the newest transaction
                    newest_tx = max(fund_manager.transactions, key=lambda x: x.id)
                    st.write(f"**Newest Transaction:** ID={newest_tx.id}, Type={newest_tx.type}, NAV={newest_tx.nav}")
                else:
                    st.error("❌ No new transactions were created")
                
            else:
                st.error(f"❌ NAV Update failed: {message}")
                
        # Step 3: Direct database query
        st.subheader("Step 3: Direct Database Verification")
        
        if st.button("🔍 Query Database Directly"):
            try:
                from sqlalchemy import text
                
                with data_handler.engine.connect() as conn:
                    # Get latest NAV transactions
                    result = conn.execute(text("""
                        SELECT id, date, nav, type, investor_id
                        FROM transactions 
                        WHERE nav IS NOT NULL AND nav > 0
                        ORDER BY date DESC, id DESC 
                        LIMIT 5
                    """))
                    
                    rows = result.fetchall()
                    
                    if rows:
                        st.write("**Latest NAV transactions from database:**")
                        for i, row in enumerate(rows):
                            st.write(f"{i+1}. ID:{row[0]}, Date:{row[1]}, NAV:{row[2]}, Type:{row[3]}, Investor:{row[4]}")
                    else:
                        st.warning("No NAV transactions found in database")
                        
            except Exception as e:
                st.error(f"Database query failed: {str(e)}")
        
    except Exception as e:
        st.error(f"Test failed: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    test_nav_update_direct()