# sidebar_manager.py

import streamlit as st
from datetime import datetime
from pathlib import Path

# Sửa lại import để dùng hàm an toàn từ data_utils
from data_utils import format_currency_safe
from google_drive_manager import GoogleDriveManager

class SidebarManager:
    """Quản lý toàn bộ việc hiển thị và logic của sidebar."""

    def __init__(self, fund_manager, data_handler, menu_options: list):
        self.fund_manager = fund_manager
        self.data_handler = data_handler
        self.menu_options = menu_options  # **SỬA ĐỔI: Nhận menu_options từ constructor**

    def _render_header(self):
        """Render tiêu đề và logo."""
        st.sidebar.markdown(
            '<div class="sidebar-section">🦈 FUND MANAGEMENT</div>',
            unsafe_allow_html=True
        )

    def _render_nav_display(self):
        """
        Render thẻ hiển thị NAV và thông tin Fund Manager.
        """
        latest_nav = self.fund_manager.get_latest_total_nav()
        fund_manager = self.fund_manager.get_fund_manager()
        
        nav_display = format_currency_safe(latest_nav)
        fm_info_html = ""

        # 2. Chỉ tạo chuỗi HTML nếu có đủ thông tin
        if fund_manager:
            fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
            if fm_tranches and latest_nav > 0:
                fm_units = sum(t.units for t in fm_tranches)
                fm_value = fm_units * self.fund_manager.calculate_price_per_unit(latest_nav)
                fm_info_value = format_currency_safe(fm_value, compact=True)
                
                # Tạo chuỗi HTML trên MỘT DÒNG DUY NHẤT để tránh lỗi parsing
                fm_info_html = f'<div class="fm-info">FM: {fm_units:,.1f}u ({fm_info_value})</div>'

        # 3. Xây dựng chuỗi HTML cuối cùng
        # Biến fm_info_html giờ đây hoặc là rỗng, hoặc là một chuỗi HTML hoàn chỉnh
        # không có ký tự xuống dòng thừa.
        html_content = f"""
            <div class="nav-card">
                <div class="nav-title">TỔNG NAV</div>
                <div class="nav-value">{nav_display}</div>
                {fm_info_html}
            </div>
        """
        st.sidebar.markdown(html_content, unsafe_allow_html=True)
        # **KẾT THÚC SỬA LỖI**

    def _render_quick_stats(self):
        """Render lưới thống kê nhanh."""
        stats_data = [
            (len(self.fund_manager.get_regular_investors()), "NĐT", "#0066cc"),
            (len(self.fund_manager.tranches), "Giao dịch", "#28a745"),
            (len(self.fund_manager.fee_records), "Kỳ phí", "#ffc107")
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

    
        
    def _render_navigation(self):
        """
        Render menu điều hướng, sử dụng key để quản lý trạng thái một cách chính xác.
        """
        st.sidebar.markdown('<div class="sidebar-section">MENU</div>', unsafe_allow_html=True)

        # **SỬA LỖI CHÍNH BẮT ĐẦU TỪ ĐÂY**

        # 1. Đặt một giá trị mặc định cho key của radio button nếu nó chưa tồn tại
        if 'menu_selection' not in st.session_state:
            st.session_state.menu_selection = self.menu_options[0]

        # 2. Tạo radio button và gán cho nó một `key` duy nhất.
        # Streamlit sẽ tự động cập nhật st.session_state.menu_selection khi người dùng nhấp chuột.
        st.sidebar.radio(
            "Chức năng",
            self.menu_options,
            # Index được xác định bởi giá trị hiện tại của key trong session_state
            index=self.menu_options.index(st.session_state.menu_selection),
            key="menu_selection", # Đây là phần quan trọng nhất
            label_visibility="collapsed"
        )
        
        # 3. Trả về giá trị đã được đồng bộ hóa từ session_state.
        # Đây là "nguồn chân lý duy nhất" cho trang hiện tại.
        return st.session_state.menu_selection

    def _render_user_status(self):
        
        if st.session_state.get('logged_in', False):
            st.sidebar.success("👤 Chế độ Admin")
            if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()
        else:
            st.sidebar.warning("🔒 Chế độ chỉ xem")
        st.sidebar.markdown("---")
    


    def _render_action_buttons(self):
        
        """Render các nút thao tác nhanh."""
        st.sidebar.markdown('<div class="sidebar-section">Thao tác nhanh</div>', unsafe_allow_html=True)
        col1, col2 = st.sidebar.columns(2)
        if col1.button("📊 Export Excel", use_container_width=True, help="Xuất báo cáo tổng hợp ra file Excel"):
            self._handle_export()
        if col2.button("☁️ Test Drive", use_container_width=True, help="Kiểm tra kết nối tới Google Drive"):
            self._handle_drive_test()

    def _render_footer(self):
        """Render thông tin cuối sidebar."""
        st.sidebar.markdown('<div class="sidebar-section">Thông tin</div>', unsafe_allow_html=True)
        export_dir = Path("exports")
        if export_dir.exists():
            excel_files = list(export_dir.glob("*.xlsx"))
            if excel_files:
                latest_file = max(excel_files, key=lambda p: p.stat().st_mtime)
                st.sidebar.caption(f"Last export: {datetime.fromtimestamp(latest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")

        st.sidebar.caption("v2.1 - UI Fix")

    # **PHƯƠNG THỨC MỚI: Dùng để hiển thị thông tin debug ở cuối**
    def _render_debug_info(self):
        """Hiển thị thông tin kết nối và dữ liệu đã tải ở cuối sidebar."""
        st.sidebar.markdown('<div class="sidebar-section">Thông tin hệ thống</div>', unsafe_allow_html=True)

        if self.data_handler and self.data_handler.connected:
            st.sidebar.success("🟢 Supabase Connected")
            with st.sidebar.expander("📊 Database Info"):
                conn_info = self.data_handler.connection_info
                ver_info = self.data_handler.version_info
                st.write(f"**Host:** `{conn_info.get('host', 'N/A')}`")
                st.write(f"**Database:** `{ver_info.get('database_name', 'N/A')}`")
                st.write(f"**User:** `{ver_info.get('current_user', 'N/A')}`")
        else:
            st.sidebar.error("🔴 Supabase Disconnected")

        # Hiển thị thông tin "Loaded" ở đây
        st.sidebar.info(
            f"📊 Đã tải: {len(self.fund_manager.investors)} NĐT, "
            f"{len(self.fund_manager.tranches)} Giao dịch, "
            f"{len(self.fund_manager.fee_records)} Kỳ phí"
        )
    
    def render(self) -> str:
        """Render toàn bộ sidebar và trả về trang được chọn."""
        self._render_header()
        
        # **SỰ THAY ĐỔI CHÍNH NẰM Ở ĐÂY**
        self._render_nav_display()
        self._render_quick_stats()
        selected_page = self._render_navigation() # 1. MENU
        self._render_action_buttons()           # 2. THAO TÁC NHANH
        self._render_user_status()
        
        # **SỬA ĐỔI: Gọi hàm hiển thị debug ở cuối cùng**
        self._render_debug_info()
        self._render_footer() 
        return selected_page

    def _handle_export(self):
        """Xử lý sự kiện nhấn nút Export."""
        with st.spinner("Đang xuất file Excel..."):
            try:
                gdrive = GoogleDriveManager(self.fund_manager)
                success = gdrive.auto_export_and_upload(trigger="manual")
                if success:
                    st.balloons()
                    st.success("✅ Xuất và upload thành công!")
            except Exception as e:
                st.error(f"❌ Lỗi khi xuất file: {e}")

    def _handle_drive_test(self):
        """Xử lý sự kiện nhấn nút Test Drive."""
        with st.spinner("Đang kiểm tra kết nối Google Drive..."):
            try:
                gdrive = GoogleDriveManager(self.fund_manager)
                if gdrive.connected:
                    st.success("✅ Kết nối Google Drive thành công!")
                else:
                    st.error("❌ Không thể kết nối. Kiểm tra lại file credentials.")
            except Exception as e:
                st.error(f"❌ Lỗi kết nối: {e}")