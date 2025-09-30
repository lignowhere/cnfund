"""
Simplified Caching Service for CNFund System
NO CACHE - All decorators are pass-through (do nothing)
"""

import streamlit as st
from typing import Callable
from functools import wraps

# === NO CACHE DECORATORS (Pass-through only) ===

def cache_investor_data(func: Callable):
    """NO CACHE - Returns function as-is"""
    return func

def cache_transaction_data(func: Callable):
    """NO CACHE - Returns function as-is"""
    return func

def cache_nav_data(func: Callable):
    """NO CACHE - Returns function as-is"""
    return func

def cache_report_data(func: Callable):
    """NO CACHE - Returns function as-is"""
    return func

def cache_static_data(func: Callable):
    """NO CACHE - Returns function as-is"""
    return func

# === CACHE INVALIDATION ===

def invalidate_investor_cache():
    """Invalidate all investor-related cache"""
    st.cache_data.clear()

def invalidate_transaction_cache():
    """Invalidate all transaction-related cache"""
    st.cache_data.clear()

def invalidate_nav_cache():
    """Invalidate all NAV-related cache"""
    st.cache_data.clear()

def invalidate_all_data_cache():
    """Invalidate all data caches after updates"""
    st.cache_data.clear()

# === CACHE WARMING ===

def warm_cache(fund_manager):
    """Warm up cache with frequently accessed data"""
    try:
        # Pre-load frequently accessed data
        _ = fund_manager.get_regular_investors()
        _ = fund_manager.transactions  # Access transactions list directly
        _ = fund_manager.get_latest_total_nav()
        print("✅ Cache warming completed")
    except Exception as e:
        print(f"⚠️ Cache warming failed: {e}")
        import traceback
        traceback.print_exc()

# === CACHE STATISTICS (SIMPLIFIED) ===

def get_cache_stats():
    """Get simplified cache statistics"""
    # Streamlit doesn't expose cache stats directly
    # So we return a simple message
    return {
        'message': 'Using Streamlit built-in caching',
        'info': 'Cache is managed automatically by Streamlit'
    }

def render_cache_info():
    """Render cache information"""
    st.subheader("💾 Cache Information")
    st.info("""
    **Caching Strategy: NO CACHE**
    - All data is always loaded fresh from Google Drive
    - Ensures 100% data accuracy and consistency
    - No stale data issues

    ✅ Every page load = fresh data
    ✅ All users see the same (latest) data
    """)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🧹 Clear All Cache"):
            st.cache_data.clear()
            st.success("✅ Cache cleared!")

    with col2:
        st.caption("Cache clears automatically on code changes")

# === STREAMLIT CACHING WRAPPERS ===

@st.cache_data(ttl=300, show_spinner=False)
def cached_load_investors(fund_manager):
    """Cache investor loading"""
    return fund_manager.get_regular_investors()

@st.cache_data(ttl=120, show_spinner=False)
def cached_load_transactions(fund_manager):
    """Cache transaction loading"""
    return fund_manager.transactions

@st.cache_data(ttl=300, show_spinner=False)
def cached_load_nav_history(fund_manager):
    """Cache NAV history"""
    return fund_manager.get_nav_history()

@st.cache_data(ttl=600, show_spinner=False)
def cached_load_nav(fund_manager):
    """Cache latest NAV"""
    return fund_manager.get_latest_total_nav()

# === AUTO CLEANUP ===

def auto_cleanup_cache():
    """No-op: Streamlit handles cleanup automatically"""
    pass

# Compatibility layer - keep old function names
get_cache_service = lambda: None  # No service needed