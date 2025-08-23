# performance_optimizer.py - Comprehensive performance optimization

import streamlit as st
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
import asyncio
from functools import wraps

class PerformanceOptimizer:
    """Comprehensive performance optimization for the fund management system"""
    
    def __init__(self):
        self.cache_duration = 300  # 5 minutes default cache
        self.debug_mode = st.secrets.get("DEBUG_MODE", False)
        
    @staticmethod
    def smart_cache_key(*args, **kwargs) -> str:
        """Generate intelligent cache key based on data state"""
        # Create hash from arguments and current data state
        key_data = {
            'args': args,
            'kwargs': kwargs,
            'timestamp': int(time.time() / 60)  # Cache per minute
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()
    
    @staticmethod
    def conditional_rerun(condition_func, delay=0.5):
        """Only rerun if condition is met, with debouncing"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                
                # Check if rerun is needed
                if condition_func():
                    # Debounce reruns
                    last_rerun = st.session_state.get('last_rerun_time', 0)
                    current_time = time.time()
                    
                    if current_time - last_rerun > delay:
                        st.session_state.last_rerun_time = current_time
                        st.rerun()
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def cached_data_loader(cache_key: str, loader_func, expire_minutes: int = 5):
        """Intelligent data caching with expiration"""
        cache_data = st.session_state.get(f'cache_{cache_key}', {})
        
        # Check if cache exists and is valid
        if cache_data:
            cache_time = cache_data.get('timestamp', 0)
            expire_time = cache_time + (expire_minutes * 60)
            
            if time.time() < expire_time:
                return cache_data['data']
        
        # Cache expired or doesn't exist, reload
        with st.spinner("⚡ Đang tải dữ liệu..."):
            start_time = time.time()
            data = loader_func()
            load_time = time.time() - start_time
            
            # Store in cache
            st.session_state[f'cache_{cache_key}'] = {
                'data': data,
                'timestamp': time.time(),
                'load_time': load_time
            }
            
            if load_time > 2:
                st.warning(f"⚠️ Tải dữ liệu chậm: {load_time:.1f}s")
        
        return data

    @staticmethod
    def invalidate_cache(pattern: str = "cache_"):
        """Invalidate cached data matching pattern"""
        keys_to_remove = [
            key for key in st.session_state.keys() 
            if key.startswith(pattern)
        ]
        
        for key in keys_to_remove:
            del st.session_state[key]
        
        if keys_to_remove:
            st.toast(f"🔄 Đã làm mới {len(keys_to_remove)} cache entries")

    @staticmethod 
    def optimize_database_queries():
        """Database query optimization suggestions"""
        return {
            'add_indexes': [
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tranches_investor_entry ON tranches(investor_id, entry_date DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_investor_date ON transactions(investor_id, date DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_type_date ON transactions(type, date DESC)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fee_records_period_investor ON fee_records(period, investor_id)"
            ],
            'query_optimizations': [
                "Use LIMIT for large result sets",
                "Implement pagination for transaction history", 
                "Use connection pooling",
                "Cache frequently accessed calculations"
            ]
        }

class OptimizedFundManager:
    """Performance-optimized version of FundManager"""
    
    def __init__(self, original_fund_manager):
        self.original = original_fund_manager
        self.optimizer = PerformanceOptimizer()
        
    def get_cached_nav(self) -> Optional[float]:
        """Get cached NAV with intelligent refresh"""
        def load_nav():
            return self.original.get_latest_total_nav()
        
        return self.optimizer.cached_data_loader(
            'latest_nav', 
            load_nav, 
            expire_minutes=2  # NAV cache for 2 minutes
        )
    
    def get_cached_investor_balance(self, investor_id: int, nav: float) -> tuple:
        """Cache investor balance calculations"""
        cache_key = f'balance_{investor_id}_{int(nav)}'
        
        def load_balance():
            return self.original.get_investor_balance(investor_id, nav)
        
        return self.optimizer.cached_data_loader(cache_key, load_balance, expire_minutes=1)
    
    def get_cached_fee_calculation(self, investor_id: int, ending_date: datetime, nav: float) -> Dict:
        """Cache fee calculations"""
        cache_key = f'fee_{investor_id}_{ending_date.date()}_{int(nav)}'
        
        def load_fee():
            return self.original.calculate_investor_fee(investor_id, ending_date, nav)
        
        return self.optimizer.cached_data_loader(cache_key, load_fee, expire_minutes=5)
    
    @PerformanceOptimizer.conditional_rerun(lambda: st.session_state.get('data_changed', False))
    def optimized_save_data(self) -> bool:
        """Optimized save with intelligent rerun"""
        success = self.original.save_data()
        
        if success:
            # Invalidate relevant caches
            self.optimizer.invalidate_cache("cache_")
            st.session_state.data_changed = False
            st.toast("✅ Đã lưu dữ liệu!", icon="💾")
        
        return success

class OptimizedUIComponents:
    """Performance-optimized UI components"""
    
    @staticmethod
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def format_currency_table(amounts: List[float]) -> List[str]:
        """Batch format currency for better performance"""
        from utils import format_currency
        return [format_currency(amount) for amount in amounts]
    
    @staticmethod
    def lazy_dataframe(data_func, columns: List[str], page_size: int = 50):
        """Implement pagination for large datasets"""
        if 'df_page' not in st.session_state:
            st.session_state.df_page = 0
        
        # Get total data count without loading all data
        total_data = data_func()
        total_pages = (len(total_data) - 1) // page_size + 1
        
        # Display pagination controls
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("⏮️ Đầu", disabled=st.session_state.df_page == 0):
                st.session_state.df_page = 0
                st.rerun()
        
        with col2:
            if st.button("⏪ Trước", disabled=st.session_state.df_page == 0):
                st.session_state.df_page -= 1
                st.rerun()
        
        with col3:
            st.write(f"Trang {st.session_state.df_page + 1} / {total_pages}")
        
        with col4:
            if st.button("⏩ Sau", disabled=st.session_state.df_page >= total_pages - 1):
                st.session_state.df_page += 1
                st.rerun()
        
        with col5:
            if st.button("⏭️ Cuối", disabled=st.session_state.df_page >= total_pages - 1):
                st.session_state.df_page = total_pages - 1
                st.rerun()
        
        # Show current page data
        start_idx = st.session_state.df_page * page_size
        end_idx = min(start_idx + page_size, len(total_data))
        page_data = total_data[start_idx:end_idx]
        
        return page_data
    
    @staticmethod
    def smart_selectbox(label: str, options: List, key: str, on_change_callback=None):
        """Optimized selectbox with change detection"""
        previous_value = st.session_state.get(f"{key}_prev", None)
        
        current_value = st.selectbox(label, options, key=key)
        
        # Detect actual changes
        if current_value != previous_value:
            st.session_state[f"{key}_prev"] = current_value
            if on_change_callback:
                on_change_callback(current_value)
        
        return current_value

class DatabaseOptimizer:
    """Database-specific optimizations"""
    
    def __init__(self, data_handler):
        self.data_handler = data_handler
    
    def create_performance_indexes(self):
        """Create performance-critical indexes with safe connection handling"""
        if not self.data_handler.connected:
            st.error("❌ Database not connected")
            return False
        
        # Simple indexes only (avoid CONCURRENTLY in transactions)
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_investors_fund_manager ON investors(is_fund_manager)",
            "CREATE INDEX IF NOT EXISTS idx_tranches_investor_id ON tranches(investor_id)", 
            "CREATE INDEX IF NOT EXISTS idx_tranches_entry_date ON tranches(entry_date)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_investor_date ON transactions(investor_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)",
            "CREATE INDEX IF NOT EXISTS idx_fee_records_investor_period ON fee_records(investor_id, period)",
            "CREATE INDEX IF NOT EXISTS idx_fee_records_calc_date ON fee_records(calculation_date)"
        ]
        
        success_count = 0
        try:
            from sqlalchemy import text
            
            # Use a simple approach - one connection, one transaction
            with self.data_handler.engine.connect() as conn:
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                        conn.commit()
                        success_count += 1
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "already exists" not in error_msg:
                            st.warning(f"⚠️ Index warning: {str(e)[:100]}")
                        else:
                            success_count += 1  # Count existing indexes as success
            
            st.success(f"✅ Processed {success_count}/{len(indexes)} performance indexes")
            
            # Show simple index status
            self._show_simple_index_status()
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error with indexes: {str(e)[:200]}")
            return False
    
    def _show_simple_index_status(self):
        """Show simplified index status"""
        try:
            from sqlalchemy import text
            with self.data_handler.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(*) as index_count
                    FROM pg_indexes 
                    WHERE schemaname = 'public' 
                    AND indexname LIKE 'idx_%'
                """))
                
                row = result.fetchone()
                if row:
                    index_count = row[0]
                    st.info(f"📊 Found {index_count} custom indexes in database")
                
        except Exception as e:
            st.info("ℹ️ Could not retrieve index information")
    
    def analyze_query_performance(self):
        """Analyze and suggest query optimizations"""
        suggestions = []
        
        try:
            from sqlalchemy import text
            with self.data_handler.engine.connect() as conn:
                # Check table sizes
                result = conn.execute(text("""
                    SELECT 
                        schemaname, tablename, 
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """))
                
                tables_info = result.fetchall()
                for table in tables_info:
                    if table.size_bytes > 10000000:  # > 10MB
                        suggestions.append(f"Large table {table.tablename} ({table.size}) - consider archiving old data")
                
                # Check for missing indexes on foreign keys
                result = conn.execute(text("""
                    SELECT tablename, attname, n_distinct, correlation
                    FROM pg_stats 
                    WHERE schemaname = 'public' 
                    AND attname LIKE '%_id'
                    ORDER BY n_distinct DESC
                """))
                
                fk_stats = result.fetchall()
                for stat in fk_stats:
                    if abs(stat.correlation) < 0.1:
                        suggestions.append(f"Consider index on {stat.tablename}.{stat.attname} (low correlation: {stat.correlation:.3f})")
                
                return suggestions
                
        except Exception as e:
            return [f"Error analyzing performance: {e}"]

# Performance monitoring decorator
def performance_monitor(func_name: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log slow operations
                if execution_time > 2.0:
                    st.warning(f"⚠️ Slow operation: {func_name} took {execution_time:.2f}s")
                elif execution_time > 1.0:
                    st.info(f"ℹ️ {func_name} completed in {execution_time:.2f}s")
                
                # Store performance metrics
                if 'performance_metrics' not in st.session_state:
                    st.session_state.performance_metrics = {}
                
                st.session_state.performance_metrics[func_name] = {
                    'last_execution_time': execution_time,
                    'timestamp': datetime.now(),
                    'success': True
                }
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log errors with timing
                st.error(f"❌ {func_name} failed after {execution_time:.2f}s: {e}")
                
                st.session_state.performance_metrics[func_name] = {
                    'last_execution_time': execution_time,
                    'timestamp': datetime.now(),
                    'success': False,
                    'error': str(e)
                }
                
                raise
        
        return wrapper
    return decorator

class PerformanceDashboard:
    """Dashboard to monitor application performance"""
    
    @staticmethod
    def render_performance_metrics():
        """Render performance monitoring dashboard"""
        if 'performance_metrics' not in st.session_state:
            st.info("📊 No performance metrics available yet")
            return
        
        metrics = st.session_state.performance_metrics
        
        st.subheader("📈 Performance Metrics")
        
        # Summary stats
        total_operations = len(metrics)
        successful_operations = sum(1 for m in metrics.values() if m.get('success', False))
        avg_execution_time = sum(m['last_execution_time'] for m in metrics.values()) / total_operations if total_operations > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Operations", total_operations)
        col2.metric("Success Rate", f"{successful_operations/total_operations*100:.1f}%" if total_operations > 0 else "0%")
        col3.metric("Avg Execution Time", f"{avg_execution_time:.2f}s")
        
        # Detailed metrics table
        if st.checkbox("Show Detailed Metrics"):
            import pandas as pd
            
            metrics_data = []
            for func_name, data in metrics.items():
                metrics_data.append({
                    'Function': func_name,
                    'Execution Time (s)': f"{data['last_execution_time']:.3f}",
                    'Status': '✅ Success' if data.get('success', False) else '❌ Failed',
                    'Last Run': data['timestamp'].strftime('%H:%M:%S'),
                    'Error': data.get('error', '-')[:50] + '...' if data.get('error', '') else '-'
                })
            
            df = pd.DataFrame(metrics_data)
            st.dataframe(df, use_container_width=True)
        
        # Clear metrics button
        if st.button("🗑️ Clear Performance Metrics"):
            del st.session_state.performance_metrics
            st.rerun()