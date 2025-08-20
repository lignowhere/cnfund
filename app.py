import streamlit as st
import os
from config import PAGE_CONFIG
from services import FundManager
from utils import format_currency
import sys
from pathlib import Path

# === SECURITY LOGIC (Di chuyển từ config.py để tránh import issues) ===
try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except (KeyError, FileNotFoundError, AttributeError):
    # Fallback cho local hoặc nếu secrets chưa set
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    if not ADMIN_PASSWORD:
        ADMIN_PASSWORD = "buffett123"  # Placeholder cho test; set env var hoặc secrets thực tế
        st.warning("Warning: Using default password. Set ADMIN_PASSWORD in Secrets or env var for security.")

# Add pages directory to path
sys.path.append(str(Path(__file__).parent / "pages"))

# Import pages
from investor_page import InvestorPage
from transaction_page import TransactionPage
from fee_page import FeePage
from report_page import ReportPage

# Set page config
st.set_page_config(**PAGE_CONFIG)

# CSS để ẩn file explorer và custom styling
st.markdown("""
<style>
    /* Ẩn Streamlit Cloud file explorer/navigation */
    .css-1d391kg, 
    .css-17eq0hr,
    .css-1y4p8pa,
    .css-12oz5g7,
    section[data-testid="stSidebarNav"],
    div[data-testid="stSidebarNav"],
    .css-163ttbj,
    ul[data-testid="stSidebarNavItems"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        overflow: hidden !important;
    }
    
    /* Điều chỉnh padding sidebar */
    .css-1lcbmhc {
        padding-top: 1rem;
    }
    
    /* Custom styling cho app */
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .positive-value {
        color: #00C851 !important;
        font-weight: bold;
    }
    
    .negative-value {
        color: #ff4444 !important;
        font-weight: bold;
    }
    
    /* Đảm bảo sidebar content hiển thị đúng */
    .css-1d391kg ~ div {
        display: block !important;
    }
</style>
""", unsafe_allow_html=True)

class FundManagementApp:
    """Main app class"""
    
    def __init__(self):
        if 'fund_manager' not in st.session_state:
            st.session_state.fund_manager = FundManager()
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False  # Default: chưa đăng nhập
        self.fund_manager = st.session_state.fund_manager
    
    def render_sidebar(self):
        """Render sidebar"""
        st.sidebar.title("🏦 Fund Management")
        
        # Latest NAV (luôn hiển thị)
        latest_nav = self.fund_manager.get_latest_total_nav()
        if latest_nav:
            st.sidebar.metric("💰 Total NAV", format_currency(latest_nav))
        else:
            st.sidebar.info("ℹ️ Quỹ chưa có NAV")
        
        # Navigation
        st.sidebar.markdown("---")
        page = st.sidebar.radio("📋 Menu", [
            "👥 Thêm Nhà Đầu Tư",
            "✏️ Sửa Thông Tin NĐT",
            "💸 Thêm Giao Dịch", 
            "📈 Thêm Total NAV",
            "🧮 Tính Toán Phí",
            "🔍 Tính Phí Riêng",
            "📊 Báo Cáo & Thống Kê"
        ])
        
        # Quick stats (luôn hiển thị)
        if self.fund_manager.investors:
            st.sidebar.markdown("---")
            st.sidebar.markdown("📊 **Thống Kê**")
            col1, col2 = st.sidebar.columns(2)
            col1.metric("Investors", len(self.fund_manager.investors))
            col2.metric("Tranches", len(self.fund_manager.tranches))
        
        # Logout button nếu đã đăng nhập
        if st.session_state.logged_in:
            if st.sidebar.button("🚪 Logout"):
                st.session_state.logged_in = False
                st.rerun()  # Refresh app
        
        return page
    
    def render_login_form(self):
        """Render form login"""
        with st.container():
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.subheader("🔒 Yêu cầu đăng nhập để chỉnh sửa")
            password = st.text_input("Mật khẩu", type="password")
            if st.button("Đăng nhập"):
                if password == ADMIN_PASSWORD:
                    st.session_state.logged_in = True
                    st.success("✅ Đăng nhập thành công!")
                    st.rerun()  # Refresh để hiển thị nội dung
                else:
                    st.error("❌ Mật khẩu sai")
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_main_content(self, page: str):
        """Render main content với kiểm tra bảo mật"""
        edit_pages = [
            "👥 Thêm Nhà Đầu Tư",
            "✏️ Sửa Thông Tin NĐT",
            "💸 Thêm Giao Dịch", 
            "📈 Thêm Total NAV",
            "🧮 Tính Toán Phí"
        ]
        
        if page in edit_pages and not st.session_state.logged_in:
            self.render_login_form()
            return  # Dừng render nội dung nếu chưa login
        
        # Render nội dung bình thường
        if page == "👥 Thêm Nhà Đầu Tư":
            investor_page = InvestorPage(self.fund_manager)
            investor_page.render_add_form()
            
        elif page == "✏️ Sửa Thông Tin NĐT":
            investor_page = InvestorPage(self.fund_manager)
            investor_page.render_edit_page()
            
        elif page == "💸 Thêm Giao Dịch":
            transaction_page = TransactionPage(self.fund_manager)
            transaction_page.render_transaction_form()
            
        elif page == "📈 Thêm Total NAV":
            transaction_page = TransactionPage(self.fund_manager)
            transaction_page.render_nav_update()
            
        elif page == "🧮 Tính Toán Phí":
            fee_page = FeePage(self.fund_manager)
            fee_page.render_fee_calculation()
            
        elif page == "🔍 Tính Phí Riêng":
            fee_page = FeePage(self.fund_manager)
            fee_page.render_individual_fee()
            
        elif page == "📊 Báo Cáo & Thống Kê":
            report_page = ReportPage(self.fund_manager)
            report_page.render_reports()
    
    def handle_save(self):
        """Handle saving data (chỉ nếu logged_in cho edit)"""
        if st.session_state.get('data_changed', False):
            if self.fund_manager.save_data():
                st.session_state.data_changed = False
                st.success("✅ Đã lưu dữ liệu")
    
    def run(self):
        """Run app"""
        try:
            selected_page = self.render_sidebar()
            self.render_main_content(selected_page)
            self.handle_save()
        except Exception as e:
            st.error(f"Lỗi ứng dụng: {str(e)}")

# Main entry point
if __name__ == "__main__":
    app = FundManagementApp()
    app.run()