# realtime_sync_minimal.py - Real-time sync tối ưu, không hiện controls

import streamlit as st
import time
from datetime import datetime

class RealTimeDataSync:
    """Real-time data sync - chỉ hoạt động thầm lặng"""
    
    @staticmethod
    def force_data_refresh():
        """Force refresh - không hiện thông báo"""
        cache_keys_to_clear = [
            key for key in st.session_state.keys() 
            if any(word in key.lower() for word in ['cache', 'nav', 'balance', 'investor', 'tranche'])
        ]
        
        for key in cache_keys_to_clear:
            del st.session_state[key]
        
        st.cache_data.clear()
        st.session_state.force_refresh = True
        st.session_state.last_transaction_time = time.time()
    
    @staticmethod
    def reload_fund_manager_data(fund_manager):
        """Reload data - chỉ log lỗi nếu có"""
        try:
            fund_manager.load_data()
            return True
        except Exception as e:
            st.sidebar.error(f"❌ Reload failed: {str(e)}")
            return False
    
    @staticmethod
    def smart_cache_invalidation():
        """Smart cache invalidation - thầm lặng"""
        nav_keys = [key for key in st.session_state.keys() if 'nav' in key.lower()]
        for key in nav_keys:
            del st.session_state[key]
        
        balance_keys = [key for key in st.session_state.keys() if 'balance' in key.lower()]
        for key in balance_keys:
            del st.session_state[key]
        
        investor_keys = [key for key in st.session_state.keys() if 'investor' in key.lower()]
        for key in investor_keys:
            del st.session_state[key]

class TransactionHandler:
    """Transaction handler tối ưu"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
        self.sync_manager = RealTimeDataSync()
    
    def process_transaction_with_sync(self, transaction_func, *args, **kwargs):
        """Process transaction với auto-sync thầm lặng"""
        try:
            success, message = transaction_func(*args, **kwargs)
            
            if success:
                st.success(f"✅ {message}")
                st.session_state.data_changed = True
                
                # Auto-sync thầm lặng
                self._silent_auto_sync()
                return True, message
            else:
                st.error(f"❌ {message}")
                return False, message
                
        except Exception as e:
            st.error(f"❌ Transaction failed: {str(e)}")
            return False, str(e)
    
    def _silent_auto_sync(self):
        """Auto-sync thầm lặng"""
        try:
            # Save data
            save_success = self._save_with_minimal_feedback()
            
            if save_success:
                # Clear caches
                self.sync_manager.smart_cache_invalidation()
                
                # Reload data
                self.sync_manager.reload_fund_manager_data(self.fund_manager)
                
                # Force UI refresh
                self.sync_manager.force_data_refresh()
                time.sleep(0.5)
                st.rerun()
        except Exception as e:
            st.error(f"❌ Auto-sync failed: {str(e)}")
    
    def _save_with_minimal_feedback(self):
        """Save với feedback tối thiểu"""
        try:
            if hasattr(self.fund_manager, 'ultra_fast_save_data'):
                success = self.fund_manager.ultra_fast_save_data()
            elif hasattr(self.fund_manager, 'optimized_save_data'):
                success = self.fund_manager.optimized_save_data()
            else:
                success = self.fund_manager.save_data()
            
            if success:
                st.session_state.data_changed = False
                return True
            else:
                st.sidebar.error("❌ Save failed")
                return False
                
        except Exception as e:
            st.sidebar.error(f"❌ Save error: {str(e)}")
            return False

class UIRefreshManager:
    """UI refresh manager tối ưu"""
    
    @staticmethod
    def auto_refresh_check():
        """Auto-refresh check - thầm lặng"""
        if st.session_state.get('force_refresh', False):
            st.session_state.force_refresh = False
            time.sleep(0.5)
            st.rerun()
    
    @staticmethod
    def manual_refresh_button():
        """Manual refresh - chỉ khi cần thiết"""
        if st.session_state.get('data_changed', False):
            if st.sidebar.button("🔄 Refresh Data", width="stretch"):
                RealTimeDataSync.force_data_refresh()
                st.rerun()

# === INTEGRATION FUNCTIONS (MINIMAL) ===

def apply_realtime_sync(app_instance):
    """Apply real-time sync - thầm lặng"""
    UIRefreshManager.auto_refresh_check()
    
    # Chỉ hiện nút refresh khi cần
    UIRefreshManager.manual_refresh_button()
    
    if hasattr(app_instance, 'fund_manager'):
        transaction_handler = TransactionHandler(app_instance.fund_manager)
        app_instance.transaction_handler = transaction_handler

# BỎ CÁC FUNCTION KHÔNG CẦN THIẾT:
# - render_sync_controls() 
# - emergency_data_refresh()
# - enhance_transaction_pages()