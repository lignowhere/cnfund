# save_optimization.py - Optimize save operations for better performance

import streamlit as st
import time
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

class SaveOptimizer:
    """Optimize save operations for better performance"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
        self.data_handler = fund_manager.data_handler
    
    def optimized_save_all(self) -> tuple[bool, str, Dict[str, float]]:
        """Optimized save operation with detailed timing"""
        start_time = time.time()
        timing_info = {}
        
        try:
            # Step 1: Quick validation (don't do full validation if not needed)
            validation_start = time.time()
            if not self._quick_data_check():
                return False, "Quick data validation failed", timing_info
            timing_info['validation'] = time.time() - validation_start
            
            # Step 2: Prepare data for batch operations
            prep_start = time.time()
            data_batches = self._prepare_data_batches()
            timing_info['preparation'] = time.time() - prep_start
            
            # Step 3: Execute batch save with transaction
            save_start = time.time()
            success = self._execute_batch_save(data_batches)
            timing_info['save_execution'] = time.time() - save_start
            
            # Step 4: Post-save cleanup
            cleanup_start = time.time()
            if success:
                self._post_save_cleanup()
            timing_info['cleanup'] = time.time() - cleanup_start
            
            total_time = time.time() - start_time
            timing_info['total'] = total_time
            
            message = f"Save completed in {total_time:.1f}s"
            if total_time > 5:
                message += " (slower than expected)"
            
            return success, message, timing_info
            
        except Exception as e:
            total_time = time.time() - start_time
            timing_info['total'] = total_time
            return False, f"Save failed after {total_time:.1f}s: {str(e)}", timing_info
    
    def _quick_data_check(self) -> bool:
        """Quick data consistency check (not full validation)"""
        try:
            # Just check basic data integrity
            if not self.fund_manager.investors:
                return False
            
            # Check if fund manager exists
            fund_manager = self.fund_manager.get_fund_manager()
            if not fund_manager:
                return False
            
            # Check for obvious data issues
            for tranche in self.fund_manager.tranches:
                if tranche.units <= 0:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _prepare_data_batches(self) -> Dict[str, List]:
        """Prepare data in optimized batches"""
        return {
            'investors': self.fund_manager.investors,
            'tranches': self.fund_manager.tranches,
            'transactions': self.fund_manager.transactions,
            'fee_records': self.fund_manager.fee_records
        }
    
    def _execute_batch_save(self, data_batches: Dict[str, List]) -> bool:
        """Execute optimized batch save operation"""
        try:
            # Use the existing optimized save method
            return self.data_handler.save_all_data_enhanced(
                data_batches['investors'],
                data_batches['tranches'],
                data_batches['transactions'],
                data_batches['fee_records']
            )
        except Exception as e:
            st.error(f"Batch save failed: {str(e)}")
            return False
    
    def _post_save_cleanup(self):
        """Post-save cleanup operations"""
        # Clear any temporary data
        if hasattr(st.session_state, 'temp_data'):
            del st.session_state.temp_data
        
        # Mark data as clean
        st.session_state.data_changed = False

class AsyncSaveManager:
    """Manage asynchronous save operations for better user experience"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
        self.save_optimizer = SaveOptimizer(fund_manager)
    
    def save_with_progress(self) -> bool:
        """Save with detailed progress feedback"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Validation
            status_text.text("🔍 Validating data...")
            progress_bar.progress(20)
            
            if not self.save_optimizer._quick_data_check():
                status_text.error("❌ Data validation failed")
                return False
            
            # Step 2: Preparation
            status_text.text("📋 Preparing data...")
            progress_bar.progress(40)
            time.sleep(0.1)  # Small delay for UI feedback
            
            # Step 3: Save execution
            status_text.text("💾 Saving to database...")
            progress_bar.progress(60)
            
            success, message, timing_info = self.save_optimizer.optimized_save_all()
            
            progress_bar.progress(90)
            
            if success:
                # Step 4: Finalization
                status_text.text("✅ Finalizing...")
                progress_bar.progress(100)
                time.sleep(0.2)
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Show detailed timing
                self._show_save_performance(timing_info)
                
                return True
            else:
                progress_bar.empty()
                status_text.error(f"❌ {message}")
                return False
                
        except Exception as e:
            progress_bar.empty()
            status_text.error(f"❌ Save error: {str(e)}")
            return False
    
    def _show_save_performance(self, timing_info: Dict[str, float]):
        """Show save performance breakdown"""
        total_time = timing_info.get('total', 0)
        
        if total_time > 8:
            st.sidebar.error(f"🔴 Very slow save: {total_time:.1f}s")
        elif total_time > 4:
            st.sidebar.warning(f"🟡 Slow save: {total_time:.1f}s")
        else:
            st.sidebar.success(f"🟢 Save: {total_time:.1f}s")
        
        # Detailed breakdown for slow saves
        if total_time > 3:
            with st.sidebar.expander("📊 Save Performance Breakdown"):
                for step, duration in timing_info.items():
                    if step != 'total':
                        percentage = (duration / total_time) * 100
                        st.write(f"**{step.title()}:** {duration:.2f}s ({percentage:.0f}%)")

class TransactionOptimizer:
    """Optimize transaction processing for better performance"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
        self.async_save_manager = AsyncSaveManager(fund_manager)
    
    def process_transaction_optimized(self, transaction_type: str, **kwargs) -> tuple[bool, str]:
        """Process transaction with optimized save"""
        try:
            # Process the transaction using existing methods
            if transaction_type == 'deposit':
                success, message = self.fund_manager.process_deposit(**kwargs)
            elif transaction_type == 'withdrawal':
                success, message = self.fund_manager.process_withdrawal(**kwargs)
            elif transaction_type == 'nav_update':
                success, message = self.fund_manager.process_nav_update(**kwargs)
            else:
                return False, f"Unknown transaction type: {transaction_type}"
            
            if success:
                # Mark data as changed but don't save immediately
                st.session_state.data_changed = True
                
                # Show immediate success feedback
                st.success(f"✅ {message}")
                
                # Auto-save in background (optional)
                if st.checkbox("🔄 Auto-save after transaction", value=True):
                    with st.spinner("💾 Auto-saving..."):
                        save_success = self.async_save_manager.save_with_progress()
                        if save_success:
                            st.toast("💾 Data saved automatically!", icon="✅")
                        else:
                            st.warning("⚠️ Auto-save failed. Please save manually.")
                
                return True, message
            else:
                return False, message
                
        except Exception as e:
            return False, f"Transaction processing failed: {str(e)}"

# === INTEGRATION FUNCTIONS ===

def enhance_save_operations(fund_manager):
    """Enhance save operations for existing app"""
    
    def optimized_save_data():
        """Replace the standard save_data method"""
        save_optimizer = SaveOptimizer(fund_manager)
        success, message, timing_info = save_optimizer.optimized_save_all()
        
        # Show performance feedback
        if timing_info:
            total_time = timing_info.get('total', 0)
            if total_time > 5:
                st.sidebar.error(f"🔴 Save: {total_time:.1f}s")
                
                # Show breakdown for slow saves
                with st.sidebar.expander("📊 Save Breakdown"):
                    for step, duration in timing_info.items():
                        if step != 'total':
                            st.write(f"{step}: {duration:.2f}s")
            else:
                st.sidebar.success(f"🟢 Save: {total_time:.1f}s")
        
        return success
    
    # Replace the save method
    fund_manager.optimized_save_data = optimized_save_data
    return fund_manager

def smart_save_handler(fund_manager):
    """Smart save handler with user options"""
    
    if not st.session_state.get('data_changed', False):
        return
    
    # Show save options
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Save Options")
    
    save_mode = st.sidebar.radio(
        "Save Mode",
        ["🚀 Fast Save", "📊 Detailed Save", "🔧 Manual Control"],
        key="save_mode"
    )
    
    if save_mode == "🚀 Fast Save":
        # Automatic fast save
        save_optimizer = SaveOptimizer(fund_manager)
        success, message, timing = save_optimizer.optimized_save_all()
        
        if success:
            st.sidebar.success(f"✅ {message}")
        else:
            st.sidebar.error(f"❌ {message}")
    
    elif save_mode == "📊 Detailed Save":
        # Save with progress and detailed feedback
        if st.sidebar.button("💾 Save with Progress", width="stretch"):
            async_save_manager = AsyncSaveManager(fund_manager)
            success = async_save_manager.save_with_progress()
            
            if success:
                st.sidebar.success("✅ Detailed save completed")
            else:
                st.sidebar.error("❌ Detailed save failed")
    
    elif save_mode == "🔧 Manual Control":
        # Manual save control
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("⚡ Quick", width="stretch"):
                success = fund_manager.save_data()
                if success:
                    st.sidebar.success("✅ Quick save")
                else:
                    st.sidebar.error("❌ Quick save failed")
        
        with col2:
            if st.button("🔍 Validate", width="stretch"):
                validation = fund_manager.validate_data_consistency()
                if validation['valid']:
                    st.sidebar.success("✅ Data valid")
                else:
                    st.sidebar.error("❌ Data invalid")

# === DATABASE CONNECTION OPTIMIZATION ===

def optimize_database_connection(data_handler):
    """Optimize database connection for better save performance"""
    
    if not hasattr(data_handler, 'engine') or not data_handler.engine:
        # For CSV handler, no database optimization needed
        if hasattr(data_handler, '__class__') and 'CSV' in data_handler.__class__.__name__:
            st.sidebar.info("📁 CSV Storage - No database optimization needed")
        return False
    
    try:
        # Check current connection pool settings
        current_pool_size = getattr(data_handler.engine.pool, 'size', lambda: 5)()
        current_max_overflow = getattr(data_handler.engine.pool, 'max_overflow', lambda: 10)()
        
        st.sidebar.info(f"🔗 DB Pool: {current_pool_size} + {current_max_overflow} overflow")
        
        # Show connection health
        try:
            from sqlalchemy import text
            start_time = time.time()
            with data_handler.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            ping_time = time.time() - start_time
            
            if ping_time > 1.0:
                st.sidebar.error(f"🔴 DB ping: {ping_time:.2f}s")
            elif ping_time > 0.5:
                st.sidebar.warning(f"🟡 DB ping: {ping_time:.2f}s")
            else:
                st.sidebar.success(f"🟢 DB ping: {ping_time:.2f}s")
                
        except Exception as e:
            st.sidebar.error(f"🔴 DB ping failed: {str(e)[:30]}")
        
        return True
        
    except Exception as e:
        st.sidebar.warning(f"⚠️ DB optimization unavailable: {str(e)[:30]}")
        return False