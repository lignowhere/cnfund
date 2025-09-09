# data_utils_optimized.py - Performance-optimized utility functions

import streamlit as st
import re
import time
from typing import List, Dict, Any, Optional, Union
from functools import lru_cache, wraps
from datetime import datetime, date
import pandas as pd
from timezone_manager import TimezoneManager

# === PERFORMANCE-OPTIMIZED FORMATTING FUNCTIONS ===

@lru_cache(maxsize=1000)
def format_currency_cached(amount: float, compact: bool = False) -> str:
    """Cached version of currency formatting for better performance"""
    if amount is None or pd.isna(amount):
        return "0đ"
    
    try:
        amount = float(amount)
        if compact and abs(amount) >= 1_000_000:
            if abs(amount) >= 1_000_000_000:
                return f"{amount/1_000_000_000:.1f}Tđ"
            else:
                return f"{amount/1_000_000:.0f}Mđ"
        
        return f"{amount:,.0f}đ"
    except (ValueError, TypeError):
        return "0đ"

@lru_cache(maxsize=500)
def format_percentage_cached(value: float, decimals: int = 2) -> str:
    """Cached percentage formatting"""
    if value is None or pd.isna(value):
        return "0%"
    
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (ValueError, TypeError):
        return "0%"

@lru_cache(maxsize=200)
def parse_currency_cached(text: str) -> float:
    """Cached currency parsing with enhanced error handling"""
    if not text:
        return 0.0
    
    # Convert to string and clean
    clean_text = str(text).strip()
    if not clean_text:
        return 0.0
    
    # Remove currency symbols, commas, spaces
    clean_text = re.sub(r'[đĐ,\s]', '', clean_text)
    
    # Handle empty after cleaning
    if not clean_text:
        return 0.0
    
    try:
        # Try to convert to float
        value = float(clean_text)
        return max(0.0, value)  # Ensure non-negative
    except (ValueError, TypeError):
        return 0.0

# === BATCH PROCESSING FUNCTIONS ===

def batch_format_currency(amounts: List[float], compact: bool = False) -> List[str]:
    """Batch format currencies for better performance in tables"""
    return [format_currency_cached(amount, compact) for amount in amounts]

def batch_format_percentage(values: List[float], decimals: int = 2) -> List[str]:
    """Batch format percentages"""
    return [format_percentage_cached(value, decimals) for value in values]

# === SMART CACHING DECORATOR ===

def smart_cache(expire_seconds: int = 300, key_func=None):
    """Smart caching decorator with expiration"""
    def decorator(func):
        cache_store = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = str(hash((args, tuple(sorted(kwargs.items())))))
            
            current_time = time.time()
            
            # Check if cached result exists and is still valid
            if cache_key in cache_store:
                cached_result, cached_time = cache_store[cache_key]
                if current_time - cached_time < expire_seconds:
                    return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_store[cache_key] = (result, current_time)
            
            # Clean old cache entries periodically
            if len(cache_store) > 100:
                cutoff_time = current_time - expire_seconds
                cache_store = {
                    k: v for k, v in cache_store.items() 
                    if v[1] > cutoff_time
                }
            
            return result
        
        return wrapper
    return decorator

# === OPTIMIZED DATA VALIDATION ===

class FastValidator:
    """High-performance data validator"""
    
    @staticmethod
    @lru_cache(maxsize=100)
    def validate_email_cached(email: str) -> bool:
        """Cached email validation"""
        if not email or not isinstance(email, str):
            return True  # Empty email is allowed
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    @staticmethod
    @lru_cache(maxsize=100)
    def validate_phone_cached(phone: str) -> bool:
        """Cached phone validation"""
        if not phone or not isinstance(phone, str):
            return True  # Empty phone is allowed
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        return len(digits_only) >= 9 and len(digits_only) <= 15
    
    @staticmethod
    def validate_amount(amount: Union[str, float, int]) -> tuple[bool, str]:
        """Fast amount validation"""
        try:
            if isinstance(amount, str):
                parsed_amount = parse_currency_cached(amount)
            else:
                parsed_amount = float(amount)
            
            if parsed_amount < 0:
                return False, "Số tiền không được âm"
            
            if parsed_amount > 1_000_000_000_000:  # 1 trillion VND
                return False, "Số tiền quá lớn"
            
            return True, ""
            
        except (ValueError, TypeError):
            return False, "Số tiền không hợp lệ"

# === PERFORMANCE-OPTIMIZED ERROR HANDLER ===

class OptimizedErrorHandler:
    """Performance-optimized error handling"""
    
    def __init__(self, operation: str, show_details: bool = False):
        self.operation = operation
        self.show_details = show_details
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            execution_time = time.time() - self.start_time if self.start_time else 0
            
            error_msg = f"❌ Lỗi {self.operation}"
            if execution_time > 0:
                error_msg += f" (sau {execution_time:.1f}s)"
            
            if self.show_details:
                error_msg += f": {str(exc_val)}"
            
            st.error(error_msg)
            
            # Log to session state for debugging
            if 'error_log' not in st.session_state:
                st.session_state.error_log = []
            
            st.session_state.error_log.append({
                'timestamp': TimezoneManager.now(),
                'operation': self.operation,
                'error': str(exc_val),
                'execution_time': execution_time
            })
            
            # Keep only last 50 errors
            if len(st.session_state.error_log) > 50:
                st.session_state.error_log = st.session_state.error_log[-50:]
            
            return True  # Suppress the exception
        
        return False

# === OPTIMIZED DATAFRAME OPERATIONS ===

class FastDataFrame:
    """Performance-optimized DataFrame operations"""
    
    @staticmethod
    def create_optimized_df(data: List[Dict], columns: List[str] = None) -> pd.DataFrame:
        """Create DataFrame with optimized dtypes"""
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Optimize dtypes
        for col in df.columns:
            if col.endswith('_id') or col == 'ID':
                df[col] = pd.to_numeric(df[col], errors='coerce', downcast='integer')
            elif 'date' in col.lower() or 'time' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
            elif 'amount' in col.lower() or 'nav' in col.lower() or 'units' in col.lower():
                df[col] = pd.to_numeric(df[col], errors='coerce', downcast='float')
        
        return df
    
    @staticmethod
    def format_df_for_display(df: pd.DataFrame, currency_cols: List[str] = None, 
                             percentage_cols: List[str] = None) -> pd.DataFrame:
        """Format DataFrame for optimized display"""
        if df.empty:
            return df
        
        display_df = df.copy()
        
        # Batch format currency columns
        if currency_cols:
            for col in currency_cols:
                if col in display_df.columns:
                    amounts = display_df[col].fillna(0).tolist()
                    display_df[col] = batch_format_currency(amounts)
        
        # Batch format percentage columns
        if percentage_cols:
            for col in percentage_cols:
                if col in display_df.columns:
                    values = display_df[col].fillna(0).tolist()
                    display_df[col] = batch_format_percentage(values)
        
        return display_df
    
    @staticmethod
    def paginate_dataframe(df: pd.DataFrame, page_size: int = 50, page_num: int = 0) -> tuple[pd.DataFrame, int]:
        """Paginate DataFrame for better performance"""
        if df.empty:
            return df, 0
        
        total_pages = (len(df) - 1) // page_size + 1
        start_idx = page_num * page_size
        end_idx = min(start_idx + page_size, len(df))
        
        return df.iloc[start_idx:end_idx], total_pages

# === MEMORY OPTIMIZATION ===

class MemoryOptimizer:
    """Memory usage optimization"""
    
    @staticmethod
    def cleanup_session_state(keep_patterns: List[str] = None):
        """Cleanup session state keeping only essential data"""
        if keep_patterns is None:
            keep_patterns = ['logged_in', 'app_start_time', 'fund_manager', 'data_handler']
        
        keys_to_remove = []
        for key in st.session_state.keys():
            should_keep = any(pattern in key for pattern in keep_patterns)
            if not should_keep:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state[key]
        
        return len(keys_to_remove)
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get current memory usage information"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'cpu_percent': process.cpu_percent(),
                'session_state_items': len(st.session_state.keys())
            }
        except ImportError:
            return {'error': 'psutil not available'}

# === BACKWARD COMPATIBILITY ===

# Keep original function names for backward compatibility
def format_currency_safe(amount: float, compact: bool = False) -> str:
    """Backward compatible currency formatting"""
    return format_currency_cached(amount, compact)

def validate_email(email: str) -> bool:
    """Backward compatible email validation"""
    return FastValidator.validate_email_cached(email)

def validate_phone(phone: str) -> bool:
    """Backward compatible phone validation"""
    return FastValidator.validate_phone_cached(phone)

# Use optimized error handler as default
ErrorHandler = OptimizedErrorHandler

# === UTILITY CONSTANTS ===

EPSILON = 1e-6
DEFAULT_UNIT_PRICE = 1000000.0  # 1M VND
HURDLE_RATE_ANNUAL = 0.06  # 6%
PERFORMANCE_FEE_RATE = 0.20  # 20%

# === PERFORMANCE MONITORING HELPERS ===

def time_function(func_name: str):
    """Decorator to time function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log slow functions
            if execution_time > 1.0:
                st.sidebar.caption(f"⚠️ {func_name}: {execution_time:.1f}s")
            
            return result
        return wrapper
    return decorator

@smart_cache(expire_seconds=60)
def get_cached_stats(data_list: List) -> Dict[str, Any]:
    """Get cached statistics for data collections"""
    if not data_list:
        return {'count': 0, 'is_empty': True}
    
    return {
        'count': len(data_list),
        'is_empty': False,
        'last_updated': TimezoneManager.now().isoformat()
    }