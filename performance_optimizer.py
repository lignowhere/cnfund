#!/usr/bin/env python3
"""
Performance Optimization Module for Streamlit Cloud
Includes async operations, caching, and deferred processing
"""

import asyncio
import time
from typing import Callable, Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
from functools import wraps
import threading
import queue
import json
from datetime import datetime, timedelta

class PerformanceOptimizer:
    """Performance optimization utilities for Streamlit Cloud"""
    
    def __init__(self):
        self.background_tasks = queue.Queue()
        self.cache = {}
        self.cache_expiry = {}
        self.background_thread = None
        self.running = False
        self.start_background_processor()
    
    def start_background_processor(self):
        """Start background thread for processing deferred tasks"""
        if not self.running:
            self.running = True
            self.background_thread = threading.Thread(
                target=self._background_worker, 
                daemon=True
            )
            self.background_thread.start()
    
    def _background_worker(self):
        """Background worker thread for processing queued tasks"""
        while self.running:
            try:
                if not self.background_tasks.empty():
                    task = self.background_tasks.get(timeout=1)
                    if task:
                        func, args, kwargs = task
                        try:
                            func(*args, **kwargs)
                        except Exception as e:
                            print(f"Background task error: {e}")
                        finally:
                            self.background_tasks.task_done()
                else:
                    time.sleep(0.1)  # Small delay to prevent CPU spinning
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Background worker error: {e}")
                time.sleep(1)
    
    def defer_task(self, func: Callable, *args, **kwargs):
        """Queue a task for background processing"""
        self.background_tasks.put((func, args, kwargs))
    
    def cached_operation(self, cache_key: str, ttl_seconds: int = 300):
        """Decorator for caching expensive operations"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                now = datetime.now()
                
                # Check if cached result exists and is still valid
                if (cache_key in self.cache and 
                    cache_key in self.cache_expiry and 
                    now < self.cache_expiry[cache_key]):
                    return self.cache[cache_key]
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.cache[cache_key] = result
                self.cache_expiry[cache_key] = now + timedelta(seconds=ttl_seconds)
                return result
            return wrapper
        return decorator
    
    def clear_cache(self, pattern: str = None):
        """Clear cache entries matching pattern"""
        if pattern is None:
            self.cache.clear()
            self.cache_expiry.clear()
        else:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                self.cache.pop(key, None)
                self.cache_expiry.pop(key, None)
    
    def batch_operation(self, operations: list, batch_size: int = 10):
        """Execute operations in batches to prevent blocking"""
        results = []
        for i in range(0, len(operations), batch_size):
            batch = operations[i:i + batch_size]
            batch_results = []
            for op in batch:
                func, args, kwargs = op
                try:
                    result = func(*args, **kwargs)
                    batch_results.append(result)
                except Exception as e:
                    print(f"Batch operation error: {e}")
                    batch_results.append(None)
            results.extend(batch_results)
        return results

class FastTransactionProcessor:
    """Optimized transaction processor for Streamlit Cloud"""
    
    def __init__(self, fund_manager, optimizer: PerformanceOptimizer):
        self.fund_manager = fund_manager
        self.optimizer = optimizer
        self.pending_saves = set()
    
    def process_transaction_fast(self, transaction_func, *args, **kwargs):
        """
        Process transaction with immediate UI feedback and deferred operations
        """
        start_time = time.time()
        
        try:
            # Execute core transaction logic immediately
            result = transaction_func(*args, **kwargs)
            
            # Show immediate success feedback
            if result[0]:  # Success
                st.success(f"✅ {result[1]}")
                
                # Defer heavy operations to background
                self.optimizer.defer_task(self._deferred_save_and_backup, transaction_func.__name__)
                
                # Clear relevant caches immediately
                self.optimizer.clear_cache("nav")
                self.optimizer.clear_cache("balance")
                
                # Set flag for data change without saving immediately
                st.session_state.data_changed = True
                st.session_state.needs_background_save = True
                
                processing_time = time.time() - start_time
                print(f"⚡ Transaction processed in {processing_time:.2f}s")
                
                return True, result[1]
            else:
                st.error(f"❌ {result[1]}")
                return False, result[1]
                
        except Exception as e:
            st.error(f"❌ Transaction error: {str(e)}")
            return False, str(e)
    
    def _deferred_save_and_backup(self, operation_name: str):
        """Perform save and backup operations in background"""
        try:
            # Save data to database
            if hasattr(self.fund_manager, 'save_data'):
                save_success = self.fund_manager.save_data()
                if save_success:
                    print(f"💾 Background save completed for {operation_name}")
                else:
                    print(f"⚠️ Background save failed for {operation_name}")
            
            # Create backup if enabled (low priority)
            if hasattr(self.fund_manager, '_auto_backup_if_enabled'):
                self.fund_manager._auto_backup_if_enabled(operation_name, f"Deferred backup for {operation_name}")
                print(f"📦 Background backup completed for {operation_name}")
                
        except Exception as e:
            print(f"❌ Background save/backup error for {operation_name}: {e}")
    
    def ensure_background_save_completed(self):
        """Ensure all pending background saves are completed"""
        if st.session_state.get('needs_background_save', False):
            # Wait for background tasks to complete (with timeout)
            max_wait = 5  # seconds
            wait_time = 0
            while (not self.optimizer.background_tasks.empty() and wait_time < max_wait):
                time.sleep(0.1)
                wait_time += 0.1
            
            st.session_state.needs_background_save = False
            
            if wait_time >= max_wait:
                st.warning("⚠️ Background save may still be in progress")
            else:
                print(f"✅ Background save completed in {wait_time:.1f}s")

class StreamlitCloudOptimizer:
    """Streamlit Cloud specific optimizations"""
    
    @staticmethod
    def optimize_dataframe_display(df, max_rows: int = 1000):
        """Optimize large dataframe display for cloud"""
        if len(df) > max_rows:
            st.warning(f"⚠️ Hiển thị {max_rows} dòng đầu tiên (tổng: {len(df)} dòng)")
            return df.head(max_rows)
        return df
    
    @staticmethod
    def lazy_load_component(component_func, placeholder_text: str = "Đang tải..."):
        """Lazy load heavy components"""
        placeholder = st.empty()
        with placeholder:
            st.info(placeholder_text)
        
        try:
            result = component_func()
            placeholder.empty()
            return result
        except Exception as e:
            placeholder.error(f"❌ Lỗi tải component: {e}")
            return None
    
    @staticmethod
    def minimize_rerun_triggers():
        """Minimize unnecessary reruns"""
        # Clear session state keys that trigger unnecessary reruns
        keys_to_clear = [
            'last_action_time',
            'temp_status',
            'loading_state'
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    @staticmethod
    def batch_ui_updates(updates: list):
        """Batch multiple UI updates to reduce rerun frequency"""
        for update_func in updates:
            try:
                update_func()
            except Exception as e:
                print(f"UI update error: {e}")

# Global optimizer instance
_optimizer = None

def get_optimizer() -> PerformanceOptimizer:
    """Get global optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    return _optimizer

def create_fast_processor(fund_manager) -> FastTransactionProcessor:
    """Create optimized transaction processor"""
    optimizer = get_optimizer()
    return FastTransactionProcessor(fund_manager, optimizer)

# Convenience decorators
def fast_operation(cache_ttl: int = 300):
    """Decorator for fast cached operations"""
    optimizer = get_optimizer()
    def decorator(func):
        cache_key = f"{func.__name__}_{id(func)}"
        return optimizer.cached_operation(cache_key, cache_ttl)(func)
    return decorator

def defer_heavy_operation(func):
    """Decorator to defer heavy operations to background"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        optimizer = get_optimizer()
        optimizer.defer_task(func, *args, **kwargs)
        return True  # Return immediately
    return wrapper