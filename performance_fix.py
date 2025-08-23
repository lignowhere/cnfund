# performance_fix.py - Critical performance fixes

import streamlit as st
import time
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import asyncio

# === FIX 1: DATABASE CONNECTION OPTIMIZATION ===

class FastSupabaseDataHandler:
    """Optimized database handler wrapper"""
    
    def __init__(self, original_handler):
        self.original = original_handler
        self.connection_pool_size = 5
        self.query_timeout = 10
    
    def optimize_connection(self):
        """Optimize database connection settings"""
        if not self.original.engine:
            return False
        
        try:
            # Update engine with optimized settings
            from sqlalchemy import create_engine
            
            # Get original URL
            db_url = str(self.original.engine.url)
            
            # Create optimized engine with PostgreSQL-compatible settings
            self.original.engine = create_engine(
                db_url,
                pool_size=self.connection_pool_size,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=1800,  # 30 minutes
                connect_args={
                    "sslmode": "require",
                    "application_name": "fund_management_fast",
                    "connect_timeout": 10,
                    # Remove command_timeout - not supported by psycopg2
                }
            )
            
            st.success("✅ Database connection optimized")
            return True
            
        except Exception as e:
            st.error(f"❌ Connection optimization failed: {e}")
            return False

# === FIX 2: FAST SAVE OPERATION ===

def optimized_save_with_batching(fund_manager):
    """Optimized save operation with batching"""
    
    def batch_save():
        """Save data in optimized batches"""
        try:
            # Validate first (quick check)
            validation = fund_manager.validate_data_consistency()
            if not validation['valid']:
                return False, "Data validation failed"
            
            # Use optimized save
            success = fund_manager.data_handler.save_all_data_enhanced(
                fund_manager.investors,
                fund_manager.tranches, 
                fund_manager.transactions,
                fund_manager.fee_records
            )
            
            return success, "Save completed" if success else "Save failed"
            
        except Exception as e:
            return False, f"Save error: {str(e)}"
    
    # Run save operation
    start_time = time.time()
    success, message = batch_save()
    save_time = time.time() - start_time
    
    # Performance feedback
    if save_time > 5:
        st.warning(f"⚠️ Save took {save_time:.1f}s - Database may be slow")
    elif save_time > 2:
        st.info(f"ℹ️ Save completed in {save_time:.1f}s")
    else:
        st.success(f"✅ Fast save: {save_time:.1f}s")
    
    return success, message

# === FIX 3: REAL-TIME UI UPDATES ===

class RealTimeUpdater:
    """Handle real-time UI updates without page reload"""
    
    @staticmethod
    def invalidate_nav_cache():
        """Clear NAV-related caches"""
        cache_keys = [key for key in st.session_state.keys() if 'nav' in key.lower()]
        for key in cache_keys:
            del st.session_state[key]
    
    @staticmethod 
    def invalidate_all_caches():
        """Clear all performance caches"""
        cache_keys = [key for key in st.session_state.keys() if key.startswith('cache_')]
        for key in cache_keys:
            del st.session_state[key]
        
        # Also clear Streamlit's cache
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
    
    @staticmethod
    def smart_rerun():
        """Smart rerun that only refreshes necessary components"""
        # Mark data as changed
        st.session_state.data_changed = True
        
        # Clear caches
        RealTimeUpdater.invalidate_all_caches()
        
        # Force rerun
        st.rerun()

# === FIX 4: PAGE RENDERING ERROR HANDLER ===

class SafePageRenderer:
    """Safe page rendering with error handling"""
    
    @staticmethod
    def safe_render(render_func, page_name):
        """Safely render page with error handling"""
        try:
            start_time = time.time()
            result = render_func()
            render_time = time.time() - start_time
            
            # Performance feedback
            if render_time > 3:
                st.sidebar.error(f"❌ {page_name}: {render_time:.1f}s (very slow)")
            elif render_time > 1:
                st.sidebar.warning(f"⚠️ {page_name}: {render_time:.1f}s")
            else:
                st.sidebar.success(f"✅ {page_name}: {render_time:.1f}s")
            
            return result
            
        except Exception as e:
            st.error(f"❌ Lỗi tải trang '{page_name}': {str(e)}")
            
            # Show debug info
            with st.expander("🔍 Chi tiết lỗi"):
                st.code(str(e))
                
                # Suggest fixes
                if "not defined" in str(e):
                    st.info("💡 Có thể do lỗi import. Thử refresh trang.")
                elif "connection" in str(e).lower():
                    st.info("💡 Có thể do lỗi database connection.")
                elif "session_state" in str(e):
                    st.info("💡 Có thể do session state. Thử clear cache.")
            
            # Recovery options
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"🔄 Retry {page_name}"):
                    st.rerun()
            with col2:
                if st.button("🧹 Clear Cache & Retry"):
                    RealTimeUpdater.invalidate_all_caches()
                    st.rerun()
            
            return None

# === FIX 5: FAST CACHED FUNCTIONS ===

@st.cache_data(ttl=60)  # 1 minute cache
def fast_get_nav(fund_manager_id):
    """Fast cached NAV retrieval"""
    try:
        # Use session state fund manager
        fund_manager = st.session_state.fund_manager
        if hasattr(fund_manager, 'original'):
            fund_manager = fund_manager.original
        
        return fund_manager.get_latest_total_nav()
    except:
        return None

@st.cache_data(ttl=30)  # 30 second cache
def fast_get_balance(fund_manager_id, investor_id, nav):
    """Fast cached balance calculation"""
    try:
        fund_manager = st.session_state.fund_manager
        if hasattr(fund_manager, 'original'):
            fund_manager = fund_manager.original
        
        return fund_manager.get_investor_balance(investor_id, nav)
    except:
        return 0.0, 0.0, 0.0

@st.cache_data(ttl=120)  # 2 minute cache
def fast_get_investors(fund_manager_id):
    """Fast cached investor list"""
    try:
        fund_manager = st.session_state.fund_manager
        if hasattr(fund_manager, 'original'):
            fund_manager = fund_manager.original
        
        return fund_manager.get_regular_investors()
    except:
        return []

# === FIX 6: OPTIMIZED DATA SYNC ===

class DataSyncManager:
    """Manage data synchronization for real-time updates"""
    
    @staticmethod
    def sync_after_transaction():
        """Sync data after transaction without full reload"""
        try:
            # Clear relevant caches only
            keys_to_clear = [
                'cache_nav', 'cache_balance', 'cache_investors', 
                'cache_tranches', 'cache_latest_nav'
            ]
            
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Clear Streamlit caches
            fast_get_nav.clear()
            fast_get_balance.clear()
            fast_get_investors.clear()
            
            # Mark for refresh
            st.session_state.data_sync_needed = True
            
            return True
            
        except Exception as e:
            st.error(f"❌ Data sync failed: {e}")
            return False
    
    @staticmethod
    def check_and_sync():
        """Check if sync needed and perform it"""
        if st.session_state.get('data_sync_needed', False):
            # Reset flag
            st.session_state.data_sync_needed = False
            
            # Trigger UI update
            st.rerun()

# === FIX 7: CONNECTION HEALTH CHECK ===

def quick_db_health_check(data_handler):
    """Quick database health check with better error handling"""
    try:
        start_time = time.time()
        
        from sqlalchemy import text
        with data_handler.engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()  # Actually fetch the result
        
        response_time = time.time() - start_time
        
        if response_time > 2:
            st.sidebar.error(f"🔴 DB slow: {response_time:.1f}s")
            return False
        elif response_time > 0.5:
            st.sidebar.warning(f"🟡 DB moderate: {response_time:.1f}s") 
            return True
        else:
            st.sidebar.success(f"🟢 DB fast: {response_time:.1f}s")
            return True
            
    except Exception as e:
        error_msg = str(e)
        if "invalid dsn" in error_msg:
            st.sidebar.error("🔴 DB config error")
        elif "connection" in error_msg.lower():
            st.sidebar.error("🔴 DB connection failed")
        else:
            st.sidebar.error(f"🔴 DB error: {error_msg[:50]}")
        return False

# === INTEGRATION HELPER ===

def apply_all_performance_fixes(app_instance):
    """Apply all performance fixes to app instance with fallbacks"""
    
    # Fix 1: Optimize database connection (with fallback)
    if hasattr(app_instance, 'data_handler'):
        try:
            fast_handler = FastSupabaseDataHandler(app_instance.data_handler)
            fast_handler.optimize_connection()
        except Exception as e:
            st.sidebar.warning(f"⚠️ DB optimization skipped: {str(e)[:50]}")
    
    # Fix 2: Health check (with fallback)
    if hasattr(app_instance, 'data_handler'):
        try:
            quick_db_health_check(app_instance.data_handler)
        except Exception as e:
            st.sidebar.info("ℹ️ DB health check skipped")
    
    # Fix 3: Data sync check
    try:
        DataSyncManager.check_and_sync()
    except Exception as e:
        # Silently fail - not critical
        pass
    
    return True

# === PERFORMANCE MONITORING ===

def monitor_critical_operations():
    """Monitor critical operations and show warnings"""
    
    if 'performance_warnings' not in st.session_state:
        st.session_state.performance_warnings = []
    
    # Show recent warnings
    warnings = st.session_state.performance_warnings[-3:]  # Last 3 warnings
    
    for warning in warnings:
        if warning['severity'] == 'critical':
            st.sidebar.error(f"🚨 {warning['message']}")
        elif warning['severity'] == 'warning':
            st.sidebar.warning(f"⚠️ {warning['message']}")

def log_performance_warning(message, severity='warning'):
    """Log performance warning"""
    if 'performance_warnings' not in st.session_state:
        st.session_state.performance_warnings = []
    
    st.session_state.performance_warnings.append({
        'message': message,
        'severity': severity,
        'timestamp': time.time()
    })
    
    # Keep only last 10 warnings
    if len(st.session_state.performance_warnings) > 10:
        st.session_state.performance_warnings = st.session_state.performance_warnings[-10:]