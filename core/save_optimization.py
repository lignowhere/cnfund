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
                return False, "Kiểm tra dữ liệu nhanh thất bại", timing_info
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
            
            message = f"Lưu hoàn tất trong {total_time:.1f}s"
            if total_time > 5:
                message += " (chậm hơn kỳ vọng)"
            
            return success, message, timing_info
            
        except Exception as e:
            total_time = time.time() - start_time
            timing_info['total'] = total_time
            return False, f"Lưu thất bại sau {total_time:.1f}s: {str(e)}", timing_info
    
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
            st.error(f"Lưu theo lô thất bại: {str(e)}")
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
            status_text.text("🔍 Đang kiểm tra dữ liệu...")
            progress_bar.progress(20)
            
            if not self.save_optimizer._quick_data_check():
                status_text.error("❌ Kiểm tra dữ liệu thất bại")
                return False
            
            # Step 2: Preparation
            status_text.text("📋 Đang chuẩn bị dữ liệu...")
            progress_bar.progress(40)
            time.sleep(0.1)  # Small delay for UI feedback
            
            # Step 3: Save execution
            status_text.text("💾 Đang lưu vào cơ sở dữ liệu...")
            progress_bar.progress(60)
            
            success, message, timing_info = self.save_optimizer.optimized_save_all()
            
            progress_bar.progress(90)
            
            if success:
                # Step 4: Finalization
                status_text.text("✅ Đang hoàn tất...")
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
            status_text.error(f"❌ Lỗi lưu: {str(e)}")
            return False
    
    def _show_save_performance(self, timing_info: Dict[str, float]):
        """Show save performance breakdown"""
        total_time = timing_info.get('total', 0)
        
        if total_time > 8:
            st.sidebar.error(f"🔴 Lưu rất chậm: {total_time:.1f}s")
        elif total_time > 4:
            st.sidebar.warning(f"🟡 Lưu chậm: {total_time:.1f}s")
        else:
            st.sidebar.success(f"🟢 Lưu: {total_time:.1f}s")
        
        # Detailed breakdown for slow saves
        if total_time > 3:
            with st.sidebar.expander("📊 Phân Rã Hiệu Suất Lưu"):
                step_labels = {
                    'validation': 'Kiểm tra dữ liệu',
                    'preparation': 'Chuẩn bị dữ liệu',
                    'save_execution': 'Thực thi lưu',
                    'cleanup': 'Dọn dẹp sau lưu'
                }
                for step, duration in timing_info.items():
                    if step != 'total':
                        percentage = (duration / total_time) * 100
                        label = step_labels.get(step, step)
                        st.write(f"**{label}:** {duration:.2f}s ({percentage:.0f}%)")

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
                return False, f"Loại giao dịch không xác định: {transaction_type}"
            
            if success:
                # Mark data as changed but don't save immediately
                st.session_state.data_changed = True
                
                # Show immediate success feedback
                st.success(f"✅ {message}")
                
                # Auto-save in background (optional)
                if st.checkbox("🔄 Tự động lưu sau giao dịch", value=True):
                    with st.spinner("💾 Đang tự động lưu..."):
                        save_success = self.async_save_manager.save_with_progress()
                        if save_success:
                            st.toast("💾 Dữ liệu đã được tự động lưu!", icon="✅")
                        else:
                            st.warning("⚠️ Tự động lưu thất bại. Vui lòng lưu thủ công.")
                
                return True, message
            else:
                return False, message
                
        except Exception as e:
            return False, f"Xử lý giao dịch thất bại: {str(e)}"

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
                st.sidebar.error(f"🔴 Lưu: {total_time:.1f}s")
                
                # Show breakdown for slow saves
                with st.sidebar.expander("📊 Phân Rã Tác Vụ Lưu"):
                    step_labels = {
                        'validation': 'Kiểm tra dữ liệu',
                        'preparation': 'Chuẩn bị dữ liệu',
                        'save_execution': 'Thực thi lưu',
                        'cleanup': 'Dọn dẹp sau lưu'
                    }
                    for step, duration in timing_info.items():
                        if step != 'total':
                            st.write(f"{step_labels.get(step, step)}: {duration:.2f}s")
            else:
                st.sidebar.success(f"🟢 Lưu: {total_time:.1f}s")
        
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
    st.sidebar.subheader("💾 Tùy Chọn Lưu")
    
    save_mode = st.sidebar.radio(
        "Chế độ lưu",
        ["🚀 Lưu nhanh", "📊 Lưu chi tiết", "🔧 Điều khiển thủ công"],
        key="save_mode"
    )
    
    if save_mode == "🚀 Lưu nhanh":
        # Automatic fast save
        save_optimizer = SaveOptimizer(fund_manager)
        success, message, timing = save_optimizer.optimized_save_all()
        
        if success:
            st.sidebar.success(f"✅ {message}")
        else:
            st.sidebar.error(f"❌ {message}")
    
    elif save_mode == "📊 Lưu chi tiết":
        # Save with progress and detailed feedback
        if st.sidebar.button("💾 Lưu Kèm Tiến Trình", width="stretch"):
            async_save_manager = AsyncSaveManager(fund_manager)
            success = async_save_manager.save_with_progress()
            
            if success:
                st.sidebar.success("✅ Lưu chi tiết hoàn tất")
            else:
                st.sidebar.error("❌ Lưu chi tiết thất bại")
    
    elif save_mode == "🔧 Điều khiển thủ công":
        # Manual save control
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("⚡ Nhanh", width="stretch"):
                success = fund_manager.save_data()
                if success:
                    st.sidebar.success("✅ Lưu nhanh thành công")
                else:
                    st.sidebar.error("❌ Lưu nhanh thất bại")
        
        with col2:
            if st.button("🔍 Kiểm tra", width="stretch"):
                validation = fund_manager.validate_data_consistency()
                if validation['valid']:
                    st.sidebar.success("✅ Dữ liệu hợp lệ")
                else:
                    st.sidebar.error("❌ Dữ liệu không hợp lệ")

# === DATABASE CONNECTION OPTIMIZATION ===

def optimize_database_connection(data_handler):
    """Optimize database connection for better save performance"""
    
    if not hasattr(data_handler, 'engine') or not data_handler.engine:
        # For CSV handler, no database optimization needed
        if hasattr(data_handler, '__class__') and 'CSV' in data_handler.__class__.__name__:
            st.sidebar.info("📁 Lưu trữ CSV - Không cần tối ưu cơ sở dữ liệu")
        return False
    
    try:
        # Check current connection pool settings
        current_pool_size = getattr(data_handler.engine.pool, 'size', lambda: 5)()
        current_max_overflow = getattr(data_handler.engine.pool, 'max_overflow', lambda: 10)()
        
        st.sidebar.info(f"🔗 Pool DB: {current_pool_size} + {current_max_overflow} tràn")
        
        # Show connection health
        try:
            from sqlalchemy import text
            start_time = time.time()
            with data_handler.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            ping_time = time.time() - start_time
            
            if ping_time > 1.0:
                st.sidebar.error(f"🔴 Ping DB: {ping_time:.2f}s")
            elif ping_time > 0.5:
                st.sidebar.warning(f"🟡 Ping DB: {ping_time:.2f}s")
            else:
                st.sidebar.success(f"🟢 Ping DB: {ping_time:.2f}s")
                
        except Exception as e:
            st.sidebar.error(f"🔴 Ping DB thất bại: {str(e)[:30]}")
        
        return True
        
    except Exception as e:
        st.sidebar.warning(f"⚠️ Tối ưu DB không khả dụng: {str(e)[:30]}")
        return False
