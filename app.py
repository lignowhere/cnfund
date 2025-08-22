# app.py - Enhanced Version

import streamlit as st
import os
import sys
import time
from pathlib import Path
from datetime import datetime, date

# --- THIẾT LẬP CƠ BẢN ---
from config import PAGE_CONFIG
from services_enhanced import EnhancedFundManager
from supabase_data_handler import SupabaseDataHandler
from google_drive_manager import GoogleDriveManager

# --- IMPORT CÁC MODULE ĐÃ TÁI CẤU TRÚC ---
from styles import apply_global_styles
from sidebar_manager import SidebarManager
from data_utils import ErrorHandler

# --- IMPORT CÁC TRANG ENHANCED ---
sys.path.append(str(Path(__file__).parent / "pages"))
from pages.investor_page import InvestorPage
from pages.transaction_page import EnhancedTransactionPage  
from pages.fee_page_enhanced import SafeFeePage  
from pages.report_page_enhanced import EnhancedReportPage

# --- CÀI ĐẶT TRANG VÀ CSS ---
st.set_page_config(**PAGE_CONFIG)
apply_global_styles()

# --- LOGIC BẢO MẬT ---
try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except (KeyError, FileNotFoundError, AttributeError):
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1997")

# === NGUỒN CHÂN LÝ DUY NHẤT CHO CÁC TRANG ===
PAGE_ADD_INVESTOR = "👥 Thêm Nhà Đầu Tư"
PAGE_EDIT_INVESTOR = "✏️ Sửa Thông Tin NĐT"
PAGE_ADD_TRANSACTION = "💸 Thêm Giao Dịch"
PAGE_ADD_NAV = "📈 Thêm Total NAV"
PAGE_FM_WITHDRAWAL = "🛒 Fund Manager Withdrawal"
PAGE_MANAGE_TRANSACTIONS = "🔧 Quản Lý Giao Dịch"
PAGE_CALCULATE_FEES = "🧮 Tính Toán Phí"
PAGE_CALCULATE_INDIVIDUAL_FEE = "📋 Tính Phí Riêng"
PAGE_REPORTS = "📊 Báo Cáo & Thống Kê"
# PAGE_STRESS_TEST = "🧪 Stress Test System"  # NEW PAGE

# Danh sách tất cả các trang cho sidebar
ALL_PAGES = [
    PAGE_REPORTS, PAGE_ADD_INVESTOR, PAGE_EDIT_INVESTOR, 
    PAGE_ADD_TRANSACTION, PAGE_ADD_NAV, PAGE_FM_WITHDRAWAL, 
    PAGE_MANAGE_TRANSACTIONS, PAGE_CALCULATE_FEES, 
    PAGE_CALCULATE_INDIVIDUAL_FEE, #PAGE_STRESS_TEST
]

# Danh sách các trang yêu cầu đăng nhập để chỉnh sửa
EDIT_PAGES = [
    PAGE_ADD_INVESTOR, PAGE_EDIT_INVESTOR, PAGE_ADD_TRANSACTION,
    PAGE_ADD_NAV, PAGE_FM_WITHDRAWAL, PAGE_MANAGE_TRANSACTIONS,
    PAGE_CALCULATE_FEES, #PAGE_STRESS_TEST
]


class EnhancedFundManagementApp:
    def __init__(self):
        # Khởi tạo các thành phần theo đúng thứ tự
        if 'fund_manager' not in st.session_state:
            with st.spinner("🚀 Khởi động và tải dữ liệu từ database... Vui lòng chờ trong giây lát."):
                print(f"[{datetime.now()}] --- Initializing enhanced services for the first time...")
                
                # 1. Tạo data_handler trước
                data_handler = SupabaseDataHandler()
                
                # 2. Kiểm tra kết nối
                if not data_handler.connected:
                    st.error("Không thể kết nối tới Database. Vui lòng kiểm tra lại cấu hình.")
                    st.stop()

                # 3. Truyền data_handler vào EnhancedFundManager
                st.session_state.fund_manager = EnhancedFundManager(data_handler)
                st.session_state.data_handler = data_handler
        
        self.fund_manager = st.session_state.fund_manager
        self.data_handler = self.fund_manager.data_handler

        # Khởi tạo GoogleDriveManager (chỉ chạy 1 lần)
        if 'gdrive_manager' not in st.session_state:
            st.session_state.gdrive_manager = GoogleDriveManager(self.fund_manager)
        self.gdrive_manager = st.session_state.gdrive_manager

        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        
        self.sidebar_manager = SidebarManager(
            self.fund_manager,
            self.data_handler,
            menu_options=ALL_PAGES
        )

    def render_login_form(self):
        """Render form đăng nhập với giao diện cải tiến."""
        st.markdown("""
            <div style='max-width: 400px; margin: 2rem auto; padding: 2rem;
                        background: white; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                <h3 style='text-align: center; color: #2c3e50; margin-bottom: 1.5rem;'>
                    🔐 Yêu cầu đăng nhập để chỉnh sửa
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            password = st.text_input(
                "Mật khẩu",
                type="password",
                placeholder="Nhập mật khẩu admin...",
                label_visibility="collapsed"
            )
            if st.button("🚀 Đăng nhập", use_container_width=True, type="primary"):
                if password == ADMIN_PASSWORD:
                    st.session_state.logged_in = True
                    st.success("✅ Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("❌ Mật khẩu không chính xác.")

    def render_main_content(self, page: str):
        """Render nội dung chính với enhanced pages"""
        if page in EDIT_PAGES and not st.session_state.logged_in:
            self.render_login_form()
            return

        with ErrorHandler(f"tải trang '{page}'"):
            # Enhanced page mapping
            page_map = {
                PAGE_ADD_INVESTOR: lambda: InvestorPage(self.fund_manager).render_add_form(),
                PAGE_EDIT_INVESTOR: lambda: InvestorPage(self.fund_manager).render_edit_page(),
                PAGE_ADD_TRANSACTION: lambda: EnhancedTransactionPage(self.fund_manager).render_transaction_form(),
                PAGE_ADD_NAV: lambda: EnhancedTransactionPage(self.fund_manager).render_nav_update(),
                PAGE_FM_WITHDRAWAL: lambda: EnhancedTransactionPage(self.fund_manager).render_fund_manager_withdrawal(),
                PAGE_MANAGE_TRANSACTIONS: lambda: EnhancedTransactionPage(self.fund_manager).render_transaction_management(),
                PAGE_CALCULATE_FEES: lambda: SafeFeePage(self.fund_manager).render_enhanced_fee_calculation(),
                PAGE_CALCULATE_INDIVIDUAL_FEE: lambda: SafeFeePage(self.fund_manager).render_individual_fee(),
                PAGE_REPORTS: lambda: EnhancedReportPage(self.fund_manager).render_reports(),
                # PAGE_STRESS_TEST: lambda: self.render_stress_test_page(),
            }
            
            render_function = page_map.get(page)
            if render_function:
                render_function()
            else:
                st.warning(f"Trang '{page}' chưa được triển khai.")

    # def render_stress_test_page(self):
    #     """Render stress test page"""
    #     st.title("🧪 System Stress Test")
        
    #     st.info("""
    #     **Stress Test** kiểm tra hệ thống với dữ liệu lớn để đảm bảo:
    #     - Tính toán phí chính xác
    #     - Consistency của dữ liệu
    #     - Performance với nhiều investor & giao dịch
    #     - Validation logic
    #     """)
        
    #     # Import stress tester
    #     try:
    #         from fund_stress_test import FundStressTester
            
    #         # Scenario selection
    #         scenario_options = {
    #             'light': '🟢 Light (5 investors, 3 trans/investor, 2 fee periods)',
    #             'medium': '🟡 Medium (15 investors, 8 trans/investor, 3 fee periods)',
    #             'heavy': '🟠 Heavy (50 investors, 15 trans/investor, 5 fee periods)',
    #             'extreme': '🔴 Extreme (100 investors, 25 trans/investor, 7 fee periods)'
    #         }
            
    #         selected_display = st.selectbox(
    #             "📊 Chọn Scenario Test",
    #             list(scenario_options.values()),
    #             index=1  # Default to medium
    #         )
            
    #         # Get scenario key
    #         scenario = next(
    #             (key for key, value in scenario_options.items() if value == selected_display),
    #             'medium'
    #         )
            
    #         # Warning for heavy tests
    #         if scenario in ['heavy', 'extreme']:
    #             st.warning(f"⚠️ {scenario.upper()} test sẽ tạo rất nhiều dữ liệu test và có thể mất vài phút!")
            
    #         # Data preservation warning
    #         st.error("""
    #         🚨 **QUAN TRỌNG:** 
    #         - Test sẽ thêm nhiều investor & giao dịch test
    #         - Dữ liệu thật sẽ được bảo toàn
    #         - Sau test có thể xóa dữ liệu test nếu muốn
    #         """)
            
    #         # Confirmation
    #         confirmed = st.checkbox(f"✅ Tôi xác nhận chạy {scenario.upper()} stress test")
            
    #         col1, col2 = st.columns(2)
            
    #         # Run test button
    #         if col1.button("🚀 Chạy Stress Test", 
    #                       disabled=not confirmed, 
    #                       use_container_width=True, 
    #                       type="primary"):
                
    #             if not confirmed:
    #                 st.error("❌ Vui lòng xác nhận trước khi chạy test")
    #                 return
                
    #             # Create tester and run
    #             with st.spinner(f"🧪 Đang chạy {scenario.upper()} stress test..."):
    #                 tester = FundStressTester(self.fund_manager)
    #                 results = tester.run_comprehensive_test(scenario)
                
    #             # Display results
    #             if results.get('success', False):
    #                 st.success("✅ Stress test PASSED!")
    #                 st.balloons()
    #             else:
    #                 st.error("❌ Stress test FAILED!")
                
    #             # Show summary
    #             with st.expander("📋 Test Results Summary", expanded=True):
    #                 col_res1, col_res2, col_res3 = st.columns(3)
                    
    #                 col_res1.metric("Duration", f"{results.get('duration_seconds', 0):.1f}s")
                    
    #                 if 'data_stats' in results:
    #                     stats = results['data_stats']
    #                     col_res2.metric("Test Investors", stats.get('investors', {}).get('test_investors', 0))
    #                     col_res3.metric("Total Transactions", stats.get('transactions', {}).get('total', 0))
                
    #             # Detailed report
    #             report = tester.generate_test_report()
    #             st.text_area("📄 Detailed Report", report, height=400)
                
    #             # Export options
    #             st.markdown("### 📤 Export Results")
    #             export_col1, export_col2 = st.columns(2)
                
    #             with export_col1:
    #                 # Text report download
    #                 timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #                 report_filename = f"stress_test_report_{scenario}_{timestamp}.txt"
                    
    #                 st.download_button(
    #                     label="📄 Download Text Report",
    #                     data=report,
    #                     file_name=report_filename,
    #                     mime="text/plain",
    #                     use_container_width=True
    #                 )
                
    #             with export_col2:
    #                 # Excel report download
    #                 try:
    #                     excel_data = tester.export_test_results_to_excel()
    #                     if excel_data:
    #                         excel_filename = f"stress_test_results_{scenario}_{timestamp}.xlsx"
    #                         st.download_button(
    #                             label="📊 Download Excel Report",
    #                             data=excel_data,
    #                             file_name=excel_filename,
    #                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    #                             use_container_width=True
    #                         )
    #                 except Exception as e:
    #                     st.error(f"Excel export failed: {str(e)}")
                
    #             # Mark data as changed to trigger save
    #             st.session_state.data_changed = True
            
    #         # Clean up test data button
    #         if col2.button("🧹 Xóa Dữ Liệu Test", use_container_width=True):
    #             self._cleanup_test_data()
    #             st.success("✅ Đã xóa dữ liệu test")
    #             st.session_state.data_changed = True
    #             st.rerun()
        
    #     except ImportError:
    #         st.error("❌ Không thể import FundStressTester. Kiểm tra file fund_stress_test.py")
    #     except Exception as e:
    #         st.error(f"❌ Lỗi stress test: {str(e)}")
    
    # def _cleanup_test_data(self):
    #     """Enhanced cleanup with deadlock prevention"""
    #     try:
    #         # Get test investor IDs BEFORE any deletion
    #         test_investor_ids = {
    #             inv.id for inv in self.fund_manager.investors 
    #             if inv.name.startswith('Test_')
    #         }
            
    #         if not test_investor_ids:
    #             st.info("No test data found to clean up")
    #             return
            
    #         # Use small batches to avoid deadlocks
    #         batch_size = 10
    #         test_ids_list = list(test_investor_ids)
            
    #         for i in range(0, len(test_ids_list), batch_size):
    #             batch_ids = test_ids_list[i:i + batch_size]
                
    #             # Remove data in small batches
    #             self.fund_manager.investors = [
    #                 inv for inv in self.fund_manager.investors 
    #                 if inv.id not in batch_ids
    #             ]
                
    #             self.fund_manager.tranches = [
    #                 t for t in self.fund_manager.tranches 
    #                 if t.investor_id not in batch_ids
    #             ]
                
    #             self.fund_manager.transactions = [
    #                 t for t in self.fund_manager.transactions 
    #                 if t.investor_id not in batch_ids
    #             ]
                
    #             self.fund_manager.fee_records = [
    #                 f for f in self.fund_manager.fee_records 
    #                 if f.investor_id not in batch_ids
    #             ]
                
    #             # Save after each batch
    #             if not self.fund_manager.save_data():
    #                 st.error(f"Failed to save batch {i//batch_size + 1}")
    #                 return
                
    #             # Small delay between batches
    #             time.sleep(0.5)
            
    #         st.success(f"✅ Cleaned up {len(test_investor_ids)} test investors")
            
    #     except Exception as e:
    #         st.error(f"❌ Cleanup failed: {str(e)}")

    def handle_save(self):
        """Enhanced save handling with retry logic"""
        if st.session_state.get('data_changed', False):
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    # Validate before saving
                    validation_results = self.fund_manager.validate_data_consistency()
                    
                    if not validation_results['valid']:
                        st.error("❌ Dữ liệu không nhất quán! Không thể lưu.")
                        return
                    
                    # Try to save
                    if self.fund_manager.save_data():
                        st.session_state.data_changed = False
                        st.toast("✅ Đã lưu dữ liệu!", icon="💾")
                        st.rerun()
                        return
                    else:
                        raise Exception("Save operation returned False")
                        
                except Exception as e:
                    error_msg = str(e).lower()
                    is_deadlock = any(keyword in error_msg for keyword in [
                        'deadlock', 'lock timeout', 'could not obtain lock'
                    ])
                    
                    if is_deadlock and attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + random.uniform(0.1, 0.5)
                        st.warning(f"⚠️ Deadlock detected (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        st.error(f"❌ Lưu dữ liệu thất bại: {str(e)}")
                        return

    def run(self):
        """Chạy vòng lặp chính của ứng dụng enhanced"""
        with ErrorHandler("khởi chạy ứng dụng"):
            # Auto backup scheduling
            if self.gdrive_manager:
                self.gdrive_manager.schedule_monthly_export()
            
            # Enhanced data consistency check on startup
            if st.session_state.get('show_startup_validation', True):
                validation_results = self.fund_manager.validate_data_consistency()
                if not validation_results['valid']:
                    st.error("⚠️ Phát hiện vấn đề với dữ liệu!")
                    with st.expander("🔍 Chi tiết vấn đề", expanded=True):
                        for error in validation_results['errors']:
                            st.error(f"• {error}")
                    st.warning("🔧 Hãy kiểm tra và sửa các vấn đề trước khi tiếp tục.")
                
                # Only show once per session
                st.session_state.show_startup_validation = False
            
            selected_page = self.sidebar_manager.render()
            self.render_main_content(selected_page)
            self.handle_save()


# --- ĐIỂM KHỞI ĐỘNG ---
if __name__ == "__main__":
    app = EnhancedFundManagementApp()
    app.run()