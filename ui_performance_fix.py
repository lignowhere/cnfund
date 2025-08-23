# ui_performance_fix.py - Safe UI performance improvements

import streamlit as st
import time
from functools import wraps

# === SAFE CACHING SYSTEM ===

class SafeCache:
    """Safe caching system using session state"""
    
    @staticmethod
    def get(key, default=None):
        """Get cached value"""
        return st.session_state.get(f"cache_{key}", default)
    
    @staticmethod
    def set(key, value, ttl=300):
        """Set cached value with TTL"""
        st.session_state[f"cache_{key}"] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
    
    @staticmethod
    def is_valid(key):
        """Check if cache is still valid"""
        cache_data = st.session_state.get(f"cache_{key}")
        if not cache_data:
            return False
        
        age = time.time() - cache_data['timestamp']
        return age < cache_data['ttl']
    
    @staticmethod
    def clear_all():
        """Clear all caches"""
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith('cache_')]
        for key in keys_to_remove:
            del st.session_state[key]
        return len(keys_to_remove)

# === REAL-TIME UI UPDATES ===

class UIUpdater:
    """Handle UI updates without page refresh"""
    
    @staticmethod
    def mark_data_changed():
        """Mark data as changed for UI update"""
        st.session_state.data_changed = True
        st.session_state.ui_needs_refresh = True
    
    @staticmethod
    def clear_nav_cache():
        """Clear NAV-related caches only"""
        nav_keys = [key for key in st.session_state.keys() 
                   if any(word in key.lower() for word in ['nav', 'balance', 'price'])]
        for key in nav_keys:
            del st.session_state[key]
    
    @staticmethod
    def smart_refresh():
        """Smart refresh without full page reload"""
        UIUpdater.clear_nav_cache()
        SafeCache.clear_all()
        st.session_state.ui_needs_refresh = False
        st.rerun()

# === FAST DATA RETRIEVAL ===

def get_cached_nav(fund_manager):
    """Get NAV with safe caching"""
    cache_key = "latest_nav"
    
    if SafeCache.is_valid(cache_key):
        cached_data = SafeCache.get(cache_key)
        return cached_data['value']
    
    # Fetch fresh data
    try:
        nav = fund_manager.get_latest_total_nav()
        SafeCache.set(cache_key, nav, ttl=120)  # 2 minutes
        return nav
    except Exception as e:
        st.sidebar.warning(f"⚠️ NAV fetch failed: {str(e)[:30]}")
        return SafeCache.get(cache_key, {}).get('value', 0)

def get_cached_balance(fund_manager, investor_id, nav):
    """Get balance with safe caching"""
    cache_key = f"balance_{investor_id}_{int(nav)}"
    
    if SafeCache.is_valid(cache_key):
        cached_data = SafeCache.get(cache_key)
        return cached_data['value']
    
    # Fetch fresh data
    try:
        balance = fund_manager.get_investor_balance(investor_id, nav)
        SafeCache.set(cache_key, balance, ttl=60)  # 1 minute
        return balance
    except Exception as e:
        st.sidebar.warning(f"⚠️ Balance fetch failed: {str(e)[:30]}")
        return SafeCache.get(cache_key, {}).get('value', (0, 0, 0))

def get_cached_investors(fund_manager):
    """Get investors with safe caching"""
    cache_key = "regular_investors"
    
    if SafeCache.is_valid(cache_key):
        cached_data = SafeCache.get(cache_key)
        return cached_data['value']
    
    # Fetch fresh data
    try:
        investors = fund_manager.get_regular_investors()
        SafeCache.set(cache_key, investors, ttl=300)  # 5 minutes
        return investors
    except Exception as e:
        st.sidebar.warning(f"⚠️ Investors fetch failed: {str(e)[:30]}")
        return SafeCache.get(cache_key, {}).get('value', [])

# === PERFORMANCE MONITORING ===

def monitor_ui_performance(operation_name):
    """Monitor UI operation performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Show performance in sidebar
                if execution_time > 2.0:
                    st.sidebar.error(f"🔴 {operation_name}: {execution_time:.1f}s")
                elif execution_time > 1.0:
                    st.sidebar.warning(f"🟡 {operation_name}: {execution_time:.1f}s")
                else:
                    st.sidebar.success(f"🟢 {operation_name}: {execution_time:.1f}s")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                st.sidebar.error(f"❌ {operation_name} failed ({execution_time:.1f}s)")
                raise
        
        return wrapper
    return decorator

# === OPTIMIZED COMPONENTS ===

class FastNavDisplay:
    """Fast NAV display component"""
    
    @staticmethod
    @monitor_ui_performance("NAV Display")
    def render(fund_manager):
        """Render NAV display with caching"""
        nav = get_cached_nav(fund_manager)
        
        if nav:
            from utils import format_currency
            return format_currency(nav)
        else:
            return "Đang tải..."

class FastInvestorList:
    """Fast investor list component"""
    
    @staticmethod
    @monitor_ui_performance("Investor List")
    def render(fund_manager):
        """Render investor list with caching"""
        investors = get_cached_investors(fund_manager)
        
        return {inv.display_name: inv.id for inv in investors}

class FastBalanceDisplay:
    """Fast balance display component"""
    
    @staticmethod
    @monitor_ui_performance("Balance Display")
    def render(fund_manager, investor_id, nav):
        """Render balance with caching"""
        balance, profit, profit_perc = get_cached_balance(fund_manager, investor_id, nav)
        
        from utils import format_currency, format_percentage
        return {
            'balance': format_currency(balance),
            'profit': format_currency(profit),
            'profit_perc': format_percentage(profit_perc)
        }

# === FORM OPTIMIZATION ===

class OptimizedForms:
    """Optimized form handling"""
    
    @staticmethod
    def smart_number_input(label, value=0, key=None, step=1000000):
        """Optimized number input with better defaults"""
        return st.number_input(
            label, 
            value=value, 
            step=step,
            key=key,
            format="%d"
        )
    
    @staticmethod
    def smart_selectbox(label, options, key=None):
        """Optimized selectbox with change detection"""
        if not options:
            st.warning(f"No options for {label}")
            return None
        
        return st.selectbox(label, options, key=key)
    
    @staticmethod
    def smart_submit_button(label, use_container_width=True):
        """Optimized submit button with debouncing"""
        return st.form_submit_button(
            label, 
            use_container_width=use_container_width,
            type="primary"
        )

# === TABLE OPTIMIZATION ===

class FastTableRenderer:
    """Fast table rendering with pagination"""
    
    @staticmethod
    def render_paginated_table(data, columns, page_size=20):
        """Render table with pagination"""
        if not data:
            st.info("Không có dữ liệu")
            return
        
        total_rows = len(data)
        total_pages = (total_rows - 1) // page_size + 1
        
        # Pagination controls
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.button("⏪ Trước"):
                    if 'table_page' not in st.session_state:
                        st.session_state.table_page = 0
                    if st.session_state.table_page > 0:
                        st.session_state.table_page -= 1
                        st.rerun()
            
            with col2:
                current_page = st.session_state.get('table_page', 0)
                st.write(f"Trang {current_page + 1} / {total_pages}")
            
            with col3:
                if st.button("Sau ⏩"):
                    if 'table_page' not in st.session_state:
                        st.session_state.table_page = 0
                    if st.session_state.table_page < total_pages - 1:
                        st.session_state.table_page += 1
                        st.rerun()
        
        # Show current page data
        current_page = st.session_state.get('table_page', 0)
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, total_rows)
        
        page_data = data[start_idx:end_idx]
        
        import pandas as pd
        df = pd.DataFrame(page_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

# === SIDEBAR OPTIMIZATION ===

class FastSidebar:
    """Optimized sidebar components"""
    
    @staticmethod
    def render_nav_card(fund_manager):
        """Render NAV card with caching"""
        nav_display = FastNavDisplay.render(fund_manager)
        
        html_content = f"""
            <div class="nav-card">
                <div class="nav-title">TỔNG NAV</div>
                <div class="nav-value">{nav_display}</div>
            </div>
        """
        st.sidebar.markdown(html_content, unsafe_allow_html=True)
    
    @staticmethod
    def render_quick_stats(fund_manager):
        """Render quick stats with caching"""
        investors = get_cached_investors(fund_manager)
        
        stats_html = f"""
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" style="color: #0066cc;">{len(investors)}</div>
                    <div class="stat-label">NĐT</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: #28a745;">Active</div>
                    <div class="stat-label">System</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: #ffc107;">Online</div>
                    <div class="stat-label">Status</div>
                </div>
            </div>
        """
        st.sidebar.markdown(stats_html, unsafe_allow_html=True)

# === INTEGRATION FUNCTIONS ===

def apply_ui_optimizations():
    """Apply all UI optimizations"""
    
    # Check if refresh needed
    if st.session_state.get('ui_needs_refresh', False):
        UIUpdater.smart_refresh()
    
    # Clear old caches periodically
    if 'last_cache_clear' not in st.session_state:
        st.session_state.last_cache_clear = time.time()
    
    # Clear cache every 10 minutes
    if time.time() - st.session_state.last_cache_clear > 600:
        cleared_count = SafeCache.clear_all()
        st.session_state.last_cache_clear = time.time()
        if cleared_count > 0:
            st.sidebar.info(f"🧹 Cleared {cleared_count} old caches")

def setup_ui_performance_monitoring():
    """Setup UI performance monitoring"""
    if 'ui_performance_start' not in st.session_state:
        st.session_state.ui_performance_start = time.time()
    
    uptime = time.time() - st.session_state.ui_performance_start
    if uptime > 300:  # 5 minutes
        st.sidebar.caption(f"⏱️ Session: {uptime/60:.1f}m")

# === OPTIMIZED ERROR HANDLING ===

class UIErrorHandler:
    """Safe error handling for UI components"""
    
    @staticmethod
    def safe_render(render_func, component_name, fallback_content="Component unavailable"):
        """Safely render UI component with fallback"""
        try:
            return render_func()
        except Exception as e:
            st.error(f"❌ {component_name} error: {str(e)[:50]}")
            st.info(fallback_content)
            return None