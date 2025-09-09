#!/usr/bin/env python3
"""
Cloud Debug Utilities for Streamlit Cloud Environment
Helps debug database sync and caching issues
"""

import streamlit as st
from datetime import datetime
import json

class CloudDebugger:
    """Debug utility for cloud environment issues"""
    
    @staticmethod
    def log_nav_operation(operation_type: str, nav_value: float, details: dict = None):
        """Log NAV operations for debugging"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'operation': operation_type,
            'nav_value': nav_value,
            'details': details or {}
        }
        
        # Store in session state for debugging
        if 'nav_debug_log' not in st.session_state:
            st.session_state.nav_debug_log = []
        
        st.session_state.nav_debug_log.append(log_entry)
        
        # Keep only last 50 entries
        if len(st.session_state.nav_debug_log) > 50:
            st.session_state.nav_debug_log = st.session_state.nav_debug_log[-50:]
        
        print(f"🔍 NAV Debug Log: {json.dumps(log_entry, indent=2, default=str)}")
    
    @staticmethod
    def show_debug_panel():
        """Show debug information panel"""
        with st.expander("🔍 Cloud Debug Panel", expanded=False):
            fund_manager = st.session_state.get('fund_manager')
            
            if not fund_manager:
                st.error("No fund manager available")
                return
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Force DB Reload"):
                    fund_manager.load_data()
                    st.success("Data reloaded from database")
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Clear All Caches"):
                    st.cache_data.clear()
                    try:
                        from app import clear_app_cache
                        clear_app_cache()
                    except:
                        pass
                    st.success("All caches cleared")
            
            with col3:
                if st.button("📊 Check DB Status"):
                    data_handler = st.session_state.get('data_handler')
                    if data_handler:
                        connected = getattr(data_handler, 'connected', False)
                        st.info(f"DB Connected: {connected}")
                        
                        # Try to query database directly
                        try:
                            from sqlalchemy import text
                            with data_handler.engine.connect() as conn:
                                result = conn.execute(text("SELECT COUNT(*) FROM transactions"))
                                count = result.fetchone()[0]
                                st.info(f"Transactions in DB: {count}")
                        except Exception as e:
                            st.error(f"DB Query failed: {str(e)}")
            
            # Show NAV debug log
            nav_log = st.session_state.get('nav_debug_log', [])
            if nav_log:
                st.subheader("NAV Operation Log")
                for entry in nav_log[-10:]:  # Show last 10
                    st.json(entry)
    
    @staticmethod
    def verify_nav_sync(expected_nav: float, operation: str):
        """Verify NAV is properly synced between memory and database"""
        fund_manager = st.session_state.get('fund_manager')
        if not fund_manager:
            return False
        
        try:
            # Check memory NAV
            memory_nav = fund_manager.get_latest_total_nav()
            CloudDebugger.log_nav_operation(f"{operation}_MEMORY_CHECK", memory_nav)
            
            # Force reload from DB
            fund_manager.load_data()
            db_nav = fund_manager.get_latest_total_nav()
            CloudDebugger.log_nav_operation(f"{operation}_DB_CHECK", db_nav)
            
            # Compare values
            if memory_nav and db_nav and abs(memory_nav - db_nav) < 0.01:
                CloudDebugger.log_nav_operation(f"{operation}_SYNC_SUCCESS", db_nav, {
                    'memory_nav': memory_nav,
                    'db_nav': db_nav,
                    'expected': expected_nav
                })
                return True
            else:
                CloudDebugger.log_nav_operation(f"{operation}_SYNC_FAILED", db_nav or 0, {
                    'memory_nav': memory_nav,
                    'db_nav': db_nav,
                    'expected': expected_nav
                })
                return False
                
        except Exception as e:
            CloudDebugger.log_nav_operation(f"{operation}_ERROR", 0, {'error': str(e)})
            return False