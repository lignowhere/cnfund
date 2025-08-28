# app.py - Clean Optimized Version - No Loading Screen, Pure Performance

import streamlit as st
import os
import sys
import time
from pathlib import Path
from datetime import datetime, date



# === PURE LAZY LOADING - NO BLOAT ===
@st.cache_resource
def load_config():
    """Load config once and cache"""
    from config import PAGE_CONFIG
    return PAGE_CONFIG

@st.cache_resource  
def load_data_handler():
    """Load and cache data handler"""
    try:
        from supabase_data_handler import SupabaseDataHandler
        data_handler = SupabaseDataHandler()
        
        # Kiểm tra kết nối ngay lập tức
        if not hasattr(data_handler, 'connected') or not data_handler.connected:
            st.error("❌ Không thể kết nối tới Database")
            return None   
        return data_handler
    except Exception as e:
        st.error(f"❌ Lỗi khởi tạo Data Handler: {str(e)}")
        # Fallback to CSV (nếu cần, thêm code từ services_enhanced.py cũ)
        st.sidebar.warning("📄 Fallback to CSV storage")
        from data_handler import EnhancedDataHandler
        return EnhancedDataHandler()

@st.cache_resource
def load_fund_manager_class():
    """Load fund manager class"""
    try:
        from services_enhanced import EnhancedFundManager
        return EnhancedFundManager
    except Exception:
        from services import FundManager
        return FundManager

@st.cache_resource
def load_styles():
    """Load styles"""
    from styles import apply_global_styles
    from mobile_styles_addon import apply_complete_mobile_styles
    apply_global_styles()
    apply_complete_mobile_styles()
    return True

# === OPTIMIZATIONS LOADER ===
def load_optimizations():
    """Load all optimizations and return what's available"""
    optimizations = {
        'save_optimization': None,
        'database_optimization': None,
        'realtime_sync': None
    }
    
    try:
        from save_optimization import enhance_save_operations
        optimizations['save_optimization'] = enhance_save_operations
    except ImportError:
        pass
        
    try:
        from database_save_optimization import apply_database_save_optimization
        optimizations['database_optimization'] = apply_database_save_optimization
    except ImportError:
        pass
        
    try:
        from realtime_sync_fix import TransactionHandler
        optimizations['realtime_sync'] = TransactionHandler
    except ImportError:
        pass
    
    return optimizations

# === PAGE COMPONENTS LOADER ===
def load_page_components():
    """Load all page components"""
    sys.path.append(str(Path(__file__).parent / "pages"))
    
    pages = {}
    
    page_imports = [
        ('investor', 'pages.investor_page', 'InvestorPage'),
        ('transaction', 'pages.transaction_page', 'EnhancedTransactionPage'),
        ('fee', 'pages.fee_page_enhanced', 'SafeFeePage'),
        ('report', 'pages.report_page_enhanced', 'EnhancedReportPage')
    ]
    
    for key, module, class_name in page_imports:
        try:
            module_obj = __import__(module, fromlist=[class_name])
            pages[key] = getattr(module_obj, class_name)
        except Exception:
            pages[key] = None
    
    return pages

# === CACHED DATA FUNCTIONS ===
@st.cache_data(ttl=300)
def get_cached_nav(fund_manager_id):
    """Get cached NAV data"""
    fund_manager = st.session_state.get('fund_manager')
    if fund_manager:
        return fund_manager.get_latest_total_nav()
    return None

@st.cache_data(ttl=180)
def get_cached_investors(fund_manager_id):
    """Get cached investors data"""
    fund_manager = st.session_state.get('fund_manager')
    if fund_manager:
        return fund_manager.get_regular_investors()
    return []

def clear_app_cache():
    """Clear application caches"""
    get_cached_nav.clear()
    get_cached_investors.clear()

# === PAGE CONSTANTS ===
PAGE_ADD_INVESTOR = "👥 Thêm Nhà Đầu Tư"
PAGE_EDIT_INVESTOR = "✏️ Sửa Thông Tin NĐT"
PAGE_ADD_TRANSACTION = "💸 Thêm Giao Dịch"
PAGE_ADD_NAV = "📈 Thêm Total NAV"
PAGE_FM_WITHDRAWAL = "🛠 FM Withdrawal"
PAGE_MANAGE_TRANSACTIONS = "🔧 Quản Lý Giao Dịch"
PAGE_CALCULATE_FEES = "🧮 Tính Toán Phí"
PAGE_CALCULATE_INDIVIDUAL_FEE = "📋 Tính Phí Riêng"
PAGE_REPORTS = "📊 Báo Cáo & Thống Kê"

ALL_PAGES = [
    PAGE_REPORTS, PAGE_ADD_INVESTOR, PAGE_EDIT_INVESTOR, 
    PAGE_ADD_TRANSACTION, PAGE_ADD_NAV, PAGE_FM_WITHDRAWAL, 
    PAGE_MANAGE_TRANSACTIONS, PAGE_CALCULATE_FEES, 
    PAGE_CALCULATE_INDIVIDUAL_FEE
]

EDIT_PAGES = [
    PAGE_ADD_INVESTOR, PAGE_EDIT_INVESTOR, PAGE_ADD_TRANSACTION,
    PAGE_ADD_NAV, PAGE_FM_WITHDRAWAL, PAGE_MANAGE_TRANSACTIONS,
    PAGE_CALCULATE_FEES
]

# === MAIN APPLICATION CLASS ===
class FundManagementApp:
    """Clean, optimized Fund Management Application"""
    
    def __init__(self):
        self.initialize_session_state()
        self.setup_app()
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'app_start_time' not in st.session_state:
            st.session_state.app_start_time = time.time()
        
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        
        if 'menu_selection' not in st.session_state:
            st.session_state.menu_selection = PAGE_REPORTS
            
        if 'show_startup_validation' not in st.session_state:
            st.session_state.show_startup_validation = True
    
    def setup_app(self):
        """Setup application with optimized loading"""
        # Load configuration and set page config
        page_config = load_config()
        try:
            st.set_page_config(**page_config)
        except Exception:
            pass  # Page config already set
        
        # Load styles
        load_styles()
        
        # Initialize or load from cache
        if self.should_reinitialize():
            self.initialize_components()
        else:
            self.load_from_session()
    
    def should_reinitialize(self) -> bool:
        """Check if we need to reinitialize components"""
        required_keys = ['fund_manager', 'data_handler', 'sidebar_manager', 'pages']
        
        # Check if all required components exist
        if not all(key in st.session_state for key in required_keys):
            return True
        
        # Check if components are still valid
        try:
            fund_manager = st.session_state.get('fund_manager')
            data_handler = st.session_state.get('data_handler')
            
            if not fund_manager or not data_handler:
                return True
                
            if hasattr(data_handler, 'connected') and not data_handler.connected:
                return True
            
            # Check if last initialization was too long ago (optional)
            last_init = st.session_state.get('last_init', 0)
            if time.time() - last_init > 3600:  # 1 hour
                return True
                
        except Exception as e:
            st.warning(f"⚠️ Lỗi kiểm tra component: {str(e)}")
            return True
        
        return False
    
    def initialize_components(self):
        """Initialize all components with simple loading screen"""
        try:
            progress = st.progress(0)
            status = st.empty()

            # Step 1: Data handler
            status.info("🔌 Connecting to database...")
            self.data_handler = load_data_handler()
            if not self.data_handler or not getattr(self.data_handler, "connected", False):
                st.error("❌ Không thể kết nối Database. Vui lòng kiểm tra cấu hình.")
                self.render_error_recovery()
                st.stop()
            progress.progress(25)

            # Step 2: Fund manager
            status.info("📦 Loading fund manager...")
            FundManagerClass = load_fund_manager_class()
            self.fund_manager = FundManagerClass(self.data_handler)

            # ++++++ THÊM 2 DÒNG QUAN TRỌNG NÀY ++++++
            status.info("📂 Loading data from database...")
            self.fund_manager.load_data()  # Chủ động tải dữ liệu
            self.fund_manager._ensure_fund_manager_exists() # Đảm bảo có Fund Manager
            # +++++++++++++++++++++++++++++++++++++++

            progress.progress(50)

            # Step 3: Optimizations
            status.info("⚡ Applying optimizations...")
            optimizations = load_optimizations()
            self.apply_optimizations(optimizations)
            progress.progress(65)

            # Step 4: Load pages
            status.info("📑 Loading pages...")
            self.pages = load_page_components()
            progress.progress(80)

            # Step 5: Sidebar
            status.info("🧭 Initializing sidebar...")
            from sidebar_manager import SidebarManager
            self.sidebar_manager = SidebarManager(
                self.fund_manager,
                self.data_handler,
                menu_options=ALL_PAGES
            )
            progress.progress(90)

            # Step 6: Admin password
            status.info("🔐 Loading security settings...")
            try:
                self.admin_password = st.secrets["ADMIN_PASSWORD"]
            except Exception:
                self.admin_password = os.getenv("ADMIN_PASSWORD", "1997")
            progress.progress(100)

            # Save to session
            self.save_to_session()

            # Clear loading UI
            progress.empty()
            status.empty()
            st.success("✅ Ứng dụng đã sẵn sàng!")

        except Exception as e:
            st.error(f"❌ Khởi tạo ứng dụng thất bại: {str(e)}")
            with st.expander("🔍 Chi tiết lỗi", expanded=True):
                st.code(str(e))
            self.render_error_recovery()
            st.stop()
    
    def apply_optimizations(self, optimizations):
        """Apply available optimizations"""
        if optimizations['save_optimization']:
            self.fund_manager = optimizations['save_optimization'](self.fund_manager)
        
        if optimizations['database_optimization']:
            self.fund_manager = optimizations['database_optimization'](self.fund_manager)
        
        if optimizations['realtime_sync']:
            self.transaction_handler = optimizations['realtime_sync'](self.fund_manager)
    
    def save_to_session(self):
        """Save components to session state"""
        st.session_state.fund_manager = self.fund_manager
        st.session_state.data_handler = self.data_handler
        st.session_state.sidebar_manager = self.sidebar_manager
        st.session_state.pages = self.pages
        st.session_state.admin_password = self.admin_password
        st.session_state.last_init = time.time()
    
    def load_from_session(self):
        """Load components from session state"""
        self.fund_manager = st.session_state.fund_manager
        self.data_handler = st.session_state.data_handler
        self.sidebar_manager = st.session_state.sidebar_manager
        self.pages = st.session_state.pages
        self.admin_password = st.session_state.admin_password
    
    def render_error_recovery(self):
        """Render error recovery options"""
        st.subheader("🚨 Tùy chọn khôi phục")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Thử lại", key="retry_init"):
                self.clear_session_cache()
                st.rerun()
        
        with col2:
            if st.button("🧹 Xóa Cache", key="clear_cache"):
                self.clear_session_cache()
                clear_app_cache()
                st.success("✅ Đã xóa cache")
                st.rerun()
        
        with col3:
            if st.button("🏠 Trang chủ", key="go_home"):
                st.session_state.menu_selection = PAGE_REPORTS
                st.rerun()
    
    def clear_session_cache(self):
        """Clear session cache"""
        keys_to_clear = [
            'fund_manager', 'data_handler', 'sidebar_manager', 'pages',
            'admin_password', 'last_init'
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def render_login_form(self):
        """Render login form for edit pages"""
        st.markdown("""
            <div style='max-width: 400px; margin: 3rem auto; padding: 2rem;
                        background: white; border-radius: 15px; 
                        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                        border: 1px solid rgba(255,255,255,0.2);'>
                <h3 style='text-align: center; color: #2c3e50; margin-bottom: 2rem;
                           font-weight: 600;'>
                    🔐 Xác thực quyền chỉnh sửa
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            password = st.text_input(
                "Mật khẩu quản trị",
                type="password",
                placeholder="Nhập mật khẩu để tiếp tục...",
                help="Cần mật khẩu admin để truy cập tính năng chỉnh sửa",
                label_visibility="visible"
            )
            
            if st.button("🚀 Xác thực", use_container_width=True, type="primary"):
                if password == self.admin_password:
                    st.session_state.logged_in = True
                    st.success("✅ Xác thực thành công!")
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error("❌ Mật khẩu không chính xác.")
                    time.sleep(1)
    
    def render_main_content(self, page: str):
        """Render main content based on selected page"""
        # Check authentication for edit pages
        if page in EDIT_PAGES and not st.session_state.logged_in:
            self.render_login_form()
            return
        
        try:
            # Render appropriate page
            if page == PAGE_ADD_INVESTOR and self.pages.get('investor'):
                self.pages['investor'](self.fund_manager).render_add_form()
                
            elif page == PAGE_EDIT_INVESTOR and self.pages.get('investor'):
                self.pages['investor'](self.fund_manager).render_edit_page()
                
            elif page == PAGE_ADD_TRANSACTION and self.pages.get('transaction'):
                self.pages['transaction'](self.fund_manager).render_transaction_form()
                
            elif page == PAGE_ADD_NAV and self.pages.get('transaction'):
                self.pages['transaction'](self.fund_manager).render_nav_update()
                
            elif page == PAGE_FM_WITHDRAWAL and self.pages.get('transaction'):
                self.pages['transaction'](self.fund_manager).render_fund_manager_withdrawal()
                
            elif page == PAGE_MANAGE_TRANSACTIONS and self.pages.get('transaction'):
                self.pages['transaction'](self.fund_manager).render_transaction_management()
                
            elif page == PAGE_CALCULATE_FEES and self.pages.get('fee'):
                self.pages['fee'](self.fund_manager).render_enhanced_fee_calculation()
                
            elif page == PAGE_CALCULATE_INDIVIDUAL_FEE and self.pages.get('fee'):
                self.pages['fee'](self.fund_manager).render_individual_fee()
                
            elif page == PAGE_REPORTS and self.pages.get('report'):
                self.pages['report'](self.fund_manager).render_reports()
                
            else:
                st.warning(f"⚠️ Trang '{page}' đang được phát triển.")
                st.info("💡 Vui lòng chọn trang khác từ menu bên trái.")
                
        except Exception as e:
            st.error(f"❌ Lỗi khi tải trang '{page}': {str(e)}")
            
            # Error recovery options
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"🔄 Thử lại '{page}'", key="retry_page"):
                    st.rerun()
            with col2:
                if st.button("🧹 Xóa Cache", key="clear_page_cache"):
                    clear_app_cache()
                    st.rerun()
            with col3:
                if st.button("🏠 Về trang chủ", key="home_from_error"):
                    st.session_state.menu_selection = PAGE_REPORTS
                    st.rerun()
    
    def handle_data_save(self):
        """Handle data saving operations"""
        if not st.session_state.get('data_changed', False):
            return
        
        try:
            # Validate data before saving
            validation_results = self.fund_manager.validate_data_consistency()
            if not validation_results['valid']:
                st.error("❌ Dữ liệu không nhất quán. Không thể lưu.")
                with st.expander("🔍 Chi tiết lỗi", expanded=False):
                    for error in validation_results['errors']:
                        st.error(f"• {error}")
                return
            
            # Save data
            with st.spinner("💾 Đang lưu dữ liệu..."):
                save_success = self.fund_manager.save_data()
                
                if save_success:
                    st.session_state.data_changed = False
                    st.toast("✅ Đã lưu thành công!", icon="💾")
                    
                    # Refresh data after save
                    with st.spinner("🔄 Đang đồng bộ hóa..."):
                        clear_app_cache()
                        self.fund_manager.load_data()
                    
                    st.toast("🔗 Dữ liệu đã được đồng bộ hóa", icon="🔄")
                    st.rerun()
                else:
                    st.error("❌ Lưu dữ liệu thất bại!")
                    
        except Exception as e:
            st.error(f"❌ Lỗi khi lưu dữ liệu: {str(e)}")
    
    def run_startup_validation(self):
        """Run startup validation if needed"""
        if st.session_state.get('show_startup_validation', True):
            validation_results = self.fund_manager.validate_data_consistency()
            if not validation_results['valid']:
                st.error("⚠️ Phát hiện vấn đề với dữ liệu!")
                with st.expander("🔍 Chi tiết vấn đề", expanded=True):
                    for error in validation_results['errors']:
                        st.error(f"• {error}")
                st.warning("🔧 Hãy kiểm tra và khắc phục trước khi tiếp tục.")
            
            st.session_state.show_startup_validation = False
    
    def run(self):
        """Main application execution"""
        try:
            # Kiểm tra xem các component đã sẵn sàng chưa
            if not hasattr(self, 'sidebar_manager') or not hasattr(self, 'fund_manager'):
                st.error("❌ App chưa được khởi tạo đúng cách")
                self.render_error_recovery()
                return
            # Run startup validation if needed
            self.run_startup_validation()
            
            # Render sidebar and get selected page
            selected_page = self.sidebar_manager.render()
            
            # Render main content
            self.render_main_content(selected_page)
            
            # Handle data saving
            self.handle_data_save()
            
        except Exception as e:
            st.error("💥 Lỗi nghiêm trọng của ứng dụng!")
            
            with st.expander("🔍 Chi tiết lỗi", expanded=True):
                st.code(str(e))
            
            st.subheader("🚨 Tùy chọn khôi phục")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Khởi động lại ứng dụng"):
                    # Clear everything and restart
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
            
            with col2:
                if st.button("🧹 Xóa toàn bộ Cache"):
                    self.clear_session_cache()
                    clear_app_cache()
                    st.success("✅ Đã xóa cache")
                    time.sleep(1)
                    st.rerun()
            
            with col3:
                if st.button("🛠 Thông tin Debug"):
                    st.write("**Session State Keys:**", list(st.session_state.keys()))
                    st.write("**App Start Time:**", st.session_state.get('app_start_time', 'Unknown'))
                    if 'fund_manager' in st.session_state:
                        st.write("**Fund Manager Status:**", "Loaded")
                    if 'data_handler' in st.session_state:
                        st.write("**Data Handler Status:**", "Loaded")

# === APPLICATION ENTRY POINT ===
def main():
    """Application entry point"""
    try:
        app = FundManagementApp()
        app.run()
    except Exception as e:
        st.error("💥 Ứng dụng không thể khởi động!")
        st.code(str(e))
        
        st.subheader("🚨 Hành động khẩn cấp")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Thử khởi động lại"):
                st.rerun()
        
        with col2:
            if st.button("📞 Thông tin hỗ trợ"):
                st.info("🔧 Vui lòng liên hệ bộ phận kỹ thuật để được hỗ trợ.")

# === RUN APPLICATION ===
if __name__ == "__main__":
    main()