# app.py

import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime, date # Bạn có thể thêm date nếu chưa có

# --- THIẾT LẬP CƠ BẢN ---
from config import PAGE_CONFIG
from services_enhanced import EnhancedFundManager
from supabase_data_handler import SupabaseDataHandler # Import trực tiếp
from google_drive_manager import GoogleDriveManager

# --- IMPORT CÁC MODULE ĐÃ TÁI CẤU TRÚC ---
from styles import apply_global_styles
from sidebar_manager import SidebarManager
from data_utils import ErrorHandler

# --- IMPORT CÁC TRANG (PAGES) ---
# Add pages directory to path for dynamic importing
sys.path.append(str(Path(__file__).parent / "pages"))
from investor_page import InvestorPage
from transaction_page import TransactionPage
from fee_page_enhanced import EnhancedFeePage
from report_page_enhanced import EnhancedReportPage



# --- CÀI ĐẶT TRANG VÀ CSS ---
st.set_page_config(**PAGE_CONFIG)
apply_global_styles()  # Áp dụng tất cả CSS và JS từ file styles.py

# --- LOGIC BẢO MẬT ---
try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except (KeyError, FileNotFoundError, AttributeError):
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1997") # Mật khẩu mặc định

# === NGUỒN CHÂN LÝ DUY NHẤT CHO CÁC TRANG ===
# Định nghĩa tên các trang ở một nơi duy nhất để đảm bảo nhất quán
PAGE_ADD_INVESTOR = "👥 Thêm Nhà Đầu Tư"
PAGE_EDIT_INVESTOR = "✏️ Sửa Thông Tin NĐT"
PAGE_ADD_TRANSACTION = "💸 Thêm Giao Dịch"
PAGE_ADD_NAV = "📈 Thêm Total NAV"
PAGE_FM_WITHDRAWAL = "🛒 Fund Manager Withdrawal"
PAGE_MANAGE_TRANSACTIONS = "🔧 Quản Lý Giao Dịch"
PAGE_CALCULATE_FEES = "🧮 Tính Toán Phí"
PAGE_CALCULATE_INDIVIDUAL_FEE = "🔍 Tính Phí Riêng"
PAGE_REPORTS = "📊 Báo Cáo & Thống Kê"
PAGE_LIFETIME_PERFORMANCE = "📈 Lifetime Performance"
PAGE_FEE_HISTORY = "💰 Lịch Sử Phí"

# Danh sách tất cả các trang cho sidebar
ALL_PAGES = [
    PAGE_REPORTS, PAGE_LIFETIME_PERFORMANCE, PAGE_FEE_HISTORY,
    PAGE_ADD_INVESTOR, PAGE_EDIT_INVESTOR, PAGE_ADD_TRANSACTION,
    PAGE_ADD_NAV, PAGE_FM_WITHDRAWAL, PAGE_MANAGE_TRANSACTIONS,
    PAGE_CALCULATE_FEES, PAGE_CALCULATE_INDIVIDUAL_FEE,
]

# Danh sách các trang yêu cầu đăng nhập để chỉnh sửa
EDIT_PAGES = [
    PAGE_ADD_INVESTOR, PAGE_EDIT_INVESTOR, PAGE_ADD_TRANSACTION,
    PAGE_ADD_NAV, PAGE_FM_WITHDRAWAL, PAGE_MANAGE_TRANSACTIONS,
    PAGE_CALCULATE_FEES,
]
# === KẾT THÚC ĐỊNH NGHĨA ===


class EnhancedFundManagementApp:
    def __init__(self):
        # **SỬA LỖI QUAN TRỌNG: Khởi tạo các thành phần theo đúng thứ tự**
        if 'fund_manager' not in st.session_state:
            with st.spinner("🚀 Khởi động và tải dữ liệu từ database... Vui lòng chờ trong giây lát."):
                print(f"[{datetime.now()}] --- Initializing services for the first time...")
                
                # 1. Tạo data_handler trước
                data_handler = SupabaseDataHandler()
                
                # 2. Kiểm tra kết nối
                if not data_handler.connected:
                    st.error("Không thể kết nối tới Database. Vui lòng kiểm tra lại cấu hình.")
                    st.stop() # Dừng ứng dụng nếu không có kết nối

                # 3. Truyền data_handler vào EnhancedFundManager
                st.session_state.fund_manager = EnhancedFundManager(data_handler)

                # 4. (Tùy chọn) Lưu luôn data_handler vào session nếu cần dùng riêng
                st.session_state.data_handler = data_handler
        
        self.fund_manager = st.session_state.fund_manager
        self.data_handler = self.fund_manager.data_handler # Lấy data_handler từ fund_manager

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
        """Render nội dung chính, sử dụng page map đã được sửa lỗi."""
        if page in EDIT_PAGES and not st.session_state.logged_in:
            self.render_login_form()
            return

        with ErrorHandler(f"tải trang '{page}'"):
            # Ánh xạ từ tên trang (đã định nghĩa ở trên) sang hàm render tương ứng
            page_map = {
                PAGE_ADD_INVESTOR: lambda: InvestorPage(self.fund_manager).render_add_form(),
                PAGE_EDIT_INVESTOR: lambda: InvestorPage(self.fund_manager).render_edit_page(),
                PAGE_ADD_TRANSACTION: lambda: TransactionPage(self.fund_manager).render_transaction_form(),
                PAGE_ADD_NAV: lambda: TransactionPage(self.fund_manager).render_nav_update(),
                PAGE_FM_WITHDRAWAL: lambda: TransactionPage(self.fund_manager).render_fund_manager_withdrawal(),
                PAGE_MANAGE_TRANSACTIONS: lambda: TransactionPage(self.fund_manager).render_transaction_management(),
                PAGE_CALCULATE_FEES: lambda: EnhancedFeePage(self.fund_manager).render_enhanced_fee_calculation(),
                PAGE_CALCULATE_INDIVIDUAL_FEE: lambda: EnhancedFeePage(self.fund_manager).render_individual_fee(),
                PAGE_REPORTS: lambda: EnhancedReportPage(self.fund_manager).render_reports(),
                PAGE_LIFETIME_PERFORMANCE: lambda: EnhancedReportPage(self.fund_manager).render_lifetime_performance(),
                PAGE_FEE_HISTORY: lambda: EnhancedReportPage(self.fund_manager).render_fee_history(),
            }
            render_function = page_map.get(page)
            if render_function:
                render_function()
            else:
                st.warning(f"Trang '{page}' chưa được triển khai.")

    def handle_save(self):
        if st.session_state.get('data_changed', False):
            with ErrorHandler("lưu dữ liệu"):
                if self.fund_manager.save_data():
                    st.session_state.data_changed = False
                    
                    # Xóa các đối tượng cũ khỏi session để buộc tải lại dữ liệu mới
                    keys_to_delete = ['fund_manager', 'data_handler', 'gdrive_manager']
                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.toast("✅ Đã lưu dữ liệu! Đang tải lại...", icon="💾")
                    st.rerun()

    def run(self):
        """Chạy vòng lặp chính của ứng dụng với các đối tượng đã được khởi tạo."""
        with ErrorHandler("khởi chạy ứng dụng"):
            # Sử dụng gdrive_manager đã được lưu trong self
            if self.gdrive_manager:
                self.gdrive_manager.schedule_monthly_export()
            
            selected_page = self.sidebar_manager.render()
            self.render_main_content(selected_page)
            self.handle_save()


# --- ĐIỂM KHỞI ĐỘNG ---
if __name__ == "__main__":
    app = EnhancedFundManagementApp()
    app.run()