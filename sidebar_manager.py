# sidebar_manager.py - Clean Optimized Sidebar Manager

import streamlit as st
from datetime import datetime
from pathlib import Path
import time

class SidebarManager:
    """Professional sidebar manager with clean architecture"""

    def __init__(self, fund_manager, data_handler, menu_options: list):
        self.fund_manager = fund_manager
        self.data_handler = data_handler
        self.menu_options = menu_options
        self._cache = {}

    def _get_nav_data(_self):
        """Get NAV data with caching"""
        try:
            latest_nav = _self.fund_manager.get_latest_total_nav()
            fund_manager = _self.fund_manager.get_fund_manager()
            
            fm_info = None
            if fund_manager and latest_nav and latest_nav > 0:
                fm_tranches = _self.fund_manager.get_investor_tranches(fund_manager.id)
                if fm_tranches:
                    fm_units = sum(t.units for t in fm_tranches)
                    fm_value = fm_units * _self.fund_manager.calculate_price_per_unit(latest_nav)
                    fm_info = {'units': fm_units, 'value': fm_value}
            
            return {'nav': latest_nav, 'fm_info': fm_info}
        except Exception:
            return {'nav': None, 'fm_info': None}

    @st.cache_data(ttl=60)
    def _get_stats_data(_self):
        """Get statistics data with caching"""
        try:
            regular_investors = _self.fund_manager.get_regular_investors()
            active_tranches = [t for t in _self.fund_manager.tranches if t.units > 0]
            fee_records_count = len(_self.fund_manager.fee_records)
            
            return {
                'investors': len(regular_investors),
                'tranches': len(active_tranches),
                'fees': fee_records_count
            }
        except Exception:
            return {'investors': 0, 'tranches': 0, 'fees': 0}

    def _format_currency(self, value, compact=False):
        """Format currency with error handling"""
        try:
            # Lazy import to avoid circular dependencies
            from data_utils import format_currency_safe
            return format_currency_safe(value, compact=compact)
        except ImportError:
            # Fallback formatting
            if value is None:
                return "N/A"
            if compact and value >= 1_000_000_000:
                return f"{value/1_000_000_000:.1f}B"
            elif compact and value >= 1_000_000:
                return f"{value/1_000_000:.1f}M"
            elif compact and value >= 1_000:
                return f"{value/1_000:.1f}K"
            else:
                return f"{value:,.0f}"

    def render_header(self):
        """Render tiêu đề với responsive design"""
        st.sidebar.markdown(
            '<div class="sidebar-section">🦈 FUND MANAGEMENT</div>',
            unsafe_allow_html=True
        )

    def render_nav_card(self):
        """Render card NAV với thông tin Fund Manager - học hỏi layout từ code gốc"""
        nav_data = self._get_nav_data()
        nav_value = nav_data['nav']
        fm_info = nav_data['fm_info']
        
        nav_display = self._format_currency(nav_value) if nav_value else "Đang tải..."
        fm_info_html = ""

        # Thông tin Fund Manager (nếu có) - theo style code gốc
        if fm_info:
            fm_value_display = self._format_currency(fm_info['value'], compact=True)
            fm_value_display = fm_value_display.replace("đ", "")
            # Tạo chuỗi HTML trên MỘT DÒNG DUY NHẤT để tránh lỗi parsing
            fm_info_html = f'<div class="fm-info">FM: {fm_info["units"]:,.1f} units ({fm_value_display})</div>'

        # Card NAV với design responsive - học hỏi structure từ code gốc
        html_content = f"""
            <div class="nav-card">
                <div class="nav-title">TỔNG NAV</div>
                <div class="nav-value">{nav_display}</div>
                {fm_info_html}
            </div>
        """
        st.sidebar.markdown(html_content, unsafe_allow_html=True)

    def render_stats_grid(self):
        """Render lưới thống kê nhanh - học hỏi content từ code gốc"""
        stats = self._get_stats_data()
        
        # Stats data theo style code gốc - NĐT, Giao dịch, Kỳ phí
        stats_data = [
            (stats['investors'], "NĐT", "#0066cc"),
            (len(self.fund_manager.tranches), "Giao dịch", "#28a745"),
            (stats['fees'], "Kỳ phí", "#ffc107")
        ]
        
        stats_items = ""
        for value, label, color in stats_data:
            stats_items += f"""
            <div class="stat-item">
                <div class="stat-value" style="color: {color};">{value}</div>
                <div class="stat-label">{label}</div>
            </div>"""

        html_content = f'<div class="stats-grid">{stats_items}</div>'
        st.sidebar.markdown(html_content, unsafe_allow_html=True)

    def render_navigation_menu(self):
        """Render menu điều hướng - theo style code gốc"""
        st.sidebar.markdown('<div class="sidebar-section">MENU</div>', unsafe_allow_html=True)

        # Đặt giá trị mặc định cho key của radio button nếu chưa tồn tại
        if 'menu_selection' not in st.session_state:
            st.session_state.menu_selection = self.menu_options[0]

        # Tạo radio button và gán cho nó một key duy nhất
        # Streamlit sẽ tự động cập nhật st.session_state.menu_selection khi người dùng nhấp chuột
        current_selection = st.sidebar.radio(
            "Chức năng",
            self.menu_options,
            # Index được xác định bởi giá trị hiện tại của key trong session_state
            index=self.menu_options.index(st.session_state.menu_selection),
            key="menu_selection", # Đây là phần quan trọng nhất
            label_visibility="collapsed"
        )
        
        # Trả về giá trị đã được đồng bộ hóa từ session_state
        # Đây là "nguồn chân lý duy nhất" cho trang hiện tại
        return current_selection

    def render_user_status(self):
        """Render trạng thái người dùng - theo style code gốc"""
        if st.session_state.get('logged_in', False):
            st.sidebar.success("👤 Chế độ Admin")
            if st.sidebar.button("🚪 Đăng xuất", width="stretch"):
                st.session_state.logged_in = False
                st.rerun()
        else:
            st.sidebar.warning("🔒 Chế độ chỉ xem")

    def render_action_buttons(self):
        """Render các nút thao tác nhanh - theo style code gốc"""
        st.sidebar.markdown('<div class="sidebar-section">Thao tác nhanh</div>', unsafe_allow_html=True)
        
        col1, col2 = st.sidebar.columns(2)
        
        if col1.button("📊 Export Excel", width="stretch", 
                      help="Xuất báo cáo tổng hợp ra file Excel"):
            self.handle_excel_export()
        
        if col2.button("☁️ Test Drive", width="stretch", 
                      help="Kiểm tra kết nối tới Google Drive"):
            self.handle_drive_test()

    def render_connection_status(self):
        """Render thông tin debug - theo style code gốc"""
        st.sidebar.markdown('<div class="sidebar-section">Thông tin hệ thống</div>', unsafe_allow_html=True)

        if self.data_handler and hasattr(self.data_handler, 'connected') and self.data_handler.connected:
            st.sidebar.success("🟢 Supabase Connected")
        else:
            st.sidebar.error("🔴 Supabase Disconnected")

        

    def render_footer(self):
        """Render thông tin cuối sidebar - theo style code gốc"""
        st.sidebar.markdown('<div class="sidebar-section">Thông tin</div>', unsafe_allow_html=True)
        
        # Last export info - theo code gốc
        export_dir = Path("exports")
        if export_dir.exists():
            excel_files = list(export_dir.glob("*.xlsx"))
            if excel_files:
                latest_file = max(excel_files, key=lambda p: p.stat().st_mtime)
                st.sidebar.caption(f"Last export: {datetime.fromtimestamp(latest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")

        # Version info - theo code gốc
        st.sidebar.caption("v3.1 - Clean Architecture")

    def show_last_export_info(self):
        """Show information about last export"""
        try:
            export_dir = Path("exports")
            if export_dir.exists():
                excel_files = list(export_dir.glob("*.xlsx"))
                if excel_files:
                    latest_file = max(excel_files, key=lambda p: p.stat().st_mtime)
                    export_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
                    st.sidebar.caption(f"📊 Export cuối: {export_time.strftime('%d/%m %H:%M')}")
        except Exception:
            pass  # Silently ignore if can't get export info

    def handle_excel_export(self):
        """Handle Excel export operation"""
        try:
            # Lazy import to avoid circular dependencies
            from google_drive_manager import GoogleDriveManager
            
            with st.spinner("📊 Đang xuất Excel..."):
                gdrive = GoogleDriveManager(self.fund_manager)
                success = gdrive.auto_export_and_upload(trigger="manual")
                
                if success:
                    st.balloons()
                    st.success("✅ Xuất Excel thành công!")
                    st.toast("📊 File đã được tải lên Google Drive", icon="☁️")
                else:
                    st.warning("⚠️ Xuất Excel thành công nhưng tải lên Drive thất bại")
                    
        except ImportError:
            st.error("❌ Chức năng Google Drive không khả dụng")
        except Exception as e:
            st.error(f"❌ Lỗi xuất Excel: {str(e)}")

    def handle_drive_test(self):
        """Handle Google Drive connection test"""
        try:
            from google_drive_manager import GoogleDriveManager
            
            with st.spinner("☁️ Kiểm tra Google Drive..."):
                gdrive = GoogleDriveManager(self.fund_manager)
                
                if gdrive.connected:
                    st.success("✅ Google Drive kết nối thành công!")
                    st.toast("☁️ Drive connection OK", icon="✅")
                else:
                    st.error("❌ Không thể kết nối Google Drive")
                    st.info("💡 Kiểm tra file credentials.json")
                    
        except ImportError:
            st.error("❌ Google Drive Manager không khả dụng")
        except Exception as e:
            st.error(f"❌ Lỗi kết nối Drive: {str(e)}")

    def handle_data_refresh(self):
        """Handle data refresh operation"""
        try:
            with st.spinner("🔄 Đang làm mới dữ liệu..."):
                # Clear Streamlit caches
                if hasattr(st, 'cache_data'):
                    st.cache_data.clear()
                if hasattr(st, 'cache_resource'):
                    st.cache_resource.clear()
                
                # Clear method caches
                if hasattr(self._get_nav_data, 'clear'):
                    self._get_nav_data.clear()
                if hasattr(self._get_stats_data, 'clear'):
                    self._get_stats_data.clear()
                
                # Clear session state caches
                cache_keys_to_clear = [
                    key for key in st.session_state.keys() 
                    if any(word in key.lower() for word in ['cache', 'nav', 'balance'])
                ]
                for key in cache_keys_to_clear:
                    del st.session_state[key]
                
                # Reload fund manager data
                self.fund_manager.load_data()
                
                st.success("✅ Dữ liệu đã được làm mới!")
                st.toast("🔄 Data refreshed successfully", icon="✅")
                
                # Small delay then rerun
                time.sleep(0.5)
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Lỗi làm mới dữ liệu: {str(e)}")


    
    def render(self) -> str:
        """Render toàn bộ sidebar và trả về trang được chọn - theo flow code gốc"""
        # Nút này giờ là một phần của sidebar, sẽ ẩn/hiện cùng với sidebar
        
        
        self.render_header()
        
        # Thứ tự render theo code gốc
        self.render_nav_card()           # NAV display
        self.render_stats_grid()         # Quick stats 
        selected_page = self.render_navigation_menu()  # MENU
        self.render_action_buttons()     # Thao tác nhanh
        self.render_user_status()        # User status
        
        # Debug info và footer - theo code gốc
        self.render_connection_status()  # Thông tin hệ thống (debug info)
        # self.render_footer()             # Thông tin
        
        return selected_page

    def render_mobile_header(self):
        """Optional mobile header for main content area"""
        # Check if we're in mobile viewport (this is approximate)
        st.markdown("""
            <script>
            if (window.innerWidth <= 768) {
                document.body.classList.add('mobile-viewport');
            }
            </script>
            
            <div class="mobile-header" style="
                display: none;
                position: sticky;
                top: 0;
                background: white;
                border-bottom: 1px solid #e9ecef;
                padding: 1rem;
                text-align: center;
                font-weight: 600;
                color: #2c3e50;
                z-index: 100;
            ">
                🦈 FUND MANAGEMENT
            </div>
            
            <style>
            @media (max-width: 768px) {
                .mobile-header {
                    display: block !important;
                }
            }
            </style>
        """, unsafe_allow_html=True)